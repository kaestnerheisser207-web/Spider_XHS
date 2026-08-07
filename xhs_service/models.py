from __future__ import annotations

import base64
import binascii
from typing import Any, Literal, Optional
from urllib.parse import urlparse

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)


class RequestModel(BaseModel):
    model_config = ConfigDict(extra='forbid', populate_by_name=True)


class ProxiedRequestModel(RequestModel):
    proxies: Optional[dict[str, str]] = None

    @field_validator('proxies')
    @classmethod
    def validate_proxies(
        cls,
        proxies: Optional[dict[str, str]],
    ) -> Optional[dict[str, str]]:
        if proxies is None:
            return None
        if not proxies:
            raise ValueError('proxies must not be empty when provided')
        if not {'https', 'all'}.intersection(proxies):
            raise ValueError(
                'proxies must contain https or all because every XHS endpoint '
                'uses HTTPS'
            )
        allowed_keys = {'all', 'http', 'https'}
        if set(proxies) - allowed_keys:
            raise ValueError('proxy keys must be all, http, or https')
        allowed_schemes = {
            'http',
            'https',
            'socks4',
            'socks4a',
            'socks5',
            'socks5h',
        }
        normalized = {}
        for key, value in proxies.items():
            url = str(value).strip()
            parsed = urlparse(url)
            if parsed.scheme.lower() not in allowed_schemes or not parsed.hostname:
                raise ValueError('proxy values must be valid proxy URLs')
            normalized[key] = url
        return normalized


class CookieSessionRequest(ProxiedRequestModel):
    cookies: SecretStr
    verify_session: bool = Field(default=True, alias='validate')


class QRLoginRequest(ProxiedRequestModel):
    pass


class PhoneLoginRequest(ProxiedRequestModel):
    phone: str = Field(min_length=1)
    zone: str = Field(default='86', min_length=1)


class PhoneZoneListRequest(ProxiedRequestModel):
    pass


class PhoneVerifyRequest(RequestModel):
    code: SecretStr


class MediaInput(RequestModel):
    data: str = Field(
        min_length=1,
        description='Base64 bytes or a base64 data URL.',
    )

    def decode(self) -> bytes:
        encoded = self.data.strip()
        if encoded.startswith('data:'):
            header, separator, encoded = encoded.partition(',')
            if not separator or ';base64' not in header.lower():
                raise ValueError('media data URL must use base64 encoding')
        try:
            value = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError('media data is not valid base64') from error
        if not value:
            raise ValueError('media data is empty')
        return value


class AuthenticatedCreatorRequest(ProxiedRequestModel):
    session_id: str = Field(min_length=1)


class AccountInfoRequest(AuthenticatedCreatorRequest):
    pass


class TopicSearchRequest(AuthenticatedCreatorRequest):
    keyword: str = Field(min_length=1)


class LocationSearchRequest(AuthenticatedCreatorRequest):
    keyword: str = Field(min_length=1)


class MediaPermitRequest(AuthenticatedCreatorRequest):
    media_type: Literal['image', 'video']


class MediaUploadRequest(MediaPermitRequest):
    media: MediaInput


class VideoTranscodeRequest(AuthenticatedCreatorRequest):
    video_id: str = Field(min_length=1)


class FileEncryptionRequest(AuthenticatedCreatorRequest):
    file_id: str = Field(min_length=1)


class PostedNotesPageRequest(AuthenticatedCreatorRequest):
    page: int = Field(default=0, ge=0)
    tab: int = Field(default=0, ge=0)


class PostedNotesAllRequest(AuthenticatedCreatorRequest):
    tab: int = Field(default=0, ge=0)


class PublishRequest(AuthenticatedCreatorRequest):
    title: str = ''
    description: str = ''
    media_type: Literal['image', 'video'] = 'image'
    images: list[MediaInput] = Field(default_factory=list)
    video: Optional[MediaInput] = None
    scheduled_at_ms: Optional[int] = None
    location: Optional[str] = None
    privacy_type: int = 1
    topics: list[str] = Field(default_factory=list)
    @model_validator(mode='after')
    def validate_media(self) -> 'PublishRequest':
        if self.media_type == 'image':
            if not self.images:
                raise ValueError('images are required for an image post')
            if self.video is not None:
                raise ValueError('video must be omitted for an image post')
        else:
            if self.video is None:
                raise ValueError('video is required for a video post')
            if self.images:
                raise ValueError('images must be omitted for a video post')
        return self


class PcCookieSessionRequest(ProxiedRequestModel):
    cookies: SecretStr


class AuthenticatedPcRequest(ProxiedRequestModel):
    session_id: str = Field(min_length=1, max_length=255)


class PcAccountRequest(AuthenticatedPcRequest):
    pass


class PcSearchKeywordRequest(AuthenticatedPcRequest):
    keyword: str = Field(min_length=1, max_length=255)


class PcSearchNotesPageRequest(AuthenticatedPcRequest):
    query: str = Field(min_length=1, max_length=255)
    page: int = Field(default=1, ge=1, le=2_147_483_647)
    sort_type: int = Field(default=0, ge=0, le=2_147_483_647)
    note_type: int = Field(default=0, ge=0, le=2_147_483_647)
    note_time: int = Field(default=0, ge=0, le=2_147_483_647)
    note_range: int = Field(default=0, ge=0, le=2_147_483_647)
    position_distance: int = Field(default=0, ge=0, le=2_147_483_647)
    geo: str = Field(default='', max_length=255)
    search_id: Optional[str] = Field(default=None, max_length=255)


