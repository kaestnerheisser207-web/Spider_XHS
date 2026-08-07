from __future__ import annotations

import os
import secrets
import threading
import time
from dataclasses import dataclass, field
from typing import Literal, Optional

from apis.xhs_creator_apis import XHS_Creator_Apis
from apis.xhs_creator_login_apis import XHSCreatorLoginApi
from apis.xhs_pc_apis import XHS_Apis
from apis.xhs_pc_login_apis import XHSLoginApi
from apis.rednote_pc_login_apis import RednoteLoginApi
from xhs_utils.xhs_creator import XHSCreatorAuth
from xhs_utils.xhs_pc import XHSPcAuth


LoginMode = Literal['qrcode', 'phone']


def _positive_seconds(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as error:
        raise RuntimeError(f'{name} must be a positive integer') from error
    if value <= 0:
        raise RuntimeError(f'{name} must be a positive integer')
    return value


@dataclass
class LoginEntry:
    client: XHSCreatorLoginApi
    mode: LoginMode
    expires_at: float
    qr_id: str = ''
    phone: str = ''
    zone: str = '86'
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class SessionEntry:
    auth: XHSCreatorAuth
    api: XHS_Creator_Apis
    expires_at: float
    lock: threading.Lock = field(default_factory=threading.Lock)


class StateNotFound(KeyError):
    pass


class SessionStore:
    """Own mutable XHS login and authenticated state in one service process."""

    def __init__(
        self,
        *,
        login_ttl_seconds: Optional[int] = None,
        session_ttl_seconds: Optional[int] = None,
    ) -> None:
        self.login_ttl_seconds = login_ttl_seconds or _positive_seconds(
            'XHS_LOGIN_TTL_SECONDS', 600
        )
        self.session_ttl_seconds = session_ttl_seconds or _positive_seconds(
            'XHS_SESSION_TTL_SECONDS', 86400
        )
        self._logins: dict[str, LoginEntry] = {}
        self._sessions: dict[str, SessionEntry] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _identifier(prefix: str) -> str:
        return f'{prefix}_{secrets.token_urlsafe(24)}'

    def cleanup(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired_logins = [
                self._logins.pop(key)
                for key, value in list(self._logins.items())
                if value.expires_at <= now
            ]
            expired_sessions = [
                self._sessions.pop(key)
                for key, value in list(self._sessions.items())
                if value.expires_at <= now
            ]
        for entry in expired_logins:
            entry.client.close()
        for entry in expired_sessions:
            entry.auth.close()

    def add_login(
        self,
        client: XHSCreatorLoginApi,
        mode: LoginMode,
        *,
        qr_id: str = '',
        phone: str = '',
        zone: str = '86',
    ) -> str:
        self.cleanup()
        login_id = self._identifier('login')
        with self._lock:
            self._logins[login_id] = LoginEntry(
                client=client,
                mode=mode,
                qr_id=qr_id,
                phone=phone,
                zone=zone,
                expires_at=time.monotonic() + self.login_ttl_seconds,
            )
        return login_id

    def get_login(self, login_id: str, mode: LoginMode) -> LoginEntry:
        self.cleanup()
        with self._lock:
            entry = self._logins.get(login_id)
            if entry is None or entry.mode != mode:
                raise StateNotFound(login_id)
            entry.expires_at = time.monotonic() + self.login_ttl_seconds
            return entry

    def discard_login(self, login_id: str) -> None:
        with self._lock:
            entry = self._logins.pop(login_id, None)
        if entry is not None:
            entry.client.close()

    def add_session(self, auth: XHSCreatorAuth) -> str:
        self.cleanup()
        session_id = self._identifier('session')
        with self._lock:
            self._sessions[session_id] = SessionEntry(
                auth=auth,
                api=XHS_Creator_Apis(auth),
                expires_at=time.monotonic() + self.session_ttl_seconds,
            )
        return session_id

    def complete_login(
        self,
        login_id: Optional[str],
        client: XHSCreatorLoginApi,
        cookies: str,
        source: LoginMode,
    ) -> str:
        auth = XHSCreatorAuth.from_completed_login(
            client,
            cookies,
            login_source=source,
        )
        session_id = self.add_session(auth)
        if login_id is not None:
            with self._lock:
                self._logins.pop(login_id, None)
        return session_id

    def get_session(self, session_id: str) -> SessionEntry:
        self.cleanup()
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                raise StateNotFound(session_id)
            entry.expires_at = time.monotonic() + self.session_ttl_seconds
            return entry

    def discard_session(self, session_id: str) -> bool:
        with self._lock:
            entry = self._sessions.pop(session_id, None)
        if entry is None:
            return False
        entry.auth.close()
        return True

    def close(self) -> None:
        with self._lock:
            logins = list(self._logins.values())
            sessions = list(self._sessions.values())
            self._logins.clear()
            self._sessions.clear()
        for entry in logins:
            entry.client.close()
        for entry in sessions:
            entry.auth.close()


@dataclass
class PcLoginEntry:
    client: XHSLoginApi
    mode: LoginMode
    cookies: dict
    expires_at: float
    qr_id: str = ''
    qr_code: str = ''
    phone: str = ''
    zone: str = '86'
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class PcSessionEntry:
    auth: XHSPcAuth
    api: XHS_Apis
    expires_at: float
    lock: threading.Lock = field(default_factory=threading.Lock)


class PcSessionStore:
    """Own PC Web login and authenticated state beside Creator state."""

    def __init__(
        self,
        *,
        login_ttl_seconds: Optional[int] = None,
        session_ttl_seconds: Optional[int] = None,
    ) -> None:
        self.login_ttl_seconds = login_ttl_seconds or _positive_seconds(
            'XHS_LOGIN_TTL_SECONDS', 600
        )
        self.session_ttl_seconds = session_ttl_seconds or _positive_seconds(
            'XHS_SESSION_TTL_SECONDS', 86400
        )
        self._logins: dict[str, PcLoginEntry] = {}
        self._sessions: dict[str, PcSessionEntry] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _identifier(prefix: str) -> str:
        return f'{prefix}_{secrets.token_urlsafe(24)}'

    def cleanup(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired_logins = [
                self._logins.pop(key)
                for key, value in list(self._logins.items())
                if value.expires_at <= now
            ]
            expired_sessions = [
                self._sessions.pop(key)
                for key, value in list(self._sessions.items())
                if value.expires_at <= now
            ]
        for entry in expired_logins:
            entry.client.close()
        for entry in expired_sessions:
            entry.auth.close()

    def add_login(
        self,
        client: XHSLoginApi,
        mode: LoginMode,
        cookies: dict,
        *,
        qr_id: str = '',
        qr_code: str = '',
        phone: str = '',
        zone: str = '86',
    ) -> str:
        self.cleanup()
        login_id = self._identifier('pc_login')
        with self._lock:
            self._logins[login_id] = PcLoginEntry(
                client=client,
                mode=mode,
                cookies=cookies,
                qr_id=qr_id,
                qr_code=qr_code,
                phone=phone,
                zone=zone,
                expires_at=time.monotonic() + self.login_ttl_seconds,
            )
        return login_id

    def get_login(self, login_id: str, mode: LoginMode) -> PcLoginEntry:
        self.cleanup()
        with self._lock:
            entry = self._logins.get(login_id)
            if entry is None or entry.mode != mode:
                raise StateNotFound(login_id)
            entry.expires_at = time.monotonic() + self.login_ttl_seconds
            return entry

    def discard_login(self, login_id: str) -> None:
        with self._lock:
            entry = self._logins.pop(login_id, None)
        if entry is not None:
            entry.client.close()

    def add_session(self, auth: XHSPcAuth) -> str:
        self.cleanup()
        session_id = self._identifier('pc_session')
        with self._lock:
            self._sessions[session_id] = PcSessionEntry(
                auth=auth,
                api=XHS_Apis(auth),
                expires_at=time.monotonic() + self.session_ttl_seconds,
            )
        return session_id

    def complete_login(
        self,
        login_id: str,
        cookies: dict,
        source: LoginMode,
        account: dict,
    ) -> str:
        entry = self.get_login(login_id, source)
        auth = XHSPcAuth.from_completed_login(
            entry.client,
            XHSLoginApi.cookies_to_str(cookies),
            login_source=source,
        )
        user_id = str(
            account.get('user_id')
            or account.get('userid')
            or account.get('id')
            or ''
        )
        if user_id:
            auth.set_user_id(user_id)
        session_id = self.add_session(auth)
        with self._lock:
            self._logins.pop(login_id, None)
        return session_id

    def get_session(self, session_id: str) -> PcSessionEntry:
        self.cleanup()
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                raise StateNotFound(session_id)
            entry.expires_at = time.monotonic() + self.session_ttl_seconds
            return entry

    def discard_session(self, session_id: str) -> bool:
        with self._lock:
            entry = self._sessions.pop(session_id, None)
        if entry is None:
            return False
        entry.auth.close()
        return True

    def close(self) -> None:
        with self._lock:
            logins = list(self._logins.values())
            sessions = list(self._sessions.values())
            self._logins.clear()
            self._sessions.clear()
        for entry in logins:
            entry.client.close()
        for entry in sessions:
            entry.auth.close()


@dataclass
class RednoteLoginEntry:
    client: RednoteLoginApi
    cookies: dict
    phone: str
    zone: str
    expires_at: float
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class RednoteSessionEntry:
    client: RednoteLoginApi
    cookies: dict
    account: dict
    expires_at: float
    lock: threading.Lock = field(default_factory=threading.Lock)


class RednoteSessionStore:
    """Own Rednote phone-login state without sharing Xiaohongshu PC state."""

    def __init__(
        self,
        *,
        login_ttl_seconds: Optional[int] = None,
        session_ttl_seconds: Optional[int] = None,
    ) -> None:
        self.login_ttl_seconds = login_ttl_seconds or _positive_seconds(
            'XHS_LOGIN_TTL_SECONDS', 600
        )
        self.session_ttl_seconds = session_ttl_seconds or _positive_seconds(
            'XHS_SESSION_TTL_SECONDS', 86400
        )
        self._logins: dict[str, RednoteLoginEntry] = {}
        self._sessions: dict[str, RednoteSessionEntry] = {}
        self._lock = threading.RLock()

    @staticmethod
    def _identifier(prefix: str) -> str:
        return f'{prefix}_{secrets.token_urlsafe(24)}'

    def cleanup(self) -> None:
        now = time.monotonic()
        with self._lock:
            expired_logins = [
                self._logins.pop(key)
                for key, value in list(self._logins.items())
                if value.expires_at <= now
            ]
            expired_sessions = [
                self._sessions.pop(key)
                for key, value in list(self._sessions.items())
                if value.expires_at <= now
            ]
        for entry in expired_logins:
            entry.client.close()
        for entry in expired_sessions:
            entry.client.close()

    def add_login(
        self,
        client: RednoteLoginApi,
        cookies: dict,
        *,
        phone: str,
        zone: str = '86',
    ) -> str:
        self.cleanup()
        login_id = self._identifier('rednote_login')
        with self._lock:
            self._logins[login_id] = RednoteLoginEntry(
                client=client,
                cookies=cookies,
                phone=phone,
                zone=zone,
                expires_at=time.monotonic() + self.login_ttl_seconds,
            )
        return login_id

    def get_login(self, login_id: str) -> RednoteLoginEntry:
        self.cleanup()
        with self._lock:
            entry = self._logins.get(login_id)
            if entry is None:
                raise StateNotFound(login_id)
            entry.expires_at = time.monotonic() + self.login_ttl_seconds
            return entry

    def discard_login(self, login_id: str) -> None:
        with self._lock:
            entry = self._logins.pop(login_id, None)
        if entry is not None:
            entry.client.close()

    def complete_login(
        self,
        login_id: str,
        cookies: dict,
        account: dict,
    ) -> str:
        entry = self.get_login(login_id)
        session_id = self._identifier('rednote_session')
        with self._lock:
            self._sessions[session_id] = RednoteSessionEntry(
                client=entry.client,
                cookies=dict(cookies),
                account=dict(account),
                expires_at=time.monotonic() + self.session_ttl_seconds,
            )
            self._logins.pop(login_id, None)
        return session_id

    def get_session(self, session_id: str) -> RednoteSessionEntry:
        self.cleanup()
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None:
                raise StateNotFound(session_id)
            entry.expires_at = time.monotonic() + self.session_ttl_seconds
            return entry

    def discard_session(self, session_id: str) -> bool:
        with self._lock:
            entry = self._sessions.pop(session_id, None)
        if entry is None:
            return False
        entry.client.close()
        return True

    def close(self) -> None:
        with self._lock:
            entries = [*self._logins.values(), *self._sessions.values()]
            self._logins.clear()
            self._sessions.clear()
        for entry in entries:
            entry.client.close()
