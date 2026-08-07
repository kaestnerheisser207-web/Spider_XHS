from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status

from apis.xhs_creator_apis import XHS_Creator_Apis
from apis.xhs_creator_login_apis import XHSCreatorLoginApi
from xhs_utils.xhs_creator import XHSCreatorAuth

from .models import (
    AccountInfoRequest,
    AuthenticatedSessionResponse,
    CookieSessionResponse,
    CookieSessionRequest,
    CreatorAPIResponse,
    FileEncryptionRequest,
    LocationSearchRequest,
    MediaPermitRequest,
    MediaUploadRequest,
    PhoneLoginFailedResponse,
    PhoneLoginPendingResponse,
    PhoneLoginRequest,
    PhoneZoneListRequest,
    PhoneZoneListResponse,
    PhoneVerifyRequest,
    PostedNotesAllRequest,
    PostedNotesPageRequest,
    PublishResponse,
    PublishRequest,
    QRLoginPendingResponse,
    QRLoginPollResponse,
    QRLoginRequest,
    SessionClosedResponse,
    SessionStatusResponse,
    TopicSearchRequest,
    VideoTranscodeRequest,
)
from .pc import create_pc_router
from .rednote import create_rednote_router
from .state import (
    PcSessionStore,
    RednoteSessionStore,
    SessionStore,
    StateNotFound,
)


store = SessionStore()
pc_store = PcSessionStore()
rednote_store = RednoteSessionStore()
MINIMUM_SERVICE_KEY_LENGTH = 32


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    store.close()
    pc_store.close()
    rednote_store.close()


app = FastAPI(
    title='Spider_XHS Service',
    version='1.0.0',
    description=(
        'Standalone PC Web data and Creator publishing API backed by '
        'Spider_XHS. '
        'Login and authenticated HTTP state are process-local and expire by TTL.'
    ),
    lifespan=lifespan,
)


def require_service_key(
    authorization: Annotated[Optional[str], Header()] = None,
) -> None:
    expected = os.environ.get('XHS_SERVICE_API_KEY', '').strip()
    if len(expected) < MINIMUM_SERVICE_KEY_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'code': 'service_not_configured',
                'message': (
                    'XHS_SERVICE_API_KEY must contain at least '
                    f'{MINIMUM_SERVICE_KEY_LENGTH} characters.'
                ),
            },
        )
    scheme, separator, supplied = (authorization or '').partition(' ')
    if (
        not separator
        or scheme.lower() != 'bearer'
        or not secrets.compare_digest(supplied, expected)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': 'Invalid service token.'},
            headers={'WWW-Authenticate': 'Bearer'},
        )


ServiceAuth = Annotated[None, Depends(require_service_key)]


def _service_key_configured() -> bool:
    return len(os.environ.get('XHS_SERVICE_API_KEY', '').strip()) >= (
        MINIMUM_SERVICE_KEY_LENGTH
    )


def _not_found(kind: str) -> HTTPException:
    label = kind.replace('_', ' ')
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            'code': f'{kind}_not_found',
            'message': f'{label.title()} was not found or expired.',
        },
    )


def _upstream_failure(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={'code': 'xhs_request_failed', 'message': str(error)},
    )


def _session_response(session_id: str, message: str) -> dict:
    return {
        'status': 'authenticated',
        'message': message,
        'session_id': session_id,
        'expires_in_seconds': store.session_ttl_seconds,
    }


def _request_invalid(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={'code': 'request_invalid', 'message': str(error)},
    )


def _normalize_phone_zones(zones: Any) -> list[dict[str, str]]:
    if not isinstance(zones, list):
        raise ValueError('Creator zone list is not an array')
    normalized = []
    seen = set()
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        name = next(
            (
                str(zone[key]).strip()
                for key in (
                    'name',
                    'country_name',
                    'countryName',
                    'country',
                    'region',
                    'region_name',
                    'regionName',
                    'zone_name',
                    'zoneName',
                )
                if zone.get(key) is not None and str(zone[key]).strip()
            ),
            '',
        )
        code = next(
            (
                str(zone[key]).strip().lstrip('+')
                for key in (
                    'code',
                    'zone',
                    'country_code',
                    'countryCode',
                    'phone_code',
                    'phoneCode',
                    'zone_code',
                    'zoneCode',
                )
                if zone.get(key) is not None and str(zone[key]).strip()
            ),
            '',
        )
        if not name or not code.isdigit() or (name, code) in seen:
            continue
        seen.add((name, code))
        normalized.append({'name': name, 'code': code})
    if not normalized:
        raise ValueError('Creator zone list contains no usable entries')
    return normalized


def _call_creator_api(
    session_id: str,
    proxies: Optional[dict[str, str]],
    method_name: str,
    *args: Any,
    **kwargs: Any,
) -> dict:
    try:
        entry = store.get_session(session_id)
    except StateNotFound as error:
        raise _not_found('session') from error
    try:
        with entry.lock:
            success, message, result = getattr(entry.api, method_name)(
                *args,
                proxies=proxies,
                **kwargs,
            )
        return {'success': success, 'message': message, 'result': result}
    except ValueError as error:
        raise _request_invalid(error) from error
    except Exception as error:
        raise _upstream_failure(error) from error