class PcSearchNotesAllRequest(AuthenticatedPcRequest):
    query: str = Field(min_length=1, max_length=255)
    limit: int = Field(default=20, ge=1, le=10_000)
    sort_type: int = Field(default=0, ge=0, le=2_147_483_647)
    note_type: int = Field(default=0, ge=0, le=2_147_483_647)
    note_time: int = Field(default=0, ge=0, le=2_147_483_647)
    note_range: int = Field(default=0, ge=0, le=2_147_483_647)
    position_distance: int = Field(default=0, ge=0, le=2_147_483_647)
    geo: str = Field(default='', max_length=255)


class PcSearchUsersPageRequest(AuthenticatedPcRequest):
    query: str = Field(min_length=1, max_length=255)
    page: int = Field(default=1, ge=1, le=2_147_483_647)


class PcSearchUsersAllRequest(AuthenticatedPcRequest):
    query: str = Field(min_length=1, max_length=255)
    limit: int = Field(default=20, ge=1, le=10_000)


class PcNoteURLRequest(AuthenticatedPcRequest):
    url: str = Field(min_length=1, max_length=4096)


class PcOuterCommentPageRequest(AuthenticatedPcRequest):
    note_id: str = Field(min_length=1, max_length=255)
    cursor: str = Field(default='', max_length=2048)
    xsec_token: str = Field(min_length=1, max_length=4096)


class PcOuterCommentAllRequest(AuthenticatedPcRequest):
    note_id: str = Field(min_length=1, max_length=255)
    xsec_token: str = Field(min_length=1, max_length=4096)


class PcInnerCommentPageRequest(AuthenticatedPcRequest):
    comment: dict[str, Any]
    cursor: str = Field(default='', max_length=2048)
    xsec_token: str = Field(min_length=1, max_length=4096)


class PcProfileRequest(AuthenticatedPcRequest):
    user_id: str = Field(min_length=1, max_length=255)


class PcUserPageRequest(PcProfileRequest):
    cursor: str = Field(default='', max_length=2048)
    xsec_token: str = Field(default='', max_length=4096)
    xsec_source: str = Field(default='', max_length=255)


class PcUserAllRequest(AuthenticatedPcRequest):
    user_url: str = Field(min_length=1, max_length=4096)


class PcHomefeedPageRequest(AuthenticatedPcRequest):
    category: str = Field(min_length=1, max_length=255)
    cursor_score: str = Field(default='', max_length=2048)
    refresh_type: int = Field(default=1, ge=0, le=2_147_483_647)
    note_index: int = Field(default=0, ge=0, le=2_147_483_647)
    num: int = Field(default=20, ge=1, le=10_000)
    need_num: int = Field(default=10, ge=1, le=10_000)


class PcHomefeedAllRequest(AuthenticatedPcRequest):
    category: str = Field(min_length=1, max_length=255)
    limit: int = Field(default=20, ge=1, le=10_000)


class PcCursorRequest(AuthenticatedPcRequest):
    cursor: str = Field(default='', max_length=2048)


class PcVideoResolveRequest(RequestModel):
    note_id: str = Field(min_length=1, max_length=255)


class PcImageResolveRequest(RequestModel):
    image_url: str = Field(min_length=1, max_length=4096)


class AuthenticatedSessionResponse(BaseModel):
    status: Literal['authenticated']
    message: str
    session_id: str
    expires_in_seconds: int


class CookieSessionResponse(AuthenticatedSessionResponse):
    account: Optional[dict[str, Any]] = None


class QRLoginPendingResponse(BaseModel):
    status: Literal['waiting_scan']
    message: str
    login_id: str
    expires_in_seconds: int
    qr_id: str
    qr_url: str
    support_channels: list[Any] = Field(default_factory=list)


class QRLoginPollResponse(BaseModel):
    status: Literal['waiting_scan', 'waiting_confirm', 'expired', 'failed']
    message: str
    login_id: str
    xhs_status: Optional[int] = None
    avatar: str = ''


class PhoneLoginPendingResponse(BaseModel):
    status: Literal['waiting_code']
    message: str
    login_id: str
    expires_in_seconds: int


class PhoneLoginFailedResponse(BaseModel):
    status: Literal['failed']
    message: str
    login_id: str


class PhoneZoneItem(BaseModel):
    name: str
    code: str


class PhoneZoneListResponse(BaseModel):
    items: list[PhoneZoneItem]
    default_code: str = '86'


class SessionStatusResponse(BaseModel):
    status: Literal['authenticated']
    session_id: str
    expires_in_seconds: int


class SessionClosedResponse(BaseModel):
    status: Literal['closed']


class CreatorAPIResponse(BaseModel):
    success: bool
    message: str
    result: Any


class PublishResponse(CreatorAPIResponse):
    pass


class PcAuthenticatedSessionResponse(BaseModel):
    status: Literal['authenticated']
    message: str
    session_id: str
    expires_in_seconds: int
    account: Optional[dict[str, Any]] = None


class PcQRLoginPendingResponse(BaseModel):
    status: Literal['waiting_scan']
    message: str
    login_id: str
    expires_in_seconds: int
    qr_id: str
    qr_url: str


class PcQRLoginPollResponse(BaseModel):
    status: Literal['waiting_scan', 'waiting_confirm', 'expired', 'failed']
    message: str
    login_id: str


class PcPhoneLoginPendingResponse(BaseModel):
    status: Literal['waiting_code']
    message: str
    login_id: str
    expires_in_seconds: int


class PcAPIResponse(BaseModel):
    success: bool
    message: str
    result: Any
