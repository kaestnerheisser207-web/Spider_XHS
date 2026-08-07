import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from apis.xhs_pc_login_apis import PcLoginUpstreamError, XHSLoginApi


class PcLoginDiagnosticsTest(unittest.TestCase):
    def test_qr_finalize_rejection_keeps_only_safe_response_fields(self):
        login = XHSLoginApi.__new__(XHSLoginApi)
        login.base_url = 'https://example.test'
        login.proxies = {'https': 'http://proxy-user:proxy-password@test:8080'}
        login.http = Mock()
        login.http.get.return_value = SimpleNamespace(
            status_code=200,
            json=Mock(
                return_value={
                    'success': False,
                    'code': -1,
                    'msg': '登录异常',
                    'data': {
                        'code_status': 2,
                        'login_info': {'session': 'secret-login-session'},
                        'authorization': 'secret-authorization',
                    },
                    'cookies': 'secret-cookie',
                }
            ),
        )
        login._signed_request_params = Mock(return_value=({}, None))
        login._cookies_for_url = Mock(return_value={})
        login._merge_response_cookies = Mock()

        with (
            patch(
                'apis.xhs_pc_login_apis.build_pc_login_headers',
                side_effect=lambda headers, *_args, **_kwargs: headers,
            ),
            self.assertRaises(PcLoginUpstreamError) as raised,
        ):
            login._login_by_qrcode_status(
                'secret-qr-id',
                'secret-qr-code',
                {'web_session': 'secret-visitor-session'},
            )

        error = raised.exception
        self.assertEqual(error.code, 'pc_qr_finalize_rejected')
        self.assertEqual(str(error), '登录异常')
        self.assertEqual(
            error.diagnostics,
            {
                'phase': 'qr_finalize',
                'http_status': 200,
                'upstream_success': False,
                'upstream_code': -1,
                'code_status': 2,
                'login_session_present': True,
            },
        )
        rendered = repr(error.diagnostics)
        for secret in (
            'secret-login-session',
            'secret-authorization',
            'secret-cookie',
            'secret-qr-id',
            'secret-qr-code',
            'secret-visitor-session',
            'proxy-password',
        ):
            self.assertNotIn(secret, rendered)


if __name__ == '__main__':
    unittest.main()