@app.get('/healthz', include_in_schema=False)
def health() -> dict:
    return {'status': 'ok'}


@app.get('/readyz', include_in_schema=False)
def ready() -> dict:
    if not _service_key_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'code': 'service_not_configured',
                'message': (
                    'XHS_SERVICE_API_KEY must contain at least '
                    f'{MINIMUM_SERVICE_KEY_LENGTH} characters.'
                ),
            },
        )
    return {
        'status': 'ready',
        'service_key_configured': True,
    }


@app.post('/v1/creator/sessions/cookie')
def create_cookie_session(
    request: CookieSessionRequest,
    _: ServiceAuth,
) -> CookieSessionResponse:
    auth = None
    try:
        auth = XHSCreatorAuth.from_cookie(
            request.cookies.get_secret_value(),
            proxies=request.proxies,
        )
        api = XHS_Creator_Apis(auth)
        account = None
        if request.verify_session:
            success, message, result = api.get_user_info(
                proxies=request.proxies,
            )
            if not success:
                raise ValueError(message)
            account = (result or {}).get('data') or {}
        session_id = store.add_session(auth)
        auth = None
        return {
            **_session_response(session_id, 'Creator Cookie accepted.'),
            'account': account,
        }
    except Exception as error:
        if auth is not None:
            auth.close()
        raise _upstream_failure(error) from error


@app.post('/v1/creator/logins/qr')
def start_qr_login(
    request: QRLoginRequest,
    _: ServiceAuth,
) -> AuthenticatedSessionResponse | QRLoginPendingResponse:
    login = XHSCreatorLoginApi(proxies=request.proxies)
    try:
        result = login.start_qrcode_session()
        if result['status'] == 'authenticated':
            session_id = store.complete_login(
                None,
                login,
                result.pop('cookies'),
                'qrcode',
            )
            return _session_response(session_id, result['message'])
        login_id = store.add_login(
            login,
            'qrcode',
            qr_id=result['qr_id'],
        )
        return {
            **result,
            'login_id': login_id,
            'expires_in_seconds': store.login_ttl_seconds,
        }
    except Exception as error:
        login.close()
        raise _upstream_failure(error) from error


@app.get('/v1/creator/logins/qr/{login_id}')
def poll_qr_login(
    login_id: str,
    _: ServiceAuth,
) -> AuthenticatedSessionResponse | QRLoginPollResponse:
    try:
        entry = store.get_login(login_id, 'qrcode')
    except StateNotFound as error:
        raise _not_found('login') from error
    try:
        with entry.lock:
            result = entry.client.poll_qrcode_session(entry.qr_id)
            if result['status'] == 'authenticated':
                session_id = store.complete_login(
                    login_id,
                    entry.client,
                    result.pop('cookies'),
                    'qrcode',
                )
                return _session_response(session_id, result['message'])
            if result['status'] in {'expired', 'failed'}:
                store.discard_login(login_id)
            return {'login_id': login_id, **result}
    except Exception as error:
        raise _upstream_failure(error) from error


@app.post('/v1/creator/logins/phone')
def start_phone_login(
    request: PhoneLoginRequest,
    _: ServiceAuth,
) -> AuthenticatedSessionResponse | PhoneLoginPendingResponse:
    login = XHSCreatorLoginApi(proxies=request.proxies)
    try:
        result = login.start_phone_session(request.phone, request.zone)
        if result['status'] == 'authenticated':
            session_id = store.complete_login(
                None,
                login,
                result.pop('cookies'),
                'phone',
            )
            return _session_response(session_id, result['message'])
        login_id = store.add_login(
            login,
            'phone',
            phone=request.phone,
            zone=request.zone,
        )
        return {
            'status': result['status'],
            'message': result['message'],
            'login_id': login_id,
            'expires_in_seconds': store.login_ttl_seconds,
        }
    except Exception as error:
        login.close()
        raise _upstream_failure(error) from error


@app.post(
    '/v1/creator/logins/phone/zones',
    response_model=PhoneZoneListResponse,
)
def list_phone_zones(
    request: PhoneZoneListRequest,
    _: ServiceAuth,
) -> PhoneZoneListResponse:
    """Return the current Creator SMS country and region calling-code list."""
    login = XHSCreatorLoginApi(proxies=request.proxies)
    try:
        success, zones, _ = login.get_zone_list()
        if not success:
            raise RuntimeError('Creator zone request was not accepted')
        return {
            'items': _normalize_phone_zones(zones),
            'default_code': '86',
        }
    except Exception as error:
        raise _upstream_failure(error) from error
    finally:
        login.close()


