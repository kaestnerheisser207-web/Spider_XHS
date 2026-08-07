import base64
import unittest

from pydantic import ValidationError

from xhs_service.models import MediaInput, PublishRequest, QRLoginRequest


class MediaInputTest(unittest.TestCase):
    def test_decodes_plain_base64_and_data_url(self):
        encoded = base64.b64encode(b'image-bytes').decode()
        self.assertEqual(MediaInput(data=encoded).decode(), b'image-bytes')
        self.assertEqual(
            MediaInput(data=f'data:image/png;base64,{encoded}').decode(),
            b'image-bytes',
        )

    def test_rejects_invalid_base64(self):
        with self.assertRaisesRegex(ValueError, 'valid base64'):
            MediaInput(data='not base64!').decode()


class PublishRequestTest(unittest.TestCase):
    def test_image_post_requires_images(self):
        with self.assertRaises(ValidationError):
            PublishRequest(session_id='session_test', media_type='image')

    def test_video_post_rejects_images(self):
        encoded = base64.b64encode(b'video').decode()
        with self.assertRaises(ValidationError):
            PublishRequest(
                session_id='session_test',
                media_type='video',
                video={'data': encoded},
                images=[{'data': encoded}],
            )


class ProxyRequestTest(unittest.TestCase):
    def test_accepts_https_or_all_proxy(self):
        https = QRLoginRequest(
            proxies={'https': 'http://user:pass@proxy.test:8080'}
        )
        all_proxy = QRLoginRequest(
            proxies={'all': 'socks5h://proxy.test:1080'}
        )
        self.assertIn('https', https.proxies)
        self.assertIn('all', all_proxy.proxies)

    def test_rejects_proxy_that_cannot_cover_xhs_https_requests(self):
        with self.assertRaisesRegex(ValidationError, 'every XHS endpoint'):
            QRLoginRequest(
                proxies={'http': 'http://proxy.test:8080'}
            )


if __name__ == '__main__':
    unittest.main()
