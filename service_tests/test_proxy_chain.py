import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from apis.xhs_creator_apis import XHS_Creator_Apis
from xhs_utils.xhs_core.http import BrowserHttpClient
from xhs_utils.xhs_creator.auth import XHSCreatorAuth
from xhs_utils.xhs_creator.params import generate_request_params


PROXIES = {
    'http': 'http://proxy.test:8080',
    'https': 'http://proxy.test:8080',
}


class ProxyChainTest(unittest.TestCase):
    def test_completed_login_transfers_bound_proxy_to_auth(self):
        login = SimpleNamespace(
            proxies=PROXIES,
            http=object(),
            profile=object(),
            host_cookies_snapshot=Mock(return_value={}),
            host_cookie_state=Mock(return_value={}),
        )
        with patch.object(XHSCreatorAuth, '__init__', return_value=None) as init:
            XHSCreatorAuth.from_completed_login(
                login,
                'a1=test; web_session=secret',
                login_source='qrcode',
            )

        self.assertEqual(init.call_args.kwargs['proxies'], PROXIES)
        self.assertIs(init.call_args.kwargs['http_client'], login.http)
        self.assertIs(init.call_args.kwargs['profile'], login.profile)

    def test_signing_material_refresh_receives_request_proxy(self):
        material = SimpleNamespace(device_tag='a1')
        auth = SimpleNamespace(
            profile=SimpleNamespace(
                resolve_mns_material=Mock(return_value=('0101', material))
            ),
            validate=Mock(),
            ensure_ds_material=Mock(),
        )
        with patch(
            'xhs_utils.xhs_creator.params.generate_profile_request_params',
            return_value=({}, {}, ''),
        ):
            generate_request_params(auth, '/api/test', proxies=PROXIES)

        auth.ensure_ds_material.assert_called_once_with(proxies=PROXIES)

    def test_transport_uses_bound_proxy_and_explicit_override(self):
        client = BrowserHttpClient.__new__(BrowserHttpClient)
        client.proxies = PROXIES
        client.impersonate = 'chrome146'
        client.accept_encoding = 'gzip'
        client.http_version = 'v2tls'
        client.session = Mock()

        client.get('https://example.test/default')
        self.assertEqual(
            client.session.request.call_args.kwargs['proxies'],
            PROXIES,
        )

        override = {'https': 'http://override.test:9090'}
        client.get('https://example.test/override', proxies=override)
        self.assertEqual(
            client.session.request.call_args.kwargs['proxies'],
            override,
        )

    def test_image_publish_passes_proxy_to_every_business_step(self):
        api = XHS_Creator_Apis.__new__(XHS_Creator_Apis)
        api.base_url = 'https://creator.xiaohongshu.com'
        api.edith_url = 'https://edith.xiaohongshu.com'
        api.http = Mock()
        api.http.post.return_value.json.return_value = {
            'success': True,
            'msg': '成功',
        }
        api.get_location_info = Mock(
            return_value=(
                True,
                '成功',
                {
                    'data': {
                        'poi_list': [
                            {
                                'name': '地点',
                                'full_address': '地址',
                                'poi_id': 'poi_1',
                                'poi_type': 1,
                            }
                        ]
                    }
                },
            )
        )
        api.upload_media = Mock(
            return_value=(
                True,
                '成功',
                {
                    'fileIds': 'file_1',
                    'width': 100,
                    'height': 100,
                    'file_size': 5,
                    'mime_type': 'image/png',
                },
            )
        )
        api.get_topic = Mock(
            return_value=(
                True,
                '成功',
                {
                    'data': {
                        'topic_info_dtos': [
                            {
                                'id': 'topic_1',
                                'link': 'xhs://topic/1',
                                'name': '旅行',
                            }
                        ]
                    }
                },
            )
        )
        api._request_params = Mock(return_value=({}, {}, '{}'))

        with patch(
            'apis.xhs_creator_apis.generate_x_rap_param',
            return_value='signed',
        ), patch(
            'apis.xhs_creator_apis.load_creator_rap_fingerprint_hex',
            return_value='00',
        ):
            success, _, _ = api.post_note(
                {
                    'title': '标题',
                    'desc': '正文',
                    'media_type': 'image',
                    'images': [b'image'],
                    'location': '上海',
                    'topics': ['旅行'],
                },
                proxies=PROXIES,
            )

        self.assertTrue(success)
        api.get_location_info.assert_called_once_with('上海', proxies=PROXIES)
        api.upload_media.assert_called_once_with(
            b'image',
            'image',
            proxies=PROXIES,
        )
        api.get_topic.assert_called_once_with('旅行', proxies=PROXIES)
        self.assertEqual(
            api._request_params.call_args.kwargs['proxies'],
            PROXIES,
        )
        self.assertEqual(
            api.http.post.call_args.kwargs['proxies'],
            PROXIES,
        )

    def test_video_publish_passes_proxy_to_uploads_and_transcode(self):
        api = XHS_Creator_Apis.__new__(XHS_Creator_Apis)
        api.base_url = 'https://creator.xiaohongshu.com'
        api.edith_url = 'https://edith.xiaohongshu.com'
        api.http = Mock()
        api.http.post.return_value.json.return_value = {
            'success': True,
            'msg': '成功',
        }
        api.extract_video_cover_and_metadata = Mock(
            return_value=(b'cover', {'video': {}, 'audio': {}})
        )
        api.upload_media = Mock(
            side_effect=[
                (
                    True,
                    '成功',
                    {
                        'fileIds': 'video_file',
                        'video_id': 'video_1',
                        'file_size': 10,
                    },
                ),
                (
                    True,
                    '成功',
                    {
                        'fileIds': 'cover_file',
                        'width': 100,
                        'height': 100,
                        'file_size': 5,
                    },
                ),
            ]
        )
        api.query_transcode = Mock(
            return_value=(True, '成功', {'data': {'status': 2}})
        )
        api._request_params = Mock(return_value=({}, {}, '{}'))

        with patch(
            'apis.xhs_creator_apis.generate_x_rap_param',
            return_value='signed',
        ), patch(
            'apis.xhs_creator_apis.load_creator_rap_fingerprint_hex',
            return_value='00',
        ):
            success, _, _ = api.post_note(
                {
                    'title': '标题',
                    'desc': '正文',
                    'media_type': 'video',
                    'video': b'video',
                },
                proxies=PROXIES,
            )

        self.assertTrue(success)
        self.assertEqual(
            api.upload_media.call_args_list[0].kwargs['proxies'],
            PROXIES,
        )
        self.assertEqual(
            api.upload_media.call_args_list[1].kwargs['proxies'],
            PROXIES,
        )
        api.query_transcode.assert_called_once_with(
            'video_1',
            proxies=PROXIES,
        )
        self.assertEqual(
            api._request_params.call_args.kwargs['proxies'],
            PROXIES,
        )
        self.assertEqual(
            api.http.post.call_args.kwargs['proxies'],
            PROXIES,
        )


if __name__ == '__main__':
    unittest.main()