@app.post('/v1/creator/logins/phone/{login_id}/verify')
def verify_phone_login(
    login_id: str,
    request: PhoneVerifyRequest,
    _: ServiceAuth,
) -> AuthenticatedSessionResponse | PhoneLoginFailedResponse:
    try:
        entry = store.get_login(login_id, 'phone')
    except StateNotFound as error:
        raise _not_found('login') from error
    try:
        with entry.lock:
            result = entry.client.complete_phone_session(
                entry.phone,
                request.code.get_secret_value(),
                entry.zone,
            )
            if result['status'] != 'authenticated':
                return {'login_id': login_id, **result}
            session_id = store.complete_login(
                login_id,
                entry.client,
                result.pop('cookies'),
                'phone',
            )
            return _session_response(session_id, result['message'])
    except Exception as error:
        raise _upstream_failure(error) from error


@app.get('/v1/creator/sessions/{session_id}')
def inspect_session(session_id: str, _: ServiceAuth) -> SessionStatusResponse:
    try:
        store.get_session(session_id)
    except StateNotFound as error:
        raise _not_found('session') from error
    return {
        'status': 'authenticated',
        'session_id': session_id,
        'expires_in_seconds': store.session_ttl_seconds,
    }


@app.delete('/v1/creator/sessions/{session_id}')
def delete_session(session_id: str, _: ServiceAuth) -> SessionClosedResponse:
    if not store.discard_session(session_id):
        raise _not_found('session')
    return {'status': 'closed'}


@app.post('/v1/creator/account', response_model=CreatorAPIResponse)
def get_account_info(
    request: AccountInfoRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Return the account bound to an authenticated Creator session."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'get_user_info',
    )


@app.post('/v1/creator/topics/search', response_model=CreatorAPIResponse)
def search_topics(
    request: TopicSearchRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Search Creator topics by keyword."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'get_topic',
        request.keyword,
    )


@app.post('/v1/creator/locations/search', response_model=CreatorAPIResponse)
def search_locations(
    request: LocationSearchRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Search Creator publishing locations by keyword."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'get_location_info',
        request.keyword,
    )


@app.post('/v1/creator/media/permit', response_model=CreatorAPIResponse)
def get_media_permit(
    request: MediaPermitRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Obtain the upstream upload permit for an image or video."""
    response = _call_creator_api(
        request.session_id,
        request.proxies,
        'get_file_ids',
        request.media_type,
    )
    permit, x_t = response['result']
    response['result'] = {'permit': permit, 'x_t': x_t}
    return response


@app.post('/v1/creator/media/upload', response_model=CreatorAPIResponse)
def upload_media(
    request: MediaUploadRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Upload one image or video and return its Creator media handle."""
    try:
        media = request.media.decode()
    except ValueError as error:
        raise _request_invalid(error) from error
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'upload_media',
        media,
        request.media_type,
    )


@app.post('/v1/creator/videos/transcode', response_model=CreatorAPIResponse)
def query_video_transcode(
    request: VideoTranscodeRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Query video transcode state; upstream may require a PC web_session."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'query_transcode',
        request.video_id,
    )


@app.post('/v1/creator/files/encryption', response_model=CreatorAPIResponse)
def get_file_encryption(
    request: FileEncryptionRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Return upstream Creator encryption information for an image file id."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'encryption',
        request.file_id,
    )


@app.post('/v1/creator/posts/posted/page', response_model=CreatorAPIResponse)
def get_posted_notes_page(
    request: PostedNotesPageRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Return one cursor page from the Creator published-posts manager."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'get_posted_notes_page',
        page=request.page,
        tab=request.tab,
    )


@app.post('/v1/creator/posts/posted/all', response_model=CreatorAPIResponse)
def get_all_posted_notes(
    request: PostedNotesAllRequest,
    _: ServiceAuth,
) -> CreatorAPIResponse:
    """Follow Creator cursors and return all published posts."""
    return _call_creator_api(
        request.session_id,
        request.proxies,
        'get_all_posted_notes',
        tab=request.tab,
    )


@app.post('/v1/creator/posts')
def publish_post(request: PublishRequest, _: ServiceAuth) -> PublishResponse:
    try:
        entry = store.get_session(request.session_id)
    except StateNotFound as error:
        raise _not_found('session') from error
    try:
        note = {
            'title': request.title,
            'desc': request.description,
            'postTime': request.scheduled_at_ms,
            'location': request.location,
            'type': request.privacy_type,
            'media_type': request.media_type,
            'topics': request.topics,
        }
        if request.media_type == 'image':
            note['images'] = [item.decode() for item in request.images]
        else:
            if request.video is None:
                raise ValueError('video is required for a video post')
            note['video'] = request.video.decode()
        with entry.lock:
            success, message, result = entry.api.post_note(
                note,
                proxies=request.proxies,
            )
        return {'success': success, 'message': message, 'result': result}
    except ValueError as error:
        raise _request_invalid(error) from error
    except Exception as error:
        raise _upstream_failure(error) from error


app.include_router(create_pc_router(pc_store, require_service_key))
app.include_router(create_rednote_router(rednote_store, require_service_key))
