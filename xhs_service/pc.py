from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from apis.xhs_pc_apis import XHS_Apis
from apis.xhs_pc_login_apis import PcLoginUpstreamError, XHSLoginApi
from xhs_utils.xhs_pc import XHSPcAuth

from .models import (
    PcAPIResponse,
    PcAccountRequest,
    PcAuthenticatedSessionResponse,
    PcCookieSessionRequest,
    PcCursorRequest,
    PcHomefeedAllRequest,
    PcHomefeedPageRequest,
    PcImageResolveRequest,
    PcInnerCommentPageRequest,
    PcNoteURLRequest,
    PcOuterCommentAllRequest,
    PcOuterCommentPageRequest,
    PcPhoneLoginPendingResponse,
    PcProfileRequest,
    PcQRLoginPendingResponse,
    PcQRLoginPollResponse,
    PcSearchKeywordRequest,
    PcSearchNotesAllRequest,
    PcSearchNotesPageRequest,
    PcSearchUsersAllRequest,
    PcSearchUsersPageRequest,
    PcUserAllRequest,
    PcUserPageRequest,
    PcVideoResolveRequest,
    PhoneLoginRequest,
    PhoneVerifyRequest,
    QRLoginRequest,
    SessionClosedResponse,
    SessionStatusResponse,
)
from .state import PcSessionStore, StateNotFound


def _not_found(kind: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            'code': f'pc_{kind}_not_found',
            'message': f'PC {kind.replace("_", " ")} was not found or expired.',
        },
    )


def _request_invalid(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={'code': 'pc_request_invalid', 'message': str(error)},
    )


def _upstream_failure(error: Exception) -> HTTPException:
    detail = {'code': 'pc_request_failed', 'message': str(error)}
    if isinstance(error, PcLoginUpstreamError):
        detail = {
            'code': error.code,
            'message': str(error),
            'diagnostics': error.diagnostics,
        }
        logger.bind(
            event='pc_login_upstream_failure',
            error_code=error.code,
            **error.diagnostics,
        ).error('PC login upstream request failed: {}', str(error))
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=detail,
    )


def _session_response(
    store: PcSessionStore,
    session_id: str,
    message: str,
    account: dict | None = None,
) -> dict:
    return {
        'status': 'authenticated',
        'message': message,
        'session_id': session_id,
        'expires_in_seconds': store.session_ttl_seconds,
        'account': account,
    }


def _call_pc_api(
    store: PcSessionStore,
    request,
    method_name: str,
    *args,
    **kwargs,
) -> dict:
    try:
        entry = store.get_session(request.session_id)
    except StateNotFound as error:
        raise _not_found('session') from error
    try:
        with entry.lock:
            success, message, result = getattr(entry.api, method_name)(
                *args,
                proxies=request.proxies,
                **kwargs,
            )
        return {'success': success, 'message': message, 'result': result}
    except ValueError as error:
        raise _request_invalid(error) from error
    except Exception as error:
        raise _upstream_failure(error) from error


def _static_pc_api(method_name: str, value: str) -> dict:
    try:
        success, message, result = getattr(XHS_Apis, method_name)(value)
        return {'success': success, 'message': message, 'result': result}
    except ValueError as error:
        raise _request_invalid(error) from error
    except Exception as error:
        raise _upstream_failure(error) from error


