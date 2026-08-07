import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apis.rednote_pc_login_apis import RednoteLoginApi
from xhs_service import app as app_module
from xhs_service import rednote as rednote_module
from xhs_service.rednote import create_rednote_router
from xhs_service.state import StateNotFound
from xhs_utils.xhs_core.auth import PC_PLATFORM_CONFIG, REDNOTE_PC_PLATFORM_CONFIG
from xhs_utils.xhs_pc.params import get_request_headers_template


class FakeRednoteStore:
    login_ttl_seconds = 600
    session_ttl_seconds = 86400

    def __init__(self):
        self.login_entry = None
        self.completed_login = None
        self.session = None

    def add_login(self, client, cookies, *, phone, zone='86'):
        self.login_entry = SimpleNamespace(
            client=client,
            cookies=cookies,
            phone=phone,
            zone=zone,
            lock=threading.Lock(),
        )
        return 'rednote_login_test'

    def get_login(self, login_id):
        if login_id != 'rednote_login_test' or self.login_entry is None:
            raise StateNotFound(login_id)
        return self.login_entry

    def complete_login(self, login_id, cookies, account):
        self.completed_login = (login_id, cookies, account)
        self.session = SimpleNamespace()
        return 'rednote_session_test'

    def get_session(self, session_id):
        if session_id != 'rednote_session_test' or self.session is None:
            raise StateNotFound(session_id)
        return self.session

    def discard_session(self, session_id):
        if session_id != 'rednote_session_test' or self.session is None:
            return False
        self.session = None
        return True


def no_service_auth():
    return None


class RednoteHTTPServiceTest(unittest.TestCase):
    def test_main_openapi_exposes_only_the_rednote_phone_session_surface(self):
        paths = app_module.app.openapi()['paths']
        actual = {path for path in paths if path.startswith('/v1/rednote/')}
        self.assertEqual(
            actual,
            {
                '/v1/rednote/logins/phone',
                '/v1/rednote/logins/phone/{login_id}/verify',
                '/v1/rednote/sessions/{session_id}',
            },
        )

    def test_rednote_platform_is_independent_from_xiaohongshu_pc(self):
        self.assertEqual(PC_PLATFORM_CONFIG.origin('api'), 'https://edith.xiaohongshu.com')
        self.assertEqual(PC_PLATFORM_CONFIG.cookie_domain, '.xiaohongshu.com')
        self.assertEqual(REDNOTE_PC_PLATFORM_CONFIG.origin('web'), 'https://www.rednote.com')
        self.assertEqual(REDNOTE_PC_PLATFORM_CONFIG.origin('api'), 'https://webapi.rednote.com')
        self.assertEqual(REDNOTE_PC_PLATFORM_CONFIG.origin('security'), 'https://as.rednote.com')
        self.assertEqual(REDNOTE_PC_PLATFORM_CONFIG.origin('sem'), 'https://pages.xiaohongshu.com')
        self.assertEqual(REDNOTE_PC_PLATFORM_CONFIG.cookie_domain, '.rednote.com')

        headers = get_request_headers_template(
            method='GET',
            web_origin=REDNOTE_PC_PLATFORM_CONFIG.origin('web'),
        )
        self.assertEqual(headers['origin'], 'https://www.rednote.com')
        self.assertEqual(headers['referer'], 'https://www.rednote.com/')

        client = RednoteLoginApi()
        try:
            self.assertEqual(client.base_url, 'https://webapi.rednote.com')
            self.assertEqual(client.as_url, 'https://as.rednote.com')
            self.assertEqual(client.home_url, 'https://www.rednote.com/explore')
        finally:
            client.close()

    def test_phone_login_uses_one_rednote_client_across_start_and_verify(self):
        store = FakeRednoteStore()
        app = FastAPI()
        app.include_router(create_rednote_router(store, no_service_auth))
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

        with patch.object(rednote_module, 'RednoteLoginApi', return_value=login):
            start_response = client.post(
                '/v1/rednote/logins/phone',
                json={'phone': '13800000000', 'zone': '86'},
            )
            verify_response = client.post(
                '/v1/rednote/logins/phone/rednote_login_test/verify',
                json={'code': '123456'},
            )

        self.assertEqual(start_response.status_code, 200, start_response.text)
        self.assertEqual(start_response.json()['status'], 'waiting_code')
        self.assertEqual(verify_response.status_code, 200, verify_response.text)
        self.assertEqual(verify_response.json()['status'], 'authenticated')
        login.ensure_webprofile.assert_called_once_with(cookies)
        login.send_phone_code.assert_called_once_with('13800000000', cookies, '86')
        login.login_by_phone.assert_called_once_with(
            '13800000000',
            '123456',
            cookies,
            '86',
        )
        self.assertEqual(
            store.completed_login,
            (
                'rednote_login_test',
                authenticated_cookies,
                {'guest': False, 'user_id': 'user_1'},
            ),
        )
        login.close.assert_not_called()

    def test_invalid_code_is_a_non_gateway_business_rejection(self):
        store = FakeRednoteStore()
        app = FastAPI()
        app.include_router(create_rednote_router(store, no_service_auth))
        client = TestClient(app)
        cookies = {'a1': 'a1_value', 'web_session': 'visitor_session'}
        login = SimpleNamespace(
            generate_init_cookies=Mock(return_value=cookies),
            ensure_webprofile=Mock(return_value='gid_1'),
            send_phone_code=Mock(return_value=(True, '成功', {})),
            login_by_phone=Mock(return_value=(False, '验证码错误', {'cookies': cookies})),
            close=Mock(),
        )

        with patch.object(rednote_module, 'RednoteLoginApi', return_value=login):
            self.assertEqual(
                client.post(
                    '/v1/rednote/logins/phone',
                    json={'phone': '13800000000', 'zone': '86'},
                ).status_code,
                200,
            )
            response = client.post(
                '/v1/rednote/logins/phone/rednote_login_test/verify',
                json={'code': '000000'},
            )

        self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(
            response.json()['detail'],
            {
                'code': 'rednote_phone_code_rejected',
                'message': '验证码错误',
            },
        )
        login.close.assert_not_called()


if __name__ == '__main__':
    unittest.main()
