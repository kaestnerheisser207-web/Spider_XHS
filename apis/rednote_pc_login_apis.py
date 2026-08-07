"""Pure-HTTP Rednote PC phone-login client."""

from apis.xhs_pc_login_apis import XHSLoginApi
from xhs_utils.xhs_core.auth import REDNOTE_PC_PLATFORM_CONFIG


class RednoteLoginApi(XHSLoginApi):
    """Run the PC login state machine against the Rednote web surface."""

    def __init__(self, proxies=None, **kwargs):
        profile_fields = dict(kwargs.pop('web_profile_fields', None) or {})
        profile_fields.setdefault(
            'x66',
            {
                'referer': '',
                'location': REDNOTE_PC_PLATFORM_CONFIG.origin('web') + '/explore',
                'frame': 0,
            },
        )
        super().__init__(
            proxies=proxies,
            platform_config=REDNOTE_PC_PLATFORM_CONFIG,
            web_profile_fields=profile_fields,
            **kwargs,
        )


__all__ = ['RednoteLoginApi']