def create_pc_router(
    store: PcSessionStore,
    require_service_key: Callable,
) -> APIRouter:
    router = APIRouter(
        prefix='/v1/pc',
        tags=['pc'],
        dependencies=[Depends(require_service_key)],
    )

    @router.post(
        '/sessions/cookie',
        response_model=PcAuthenticatedSessionResponse,
    )
    def create_cookie_session(
        request: PcCookieSessionRequest,
    ) -> PcAuthenticatedSessionResponse:
        auth = None
        try:
            auth = XHSPcAuth.from_cookie(
                request.cookies.get_secret_value(),
                proxies=request.proxies,
            )
            api = XHS_Apis(auth)
            success, message, result = api.get_user_me(proxies=request.proxies)
            if not success:
                raise ValueError(message)
            account = (result or {}).get('data') or {}
            user_id = str(
                account.get('user_id')
                or account.get('userid')
                or account.get('id')
                or ''
            )
            if not user_id:
                raise ValueError('PC account response did not include user_id')
            auth.set_user_id(user_id)
            session_id = store.add_session(auth)
            auth = None
            return _session_response(
                store,
                session_id,
                'PC Cookie accepted.',
                account,
            )
        except ValueError as error:
            raise _request_invalid(error) from error
        except Exception as error:
            raise _upstream_failure(error) from error
        finally:
            if auth is not None:
                auth.close()

    @router.post('/logins/qr', response_model=PcQRLoginPendingResponse)
    def start_qr_login(request: QRLoginRequest) -> PcQRLoginPendingResponse:
        login = XHSLoginApi(proxies=request.proxies)
        try:
            cookies = login.generate_init_cookies()
            success, message, data = login.generate_qrcode(cookies)
            if not success or not data:
                raise RuntimeError(message or 'PC QR code was not created')
            cookies = data['cookies']
            success, message, cookies = login.check_qrcode_status(
                data['qr_id'],
                data['code'],
                cookies,
            )
            if success or message != '请扫描二维码':
                raise RuntimeError(
                    message or 'PC QR code preflight returned an invalid state'
                )
            login.ensure_webprofile(cookies)
            login_id = store.add_login(
                login,
                'qrcode',
                cookies,
                qr_id=data['qr_id'],
                qr_code=data['code'],
            )
            return {
                'status': 'waiting_scan',
                'message': message,
                'login_id': login_id,
                'expires_in_seconds': store.login_ttl_seconds,
                'qr_id': data['qr_id'],
                'qr_url': data['qr_url'],
            }
        except Exception as error:
            login.close()
            raise _upstream_failure(error) from error

    @router.get(
        '/logins/qr/{login_id}',
        response_model=PcAuthenticatedSessionResponse | PcQRLoginPollResponse,
    )
    def poll_qr_login(login_id: str):
        try:
            entry = store.get_login(login_id, 'qrcode')
        except StateNotFound as error:
            raise _not_found('login') from error
        try:
            with entry.lock:
                success, message, cookies = entry.client.check_qrcode_status(
                    entry.qr_id,
                    entry.qr_code,
                    entry.cookies,
                )
                entry.cookies = cookies
                if success:
                    accepted, account, cookies = entry.client.get_user_info(cookies)
                    if not accepted or account.get('guest') is not False:
                        raise RuntimeError('PC QR login did not produce a user session')
                    entry.cookies = cookies
                    session_id = store.complete_login(
                        login_id,
                        cookies,
                        'qrcode',
                        account,
                    )
                    return _session_response(
                        store,
                        session_id,
                        'PC QR login authenticated.',
                        account,
                    )
            states = {
                '请扫描二维码': 'waiting_scan',
                '请确认登录': 'waiting_confirm',
                '二维码已过期': 'expired',
            }
            current = states.get(message, 'failed')
            if current in {'expired', 'failed'}:
                store.discard_login(login_id)
            return {
                'status': current,
                'message': message,
                'login_id': login_id,
            }
        except HTTPException:
            raise
        except Exception as error:
            raise _upstream_failure(error) from error

    @router.post('/logins/phone', response_model=PcPhoneLoginPendingResponse)
    def start_phone_login(
        request: PhoneLoginRequest,
    ) -> PcPhoneLoginPendingResponse:
        login = XHSLoginApi(proxies=request.proxies)
        try:
            cookies = login.generate_init_cookies()
            login.ensure_webprofile(cookies)
            success, message, _ = login.send_phone_code(
                request.phone,
                cookies,
                request.zone,
            )
            if not success:
                raise RuntimeError(message or 'PC SMS code was not sent')
            login_id = store.add_login(
                login,
                'phone',
                cookies,
                phone=request.phone,
                zone=request.zone,
            )
            return {
                'status': 'waiting_code',
                'message': message,
                'login_id': login_id,
                'expires_in_seconds': store.login_ttl_seconds,
            }
        except Exception as error:
            login.close()
            raise _upstream_failure(error) from error

    @router.post(
        '/logins/phone/{login_id}/verify',
        response_model=PcAuthenticatedSessionResponse,
    )
    def verify_phone_login(
        login_id: str,
        request: PhoneVerifyRequest,
    ) -> PcAuthenticatedSessionResponse:
        try:
            entry = store.get_login(login_id, 'phone')
        except StateNotFound as error:
            raise _not_found('login') from error
        try:
            with entry.lock:
                success, message, result = entry.client.login_by_phone(
                    entry.phone,
                    request.code.get_secret_value(),
                    entry.cookies,
                    entry.zone,
                )
                if not success:
                    raise ValueError(message or 'PC SMS code was rejected')
                cookies = result['cookies']
                accepted, account, cookies = entry.client.get_user_info(cookies)
                if not accepted or account.get('guest') is not False:
                    raise RuntimeError('PC phone login did not produce a user session')
                entry.cookies = cookies
                session_id = store.complete_login(
                    login_id,
                    cookies,
                    'phone',
                    account,
                )
                return _session_response(
                    store,
                    session_id,
                    'PC phone login authenticated.',
                    account,
                )
        except ValueError as error:
            raise _request_invalid(error) from error
        except Exception as error:
            raise _upstream_failure(error) from error

    @router.get(
        '/sessions/{session_id}',
        response_model=SessionStatusResponse,
    )
    def inspect_session(session_id: str) -> SessionStatusResponse:
        try:
            store.get_session(session_id)
        except StateNotFound as error:
            raise _not_found('session') from error
        return {
            'status': 'authenticated',
            'session_id': session_id,
            'expires_in_seconds': store.session_ttl_seconds,
        }

    @router.delete(
        '/sessions/{session_id}',
        response_model=SessionClosedResponse,
    )
    def delete_session(session_id: str) -> SessionClosedResponse:
        if not store.discard_session(session_id):
            raise _not_found('session')
        return {'status': 'closed'}

    @router.post('/account', response_model=PcAPIResponse)
    def get_account(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_user_me')

    @router.post('/search/keywords', response_model=PcAPIResponse)
    def search_keywords(request: PcSearchKeywordRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_search_keyword', request.keyword)

    @router.post('/search/notes/page', response_model=PcAPIResponse)
    def search_notes_page(request: PcSearchNotesPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'search_note',
            request.query,
            request.page,
            request.sort_type,
            request.note_type,
            request.note_time,
            request.note_range,
            request.position_distance,
            request.geo,
            request.search_id,
        )

    @router.post('/search/notes/all', response_model=PcAPIResponse)
    def search_notes_all(request: PcSearchNotesAllRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'search_some_note',
            request.query,
            request.limit,
            request.sort_type,
            request.note_type,
            request.note_time,
            request.note_range,
            request.position_distance,
            request.geo,
        )

    @router.post('/search/users/page', response_model=PcAPIResponse)
    def search_users_page(request: PcSearchUsersPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'search_user',
            request.query,
            request.page,
        )

    @router.post('/search/users/all', response_model=PcAPIResponse)
    def search_users_all(request: PcSearchUsersAllRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'search_some_user',
            request.query,
            request.limit,
        )

    @router.post('/notes/detail', response_model=PcAPIResponse)
    def note_detail(request: PcNoteURLRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_note_info', request.url)

    @router.post('/notes/comments/outer/page', response_model=PcAPIResponse)
    def note_comments_page(request: PcOuterCommentPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_note_out_comment',
            request.note_id,
            request.cursor,
            request.xsec_token,
        )

    @router.post('/notes/comments/outer/all', response_model=PcAPIResponse)
    def note_outer_comments_all(
        request: PcOuterCommentAllRequest,
    ) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_note_all_out_comment',
            request.note_id,
            request.xsec_token,
        )

    @router.post('/notes/comments/all', response_model=PcAPIResponse)
    def note_comments_all(request: PcNoteURLRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_note_all_comment', request.url)

    @router.post('/notes/comments/inner/page', response_model=PcAPIResponse)
    def note_inner_comments_page(
        request: PcInnerCommentPageRequest,
    ) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_note_inner_comment',
            request.comment,
            request.cursor,
            request.xsec_token,
        )

    @router.post('/notes/comments/inner/all', response_model=PcAPIResponse)
    def note_inner_comments_all(
        request: PcInnerCommentPageRequest,
    ) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_note_all_inner_comment',
            request.comment,
            request.xsec_token,
        )

    @router.post('/users/profile', response_model=PcAPIResponse)
    def user_profile(request: PcProfileRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_user_info', request.user_id)

    @router.post('/users/posts/page', response_model=PcAPIResponse)
    def user_posts_page(request: PcUserPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_user_note_info',
            request.user_id,
            request.cursor,
            request.xsec_token,
            request.xsec_source,
        )

    @router.post('/users/posts/all', response_model=PcAPIResponse)
    def user_posts_all(request: PcUserAllRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_user_all_notes', request.user_url)

    @router.post('/users/likes/page', response_model=PcAPIResponse)
    def user_likes_page(request: PcUserPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_user_like_note_info',
            request.user_id,
            request.cursor,
            request.xsec_token,
            request.xsec_source,
        )

    @router.post('/users/likes/all', response_model=PcAPIResponse)
    def user_likes_all(request: PcUserAllRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_user_all_like_note_info',
            request.user_url,
        )

    @router.post('/users/collects/page', response_model=PcAPIResponse)
    def user_collects_page(request: PcUserPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_user_collect_note_info',
            request.user_id,
            request.cursor,
            request.xsec_token,
            request.xsec_source,
        )

    @router.post('/users/collects/all', response_model=PcAPIResponse)
    def user_collects_all(request: PcUserAllRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_user_all_collect_note_info',
            request.user_url,
        )

    @router.post('/feed/channels', response_model=PcAPIResponse)
    def feed_channels(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_homefeed_all_channel')

    @router.post('/feed/page', response_model=PcAPIResponse)
    def feed_page(request: PcHomefeedPageRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_homefeed_recommend',
            request.category,
            request.cursor_score,
            request.refresh_type,
            request.note_index,
            num=request.num,
            need_num=request.need_num,
        )

    @router.post('/feed/all', response_model=PcAPIResponse)
    def feed_all(request: PcHomefeedAllRequest) -> PcAPIResponse:
        return _call_pc_api(
            store,
            request,
            'get_homefeed_recommend_by_num',
            request.category,
            request.limit,
        )

    @router.post('/notifications/unread', response_model=PcAPIResponse)
    def notifications_unread(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_unread_message')

    @router.post('/notifications/mentions/page', response_model=PcAPIResponse)
    def notifications_mentions_page(request: PcCursorRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_metions', request.cursor)

    @router.post('/notifications/mentions/all', response_model=PcAPIResponse)
    def notifications_mentions_all(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_all_metions')

    @router.post('/notifications/reactions/page', response_model=PcAPIResponse)
    def notifications_reactions_page(request: PcCursorRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_likesAndcollects', request.cursor)

    @router.post('/notifications/reactions/all', response_model=PcAPIResponse)
    def notifications_reactions_all(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_all_likesAndcollects')

    @router.post('/notifications/follows/page', response_model=PcAPIResponse)
    def notifications_follows_page(request: PcCursorRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_new_connections', request.cursor)

    @router.post('/notifications/follows/all', response_model=PcAPIResponse)
    def notifications_follows_all(request: PcAccountRequest) -> PcAPIResponse:
        return _call_pc_api(store, request, 'get_all_new_connections')

    @router.post('/media/video/resolve', response_model=PcAPIResponse)
    def resolve_video(request: PcVideoResolveRequest) -> PcAPIResponse:
        return _static_pc_api('get_note_no_water_video', request.note_id)

    @router.post('/media/image/resolve', response_model=PcAPIResponse)
    def resolve_image(request: PcImageResolveRequest) -> PcAPIResponse:
        return _static_pc_api('get_note_no_water_img', request.image_url)

    return router
