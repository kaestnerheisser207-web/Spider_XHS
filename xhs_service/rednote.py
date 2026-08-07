from __future__ import annotations

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from apis.rednote_pc_login_apis import RednoteLoginApi

from .models import (
    PcAuthenticatedSessionResponse,
    PcPhoneLoginPendingResponse,
    PhoneLoginRequest,
    PhoneVerifyRequest,
    SessionClosedResponse,
    SessionStatusResponse,
)
from .state import RednoteSessionStore, StateNotFound


def _not_found(kind: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            'code': f'rednote_{kind}_not_found',
            'message': (
                f'Rednote {kind.replace("_", " ")} was not found or expired.'
            ),
        },
    )


def _business_rejection(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={'code': code, 'message': message},
    )


def _upstream_failure(error: Exception) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail={
            'code': 'rednote_pc_request_failed',
            'message': str(error),
        },
    )


def _session_response(
    store: RednoteSessionStore,
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


def create_rednote_router(
    store: RednoteSessionStore,
    require_service_key: Callable,
) -> APIRouter:
    router = APIRouter(
        prefix='/v1/rednote',
        tags=['rednote-pc'],
        dependencies=[Depends(require_service_key)],
    )

    @router.post('/logins/phone', response_model=PcPhoneLoginPendingResponse)
    def start_phone_login(
        request: PhoneLoginRequest,
    ) -> PcPhoneLoginPendingResponse:
        login = RednoteLoginApi(proxies=request.proxies)
        try:
            cookies = login.generate_init_cookies()
            login.ensure_webprofile(cookies)
            success, message, _ = login.send_phone_code(
                request.phone,
                cookies,
                request.zone,
            )
            if not success:
                raise _business_rejection(
                    'rednote_phone_code_rejected',
                    message or 'Rednote SMS code request was rejected.',
                )
            login_id = store.add_login(
                login,
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
        except HTTPException:
            login.close()
            raise
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
            entry = store.get_login(login_id)
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
                    raise _business_rejection(
                        'rednote_phone_code_rejected',
                        message or 'Rednote SMS code was rejected.',
                    )
                cookies = result['cookies']
                accepted, account, cookies = entry.client.get_user_info(cookies)
                if not accepted or account.get('guest') is not False:
                    raise RuntimeError(
                        'Rednote phone login did not produce a user session'
                    )
                entry.cookies = cookies
                session_id = store.complete_login(login_id, cookies, account)
                return _session_response(
                    store,
                    session_id,
                    'Rednote PC phone login authenticated.',
                    account,
                )
        except HTTPException:
            raise
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

    return router
