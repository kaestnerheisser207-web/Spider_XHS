import threading
import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger

from apis.xhs_pc_login_apis import PcLoginUpstreamError
from xhs_service import app as app_module
from xhs_service import pc as pc_module
from xhs_service.pc import create_pc_router
from xhs_service.state import PcSessionStore, StateNotFound


class RecordingPcAPI:
    def __init__(self):
        self.calls = []

    def __getattr__(self, method_name):
        def call(*args, **kwargs):
            self.calls.append((method_name, args, kwargs))
            return True, '成功', {'method': method_name}

        return call


class FakePcStore:
    login_ttl_seconds = 600
    session_ttl_seconds = 86400

    def __init__(self):
        self.api = RecordingPcAPI()
        self.entry = SimpleNamespace(api=self.api, lock=threading.Lock())
        self.auth = None
        self.closed_session = None

    def add_session(self, auth):
        self.auth = auth
        return 'pc_session_test'

    def get_session(self, session_id):
        if session_id != 'pc_session_test':
            raise StateNotFound(session_id)
        return self.entry

    def discard_session(self, session_id):
        if session_id != 'pc_session_test':
            return False
        self.closed_session = session_id
        return True


class FakePcLoginStore(FakePcStore):
    def __init__(self):
        super().__init__()
        self.login_entry = None
        self.completed_login = None
        self.discarded_login = None

    def add_login(
        self,
        client,
        mode,
        cookies,
        *,
        qr_id='',
        qr_code='',
        phone='',
        zone='86',
    ):
        self.login_entry = SimpleNamespace(
            client=client,
            mode=mode,
            cookies=cookies,
            qr_id=qr_id,
            qr_code=qr_code,
            phone=phone,
            zone=zone,
            lock=threading.Lock(),
        )
        return 'pc_login_test'

    def get_login(self, login_id, mode):
        if (
            login_id != 'pc_login_test'
            or self.login_entry is None
            or self.login_entry.mode != mode
        ):
            raise StateNotFound(login_id)
        return self.login_entry

    def complete_login(self, login_id, cookies, source, account):
        self.completed_login = (login_id, cookies, source, account)
        return 'pc_session_test'

    def discard_login(self, login_id):
        self.discarded_login = login_id


def no_service_auth():
    return None


