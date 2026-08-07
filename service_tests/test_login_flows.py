import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from apis.xhs_creator_login_apis import (
    QR_STATUS_SUCCESS,
    QR_STATUS_WAIT_CONFIRM,
    XHSCreatorLoginApi,
)


def login_stub() -> XHSCreatorLoginApi:
    login = XHSCreatorLoginApi.__new__(XHSCreatorLoginApi)
    login.profile = SimpleNamespace(cookie_map={'a1': 'test'})
    login._complete_security = Mock()
    login._reset_anonymous_session = Mock()
    return login


class NonInteractiveLoginTest(unittest.TestCase):
    def test_start_qrcode_returns_immediately_for_polling(self):
        login = login_stub()
        login._prepare_login_session = Mock(
            return_value=({'a1': 'test'}, {'active': False})
        )
        login.generate_qrcode = Mock(
            return_value=(
                True,
                '成功',
                {
                    'qr_id': 'qr_1',
                    'qr_url': 'xhs://qr',
                    'support_channels': [],
                },
            )
        )

        result = login.start_qrcode_session()

        self.assertEqual(result['status'], 'waiting_scan')
        self.assertEqual(result['qr_id'], 'qr_1')
        login._complete_security.assert_called_once_with()

    def test_poll_qrcode_maps_waiting_and_success(self):
        login = login_stub()
        login.query_qrcode_status = Mock(
            return_value={
                'success': False,
                'message': '请在手机上确认登录',
                'status': QR_STATUS_WAIT_CONFIRM,
                'avatar': 'avatar',
            }
        )
        self.assertEqual(
            login.poll_qrcode_session('qr_1')['status'],
            'waiting_confirm',
        )

        login.query_qrcode_status = Mock(
            return_value={
                'success': True,
                'message': '验证成功',
                'status': QR_STATUS_SUCCESS,
                'cookies': {'web_session': 'secret'},
                'avatar': '',
            }
        )
        login._accept_session = Mock(return_value='web_session=secret')
        result = login.poll_qrcode_session('qr_1')
        self.assertEqual(result['status'], 'authenticated')
        self.assertEqual(result['cookies'], 'web_session=secret')

    def test_phone_flow_has_no_terminal_input(self):
        login = login_stub()
        login._prepare_login_session = Mock(
            return_value=({'a1': 'test'}, {'active': False})
        )
        login.send_phone_code = Mock(return_value=(True, '成功', {}))
        started = login.start_phone_session('13800000000')
        self.assertEqual(started['status'], 'waiting_code')

        login.login_by_phone = Mock(
            return_value=(True, '成功', {'cookies': {'web_session': 'secret'}})
        )
        login._accept_session = Mock(return_value='web_session=secret')
        completed = login.complete_phone_session('13800000000', '123456')
        self.assertEqual(completed['status'], 'authenticated')

    def test_terminal_helpers_keep_failure_as_none(self):
        login = login_stub()
        login.start_qrcode_session = Mock(side_effect=RuntimeError('blocked'))
        self.assertIsNone(login.qrcode_login())

        login.start_phone_session = Mock(side_effect=RuntimeError('blocked'))
        with patch('builtins.input', return_value='13800000000'):
            self.assertIsNone(login.phone_login())


if __name__ == '__main__':
    unittest.main()
