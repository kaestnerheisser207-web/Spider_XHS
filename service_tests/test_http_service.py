import base64
import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from xhs_service import app as app_module


class FakeStore:
    login_ttl_seconds = 600
    session_ttl_seconds = 86400

    def __init__(self):
        self.api = SimpleNamespace(post_note=self.post_note)
        self.entry = SimpleNamespace(
            api=self.api,
            lock=__import__('threading').Lock(),
        )
        self.published = None

    def post_note(self, note, proxies=None):
        self.published = (note, proxies)
        return True, '成功', {'success': True, 'note_id': 'note_1'}

    def get_session(self, session_id):
        if session_id != 'session_test':
            raise app_module.StateNotFound(session_id)
        return self.entry

    def close(self):
        return None


class CapabilityStore:
    session_ttl_seconds = 86400

    def __init__(self):
        self.api = SimpleNamespace(
            get_user_info=Mock(return_value=(True, '成功', {'account': 'creator'})),
            get_topic=Mock(return_value=(True, '成功', {'topics': []})),
            get_location_info=Mock(return_value=(True, '成功', {'locations': []})),
            get_file_ids=Mock(
                return_value=(True, '成功', ({'permits': []}, '1700000000'))
            ),
            upload_media=Mock(
                return_value=(True, '上传成功', {'fileIds': 'file_1'})
            ),
            query_transcode=Mock(return_value=(True, '成功', {'status': 2})),
            encryption=Mock(return_value=(True, '成功', {'url': 'encrypted'})),
            get_posted_notes_page=Mock(
                return_value=(True, '成功', {'data': {'notes': [], 'page': -1}})
            ),
            get_all_posted_notes=Mock(return_value=(True, '成功', [])),
        )
        self.entry = SimpleNamespace(
            api=self.api,
            lock=__import__('threading').Lock(),
        )

    def get_session(self, session_id):
        if session_id != 'session_test':
            raise app_module.StateNotFound(session_id)
        return self.entry