class PcHTTPServiceTest(unittest.TestCase):
    def setUp(self):
        self.store = FakePcStore()
        app = FastAPI()
        app.include_router(create_pc_router(self.store, no_service_auth))
        self.client = TestClient(app)

    def test_main_openapi_exposes_every_pc_http_route(self):
        paths = app_module.app.openapi()['paths']
        expected = {
            '/v1/pc/sessions/cookie',
            '/v1/pc/logins/qr',
            '/v1/pc/logins/qr/{login_id}',
            '/v1/pc/logins/phone',
            '/v1/pc/logins/phone/{login_id}/verify',
            '/v1/pc/sessions/{session_id}',
            '/v1/pc/account',
            '/v1/pc/search/keywords',
            '/v1/pc/search/notes/page',
            '/v1/pc/search/notes/all',
            '/v1/pc/search/users/page',
            '/v1/pc/search/users/all',
            '/v1/pc/notes/detail',
            '/v1/pc/notes/comments/outer/page',
            '/v1/pc/notes/comments/outer/all',
            '/v1/pc/notes/comments/inner/page',
            '/v1/pc/notes/comments/inner/all',
            '/v1/pc/notes/comments/all',
            '/v1/pc/users/profile',
            '/v1/pc/users/posts/page',
            '/v1/pc/users/posts/all',
            '/v1/pc/users/likes/page',
            '/v1/pc/users/likes/all',
            '/v1/pc/users/collects/page',
            '/v1/pc/users/collects/all',
            '/v1/pc/feed/channels',
            '/v1/pc/feed/page',
            '/v1/pc/feed/all',
            '/v1/pc/notifications/unread',
            '/v1/pc/notifications/mentions/page',
            '/v1/pc/notifications/mentions/all',
            '/v1/pc/notifications/reactions/page',
            '/v1/pc/notifications/reactions/all',
            '/v1/pc/notifications/follows/page',
            '/v1/pc/notifications/follows/all',
            '/v1/pc/media/video/resolve',
            '/v1/pc/media/image/resolve',
        }
        actual = {path for path in paths if path.startswith('/v1/pc/')}
        self.assertEqual(actual, expected)

    def test_pc_routes_are_guarded_by_the_service_key(self):
        response = TestClient(app_module.app).post(
            '/v1/pc/account',
            json={'session_id': 'pc_session_test'},
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['detail']['code'], 'service_not_configured')

    def test_cookie_session_validates_account_and_binds_user_id(self):
        auth = SimpleNamespace(set_user_id=Mock(), close=Mock())
        api = SimpleNamespace(
            get_user_me=Mock(
                return_value=(
                    True,
                    '成功',
                    {'data': {'user_id': 'user_1', 'nickname': '测试账号'}},
                )
            )
        )
        proxies = {'https': 'http://proxy.test:8080'}

        with (
            patch.object(
                pc_module.XHSPcAuth,
                'from_cookie',
                return_value=auth,
            ) as auth_factory,
            patch.object(pc_module, 'XHS_Apis', return_value=api),
        ):
            response = self.client.post(
                '/v1/pc/sessions/cookie',
                json={
                    'cookies': 'a1=a1_value; web_session=session_value',
                    'proxies': proxies,
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['session_id'], 'pc_session_test')
        auth_factory.assert_called_once_with(
            'a1=a1_value; web_session=session_value',
            proxies=proxies,
        )
        api.get_user_me.assert_called_once_with(proxies=proxies)
        auth.set_user_id.assert_called_once_with('user_1')
        self.assertIs(self.store.auth, auth)
        auth.close.assert_not_called()

    def test_qr_login_can_be_started_and_completed_across_requests(self):
        store = FakePcLoginStore()
        app = FastAPI()
        app.include_router(create_pc_router(store, no_service_auth))
        client = TestClient(app)
        cookies = {'a1': 'a1_value', 'web_session': 'visitor_session'}
        authenticated_cookies = {
            'a1': 'a1_value',
            'web_session': 'authenticated_session',
        }
        login = SimpleNamespace(
            generate_init_cookies=Mock(return_value=cookies),
            generate_qrcode=Mock(
                return_value=(
                    True,
                    '成功',
                    {
                        'cookies': cookies,
                        'qr_id': 'qr_1',
                        'code': 'code_1',
                        'qr_url': 'xhsdiscover://qr',
                    },
                )
            ),
            check_qrcode_status=Mock(
                side_effect=[
                    (False, '请扫描二维码', cookies),
                    (True, '验证成功', authenticated_cookies),
                ]
            ),
            ensure_webprofile=Mock(return_value='gid_1'),
            get_user_info=Mock(
                return_value=(
                    True,
                    {'guest': False, 'user_id': 'user_1'},
                    authenticated_cookies,
                )
            ),
            close=Mock(),
        )

        with patch.object(pc_module, 'XHSLoginApi', return_value=login):
            start_response = client.post('/v1/pc/logins/qr', json={})
            poll_response = client.get('/v1/pc/logins/qr/pc_login_test')

        self.assertEqual(start_response.status_code, 200, start_response.text)
        self.assertEqual(start_response.json()['status'], 'waiting_scan')
        self.assertEqual(poll_response.status_code, 200, poll_response.text)
        self.assertEqual(poll_response.json()['status'], 'authenticated')
        self.assertEqual(
            store.completed_login,
            (
                'pc_login_test',
                authenticated_cookies,
                'qrcode',
                {'guest': False, 'user_id': 'user_1'},
            ),
        )
        login.ensure_webprofile.assert_called_once_with(cookies)
        login.close.assert_not_called()

    def test_qr_finalize_failure_returns_and_logs_only_safe_diagnostics(self):
        store = FakePcLoginStore()
        cookies = {
            'a1': 'secret-a1',
            'web_session': 'secret-session',
        }
        login = SimpleNamespace(
            generate_init_cookies=Mock(return_value=cookies),
            generate_qrcode=Mock(
                return_value=(
                    True,
                    '成功',
                    {
                        'cookies': cookies,
                        'qr_id': 'secret-qr-id',
                        'code': 'secret-qr-code',
                        'qr_url': 'xhsdiscover://qr',
                    },
                )
            ),
            check_qrcode_status=Mock(
                side_effect=[
                    (False, '请扫描二维码', cookies),
                    PcLoginUpstreamError(
                        'pc_qr_finalize_rejected',
                        '登录异常',
                        {
                            'phase': 'qr_finalize',
                            'http_status': 200,
                            'upstream_success': False,
                            'upstream_code': -1,
                            'code_status': 2,
                            'login_session_present': False,
                        },
                    ),
                ]
            ),
            ensure_webprofile=Mock(return_value='gid_1'),
            close=Mock(),
        )
        app = FastAPI()
        app.include_router(create_pc_router(store, no_service_auth))
        client = TestClient(app)
        output = StringIO()
        sink = logger.add(output, format='{message} {extra}')

        try:
            with patch.object(pc_module, 'XHSLoginApi', return_value=login):
                self.assertEqual(
                    client.post('/v1/pc/logins/qr', json={}).status_code,
                    200,
                )
                response = client.get('/v1/pc/logins/qr/pc_login_test')
        finally:
            logger.remove(sink)

        self.assertEqual(response.status_code, 502, response.text)
        self.assertEqual(
            response.json()['detail'],
            {
                'code': 'pc_qr_finalize_rejected',
                'message': '登录异常',
                'diagnostics': {
                    'phase': 'qr_finalize',
                    'http_status': 200,
                    'upstream_success': False,
                    'upstream_code': -1,
                    'code_status': 2,
                    'login_session_present': False,
                },
            },
        )
        logged = output.getvalue()
        self.assertIn('PC login upstream request failed', logged)
        self.assertIn("'error_code': 'pc_qr_finalize_rejected'", logged)
        self.assertNotIn('secret-a1', logged)
        self.assertNotIn('secret-session', logged)
        self.assertNotIn('secret-qr-id', logged)
        self.assertNotIn('secret-qr-code', logged)

    def test_phone_login_can_be_started_and_verified_across_requests(self):
        store = FakePcLoginStore()
        app = FastAPI()
        app.include_router(create_pc_router(store, no_service_auth))
        client = TestClient(app)
        cookies = {'a1': 'a1_value', 'web_session': 'visitor_session'}
        authenticated_cookies = {
            'a1': 'a1_value',
            'web_session': 'authenticated_session',
        }
        login = SimpleNamespace(
            generate_init_cookies=Mock(return_value=cookies),
            ensure_webprofile=Mock(return_value='gid_1'),
            send_phone_code=Mock(return_value=(True, '成功', {})),
            login_by_phone=Mock(
                return_value=(
                    True,
                    '成功',
                    {'cookies': authenticated_cookies},
                )
            ),
            get_user_info=Mock(
                return_value=(
                    True,
                    {'guest': False, 'user_id': 'user_1'},
                    authenticated_cookies,
                )
            ),
            close=Mock(),
        )

        with patch.object(pc_module, 'XHSLoginApi', return_value=login):
            start_response = client.post(
                '/v1/pc/logins/phone',
                json={'phone': '13800000000', 'zone': '86'},
            )
            verify_response = client.post(
                '/v1/pc/logins/phone/pc_login_test/verify',
                json={'code': '123456'},
            )

        self.assertEqual(start_response.status_code, 200, start_response.text)
        self.assertEqual(start_response.json()['status'], 'waiting_code')
        self.assertEqual(verify_response.status_code, 200, verify_response.text)
        self.assertEqual(verify_response.json()['status'], 'authenticated')
        login.send_phone_code.assert_called_once_with(
            '13800000000',
            cookies,
            '86',
        )
        login.login_by_phone.assert_called_once_with(
            '13800000000',
            '123456',
            cookies,
            '86',
        )
        self.assertEqual(store.completed_login[2], 'phone')
        login.close.assert_not_called()

    def test_every_authenticated_pc_capability_forwards_exact_arguments(self):
        proxies = {'https': 'http://proxy.test:8080'}
        base = {'session_id': 'pc_session_test', 'proxies': proxies}
        comment = {
            'note_id': 'note_1',
            'id': 'comment_1',
            'sub_comment_has_more': True,
            'sub_comment_cursor': 'inner_start',
            'sub_comments': [],
        }
        requests = [
            ('/v1/pc/account', base, 'get_user_me', ()),
            (
                '/v1/pc/search/keywords',
                {**base, 'keyword': '旅行'},
                'get_search_keyword',
                ('旅行',),
            ),
            (
                '/v1/pc/search/notes/page',
                {
                    **base,
                    'query': '露营',
                    'page': 2,
                    'sort_type': 1,
                    'note_type': 2,
                    'note_time': 3,
                    'note_range': 4,
                    'position_distance': 5,
                    'geo': '31,121',
                    'search_id': 'search_1',
                },
                'search_note',
                ('露营', 2, 1, 2, 3, 4, 5, '31,121', 'search_1'),
            ),
            (
                '/v1/pc/search/notes/all',
                {**base, 'query': '露营', 'limit': 12},
                'search_some_note',
                ('露营', 12, 0, 0, 0, 0, 0, ''),
            ),
            (
                '/v1/pc/search/users/page',
                {**base, 'query': '作者', 'page': 3},
                'search_user',
                ('作者', 3),
            ),
            (
                '/v1/pc/search/users/all',
                {**base, 'query': '作者', 'limit': 11},
                'search_some_user',
                ('作者', 11),
            ),
            (
                '/v1/pc/notes/detail',
                {**base, 'url': 'https://www.xiaohongshu.com/explore/note_1'},
                'get_note_info',
                ('https://www.xiaohongshu.com/explore/note_1',),
            ),
            (
                '/v1/pc/notes/comments/outer/page',
                {
                    **base,
                    'note_id': 'note_1',
                    'cursor': 'outer_1',
                    'xsec_token': 'token_1',
                },
                'get_note_out_comment',
                ('note_1', 'outer_1', 'token_1'),
            ),
            (
                '/v1/pc/notes/comments/outer/all',
                {**base, 'note_id': 'note_1', 'xsec_token': 'token_1'},
                'get_note_all_out_comment',
                ('note_1', 'token_1'),
            ),
            (
                '/v1/pc/notes/comments/inner/page',
                {
                    **base,
                    'comment': comment,
                    'cursor': 'inner_1',
                    'xsec_token': 'token_1',
                },
                'get_note_inner_comment',
                (comment, 'inner_1', 'token_1'),
            ),
            (
                '/v1/pc/notes/comments/inner/all',
                {**base, 'comment': comment, 'xsec_token': 'token_1'},
                'get_note_all_inner_comment',
                (comment, 'token_1'),
            ),
            (
                '/v1/pc/notes/comments/all',
                {**base, 'url': 'https://www.xiaohongshu.com/explore/note_1'},
                'get_note_all_comment',
                ('https://www.xiaohongshu.com/explore/note_1',),
            ),
            (
                '/v1/pc/users/profile',
                {**base, 'user_id': 'user_1'},
                'get_user_info',
                ('user_1',),
            ),
            (
                '/v1/pc/users/posts/page',
                {
                    **base,
                    'user_id': 'user_1',
                    'cursor': 'cursor_1',
                    'xsec_token': 'token_1',
                    'xsec_source': 'pc_search',
                },
                'get_user_note_info',
                ('user_1', 'cursor_1', 'token_1', 'pc_search'),
            ),
            (
                '/v1/pc/users/posts/all',
                {**base, 'user_url': 'https://www.xiaohongshu.com/user/u1'},
                'get_user_all_notes',
                ('https://www.xiaohongshu.com/user/u1',),
            ),
            (
                '/v1/pc/users/likes/page',
                {**base, 'user_id': 'user_1', 'cursor': 'cursor_1'},
                'get_user_like_note_info',
                ('user_1', 'cursor_1', '', ''),
            ),
            (
                '/v1/pc/users/likes/all',
                {**base, 'user_url': 'https://www.xiaohongshu.com/user/u1'},
                'get_user_all_like_note_info',
                ('https://www.xiaohongshu.com/user/u1',),
            ),
            (
                '/v1/pc/users/collects/page',
                {**base, 'user_id': 'user_1', 'cursor': 'cursor_1'},
                'get_user_collect_note_info',
                ('user_1', 'cursor_1', '', ''),
            ),
            (
                '/v1/pc/users/collects/all',
                {**base, 'user_url': 'https://www.xiaohongshu.com/user/u1'},
                'get_user_all_collect_note_info',
                ('https://www.xiaohongshu.com/user/u1',),
            ),
            (
                '/v1/pc/feed/channels',
                base,
                'get_homefeed_all_channel',
                (),
            ),
            (
                '/v1/pc/feed/page',
                {
                    **base,
                    'category': 'homefeed.fashion_v3',
                    'cursor_score': 'cursor_score_1',
                    'refresh_type': 3,
                    'note_index': 20,
                    'num': 30,
                    'need_num': 15,
                },
                'get_homefeed_recommend',
                ('homefeed.fashion_v3', 'cursor_score_1', 3, 20),
            ),
            (
                '/v1/pc/feed/all',
                {**base, 'category': 'homefeed.fashion_v3', 'limit': 13},
                'get_homefeed_recommend_by_num',
                ('homefeed.fashion_v3', 13),
            ),
            (
                '/v1/pc/notifications/unread',
                base,
                'get_unread_message',
                (),
            ),
            (
                '/v1/pc/notifications/mentions/page',
                {**base, 'cursor': 'cursor_1'},
                'get_metions',
                ('cursor_1',),
            ),
            (
                '/v1/pc/notifications/mentions/all',
                base,
                'get_all_metions',
                (),
            ),
            (
                '/v1/pc/notifications/reactions/page',
                {**base, 'cursor': 'cursor_1'},
                'get_likesAndcollects',
                ('cursor_1',),
            ),
            (
                '/v1/pc/notifications/reactions/all',
                base,
                'get_all_likesAndcollects',
                (),
            ),
            (
                '/v1/pc/notifications/follows/page',
                {**base, 'cursor': 'cursor_1'},
                'get_new_connections',
                ('cursor_1',),
            ),
            (
                '/v1/pc/notifications/follows/all',
                base,
                'get_all_new_connections',
                (),
            ),
        ]

        for path, payload, method, args in requests:
            with self.subTest(path=path):
                response = self.client.post(path, json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json()['result']['method'], method)
                actual_method, actual_args, kwargs = self.store.api.calls[-1]
                self.assertEqual(actual_method, method)
                self.assertEqual(actual_args, args)
                self.assertEqual(kwargs['proxies'], proxies)
                if method == 'get_homefeed_recommend':
                    self.assertEqual(kwargs['num'], 30)
                    self.assertEqual(kwargs['need_num'], 15)
                else:
                    self.assertEqual(set(kwargs), {'proxies'})

    def test_static_media_resolvers_do_not_require_an_account_session(self):
        with (
            patch.object(
                pc_module.XHS_Apis,
                'get_note_no_water_video',
                return_value=(True, '成功', 'https://video.test/file'),
            ) as video,
            patch.object(
                pc_module.XHS_Apis,
                'get_note_no_water_img',
                return_value=(True, '成功', 'https://image.test/file'),
            ) as image,
        ):
            video_response = self.client.post(
                '/v1/pc/media/video/resolve',
                json={'note_id': 'note_1'},
            )
            image_response = self.client.post(
                '/v1/pc/media/image/resolve',
                json={'image_url': 'https://sns-img.test/image!format/webp'},
            )

        self.assertEqual(video_response.status_code, 200, video_response.text)
        self.assertEqual(image_response.status_code, 200, image_response.text)
        video.assert_called_once_with('note_1')
        image.assert_called_once_with('https://sns-img.test/image!format/webp')

    def test_session_inspection_and_close_are_pc_scoped(self):
        inspect_response = self.client.get('/v1/pc/sessions/pc_session_test')
        close_response = self.client.delete('/v1/pc/sessions/pc_session_test')
        missing_response = self.client.get('/v1/pc/sessions/missing')

        self.assertEqual(inspect_response.status_code, 200)
        self.assertEqual(close_response.json(), {'status': 'closed'})
        self.assertEqual(self.store.closed_session, 'pc_session_test')
        self.assertEqual(missing_response.status_code, 404)
        self.assertEqual(
            missing_response.json()['detail']['code'],
            'pc_session_not_found',
        )


class PcSessionStoreTest(unittest.TestCase):
    def test_completed_login_transfers_transport_into_pc_session(self):
        store = PcSessionStore(login_ttl_seconds=60, session_ttl_seconds=120)
        login = SimpleNamespace(close=Mock())
        auth = SimpleNamespace(set_user_id=Mock(), close=Mock())
        api = object()
        login_id = store.add_login(
            login,
            'phone',
            {'a1': 'a1_value', 'web_session': 'session_value'},
        )

        with (
            patch(
                'xhs_service.state.XHSPcAuth.from_completed_login',
                return_value=auth,
            ) as factory,
            patch('xhs_service.state.XHS_Apis', return_value=api),
        ):
            session_id = store.complete_login(
                login_id,
                {'a1': 'a1_value', 'web_session': 'session_value'},
                'phone',
                {'user_id': 'user_1'},
            )

        entry = store.get_session(session_id)
        self.assertIs(entry.auth, auth)
        self.assertIs(entry.api, api)
        factory.assert_called_once_with(
            login,
            'a1=a1_value; web_session=session_value',
            login_source='phone',
        )
        auth.set_user_id.assert_called_once_with('user_1')
        login.close.assert_not_called()
        store.close()
        auth.close.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