class HTTPServiceTest(unittest.TestCase):
    def setUp(self):
        self.previous_key = os.environ.pop('XHS_SERVICE_API_KEY', None)
        self.client = TestClient(app_module.app)

    def tearDown(self):
        if self.previous_key is not None:
            os.environ['XHS_SERVICE_API_KEY'] = self.previous_key
        else:
            os.environ.pop('XHS_SERVICE_API_KEY', None)

    def test_health_is_public_but_ready_and_v1_fail_closed(self):
        self.assertEqual(self.client.get('/healthz').status_code, 200)
        self.assertEqual(self.client.get('/readyz').status_code, 503)
        self.assertEqual(
            self.client.post('/v1/creator/logins/qr', json={}).status_code,
            503,
        )

    def test_wrong_service_key_is_rejected(self):
        os.environ['XHS_SERVICE_API_KEY'] = 'expected-service-secret-value-1234'
        response = self.client.post(
            '/v1/creator/logins/qr',
            headers={'Authorization': 'Bearer wrong-secret'},
            json={},
        )
        self.assertEqual(response.status_code, 401)

    def test_openapi_describes_login_and_publish_responses(self):
        schema = self.client.get('/openapi.json').json()
        qr_response = schema['paths']['/v1/creator/logins/qr']['post'][
            'responses'
        ]['200']['content']['application/json']['schema']
        publish_response = schema['paths']['/v1/creator/posts']['post'][
            'responses'
        ]['200']['content']['application/json']['schema']
        self.assertIn('anyOf', qr_response)
        self.assertEqual(
            publish_response['$ref'],
            '#/components/schemas/PublishResponse',
        )

    def test_openapi_exposes_every_implemented_creator_capability(self):
        paths = self.client.get('/openapi.json').json()['paths']
        expected = {
            '/v1/creator/account',
            '/v1/creator/topics/search',
            '/v1/creator/locations/search',
            '/v1/creator/logins/phone/zones',
            '/v1/creator/media/permit',
            '/v1/creator/media/upload',
            '/v1/creator/videos/transcode',
            '/v1/creator/files/encryption',
            '/v1/creator/posts/posted/page',
            '/v1/creator/posts/posted/all',
        }
        self.assertTrue(expected.issubset(paths))

    def test_creator_capability_routes_forward_session_proxy_and_arguments(self):
        os.environ['XHS_SERVICE_API_KEY'] = 'expected-service-secret-value-1234'
        headers = {
            'Authorization': 'Bearer expected-service-secret-value-1234'
        }
        proxies = {
            'https': 'http://proxy.test:8080',
        }
        base = {'session_id': 'session_test', 'proxies': proxies}
        media = base64.b64encode(b'media-bytes').decode()
        fake_store = CapabilityStore()

        requests = [
            ('/v1/creator/account', base),
            ('/v1/creator/topics/search', {**base, 'keyword': '旅行'}),
            ('/v1/creator/locations/search', {**base, 'keyword': '上海'}),
            ('/v1/creator/media/permit', {**base, 'media_type': 'image'}),
            (
                '/v1/creator/media/upload',
                {**base, 'media_type': 'image', 'media': {'data': media}},
            ),
            ('/v1/creator/videos/transcode', {**base, 'video_id': 'video_1'}),
            ('/v1/creator/files/encryption', {**base, 'file_id': 'file_1'}),
            (
                '/v1/creator/posts/posted/page',
                {**base, 'page': 2, 'tab': 1},
            ),
            ('/v1/creator/posts/posted/all', {**base, 'tab': 1}),
        ]
        with patch.object(app_module, 'store', fake_store):
            responses = [
                self.client.post(path, headers=headers, json=payload)
                for path, payload in requests
            ]

        for response in responses:
            self.assertEqual(response.status_code, 200, response.text)
            self.assertTrue(response.json()['success'])
        self.assertEqual(
            responses[3].json()['result'],
            {'permit': {'permits': []}, 'x_t': '1700000000'},
        )
        fake_store.api.get_user_info.assert_called_once_with(proxies=proxies)
        fake_store.api.get_topic.assert_called_once_with('旅行', proxies=proxies)
        fake_store.api.get_location_info.assert_called_once_with(
            '上海', proxies=proxies
        )
        fake_store.api.get_file_ids.assert_called_once_with(
            'image', proxies=proxies
        )
        fake_store.api.upload_media.assert_called_once_with(
            b'media-bytes', 'image', proxies=proxies
        )
        fake_store.api.query_transcode.assert_called_once_with(
            'video_1', proxies=proxies
        )
        fake_store.api.encryption.assert_called_once_with(
            'file_1', proxies=proxies
        )
        fake_store.api.get_posted_notes_page.assert_called_once_with(
            proxies=proxies,
            page=2,
            tab=1,
        )
        fake_store.api.get_all_posted_notes.assert_called_once_with(
            proxies=proxies,
            tab=1,
        )

    def test_phone_zones_are_normalized_for_a_dropdown_and_use_the_proxy(self):
        os.environ['XHS_SERVICE_API_KEY'] = 'expected-service-secret-value-1234'
        proxies = {'https': 'http://proxy.test:8080'}
        login = SimpleNamespace(
            get_zone_list=Mock(
                return_value=(
                    True,
                    [
                        {'name': '中国大陆', 'code': '+86'},
                        {'countryName': '美国', 'countryCode': '1'},
                        {'country': '加拿大', 'phone_code': '1'},
                        {'name': 'invalid'},
                    ],
                    {},
                )
            ),
            close=Mock(),
        )
        with patch.object(
            app_module,
            'XHSCreatorLoginApi',
            return_value=login,
        ) as login_factory:
            response = self.client.post(
                '/v1/creator/logins/phone/zones',
                headers={
                    'Authorization': 'Bearer expected-service-secret-value-1234'
                },
                json={'proxies': proxies},
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.json(),
            {
                'items': [
                    {'name': '中国大陆', 'code': '86'},
                    {'name': '美国', 'code': '1'},
                    {'name': '加拿大', 'code': '1'},
                ],
                'default_code': '86',
            },
        )
        login_factory.assert_called_once_with(proxies=proxies)
        login.get_zone_list.assert_called_once_with()
        login.close.assert_called_once_with()

    def test_publish_uses_spider_xhs_complete_post_workflow(self):
        os.environ['XHS_SERVICE_API_KEY'] = 'expected-service-secret-value-1234'
        fake_store = FakeStore()
        image = base64.b64encode(b'image-bytes').decode()
        with patch.object(app_module, 'store', fake_store):
            response = self.client.post(
                '/v1/creator/posts',
                headers={
                    'Authorization': 'Bearer expected-service-secret-value-1234'
                },
                json={
                    'session_id': 'session_test',
                    'title': '标题',
                    'description': '正文',
                    'media_type': 'image',
                    'images': [{'data': image}],
                    'topics': ['旅行'],
                    'proxies': {
                        'http': 'http://proxy.test:8080',
                        'https': 'http://proxy.test:8080',
                    },
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        note, proxies = fake_store.published
        self.assertEqual(note['desc'], '正文')
        self.assertEqual(note['images'], [b'image-bytes'])
        self.assertEqual(note['topics'], ['旅行'])
        self.assertEqual(
            proxies,
            {
                'http': 'http://proxy.test:8080',
                'https': 'http://proxy.test:8080',
            },
        )

    def test_qr_login_binds_request_proxy_to_login_client(self):
        os.environ['XHS_SERVICE_API_KEY'] = 'expected-service-secret-value-1234'
        proxies = {
            'http': 'http://proxy.test:8080',
            'https': 'http://proxy.test:8080',
        }
        login = SimpleNamespace(
            start_qrcode_session=Mock(
                return_value={
                    'status': 'waiting_scan',
                    'message': '请扫描二维码',
                    'qr_id': 'qr_1',
                    'qr_url': 'xhs://qr',
                    'support_channels': [],
                }
            ),
            close=Mock(),
        )
        fake_store = SimpleNamespace(
            login_ttl_seconds=600,
            add_login=Mock(return_value='login_1'),
        )
        with patch.object(app_module, 'store', fake_store), patch.object(
            app_module,
            'XHSCreatorLoginApi',
            return_value=login,
        ) as login_factory:
            response = self.client.post(
                '/v1/creator/logins/qr',
                headers={
                    'Authorization': 'Bearer expected-service-secret-value-1234'
                },
                json={'proxies': proxies},
            )

        self.assertEqual(response.status_code, 200)
        login_factory.assert_called_once_with(proxies=proxies)
        fake_store.add_login.assert_called_once_with(
            login,
            'qrcode',
            qr_id='qr_1',
        )


if __name__ == '__main__':
    unittest.main()
