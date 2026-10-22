from io import BytesIO
from typing import TYPE_CHECKING

from arclet.entari import Entari
from arclet.entari.logger import log
from arclet.entari.session import EntariProtocol
from arclet.letoderea.utils import add_task
from satori import Api, Event, EventType, LoginStatus
from satori import event as events
from satori.client import Account, ApiInfo
from satori.exception import (
    ActionFailed,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    MethodNotAllowedException,
    ServerException
)
from satori.server import Server
from satori.utils import decode
from starlette.datastructures import FormData, Headers, UploadFile
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = log.wrapper("[Server]")


class DirectAdapterProtocol(EntariProtocol):
    server: Server

    async def call_api(
        self, action: str | Api, params: dict | None = None, multipart: bool = False, method: str = "POST"
    ):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.account.config.token or ''}",
            "X-Platform": self.account.platform,
            "X-Self-ID": self.account.self_id,
            "Satori-Platform": self.account.platform,
            "Satori-User-ID": self.account.self_id,
        }
        _form = None
        if multipart:
            if params is None:
                raise TypeError("multipart requires params")
            forms = []
            headers.pop("Content-Type")
            for k, v in params.items():
                if isinstance(v, dict):
                    forms.append(
                        (
                            k,
                            UploadFile(
                                BytesIO(v["value"]),
                                filename=v.get("filename"),
                                headers=Headers({"content-type": v["content_type"]})
                            )
                        )
                    )
                else:
                    forms.append((k, v))
            _form = FormData(forms)
        _headers = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]
        req = Request({"type": "http", "method": method, "path_params": {"action": action}, "headers": _headers})
        if _form:
            req._form = _form
        else:
            req._json = params or {}

        resp = await self.server.http_server_handler(req)
        if isinstance(resp, JSONResponse):
            return decode(resp.body)  # type: ignore
        content = resp.body.decode()  # type: ignore
        match resp.status_code:
            case x if 200 <= x < 300:
                return decode(content) if content else {}
            case 400:
                raise BadRequestException(content)
            case 401:
                raise UnauthorizedException(content)
            case 403:
                raise ForbiddenException(content)
            case 404:
                raise NotFoundException(content)
            case 405:
                raise MethodNotAllowedException(content)
            case x if x >= 500:
                raise ServerException(content)
            case _:
                raise ActionFailed(content)


class DirectAdapterServer(Server):
    async def post(self, event: Event):
        app = Entari.current()
        proxy_urls = []
        for provider in self.providers:
            proxy_urls.extend(provider.proxy_urls())
        await super().post(event)
        config = ApiInfo(self.host, self.port, self.path, self.token)
        if event.type == EventType.LOGIN_ADDED:
            if TYPE_CHECKING:
                assert isinstance(event, events.LoginEvent)
            login = event.login
            if not login.user:
                logger.warning(f"Received login-added event without user info: {login}")
                return
            login_sn = login.identifier
            account = Account(
                login,
                config,
                proxy_urls,
                DirectAdapterProtocol,
            )
            account.protocol.server = self
            logger.info(f"account added: {account}")
            (account.connected.set() if login.status == LoginStatus.ONLINE else account.connected.clear())
            app.accounts[login_sn] = account
            await app.account_update(account, login.status)
        elif event.type == EventType.LOGIN_UPDATED:
            if TYPE_CHECKING:
                assert isinstance(event, events.LoginEvent)
            login = event.login
            if not login.user:
                logger.warning(f"Received login-updated event without user info: {login}")
                return
            login_sn = login.identifier
            if login_sn not in app.accounts:
                if login.status != LoginStatus.ONLINE:
                    logger.warning(f"Received event for unknown account: {event}")
                    return
                account = Account(
                    login,
                    config,
                    proxy_urls,
                    DirectAdapterProtocol,
                )
                logger.info(f"account added: {account}")
                account.protocol.server = self
                account.connected.set()
                app.accounts[login_sn] = account
                await app.account_update(account, LoginStatus.ONLINE)
            else:
                account = app.accounts[login_sn].custom(protocol_cls=DirectAdapterProtocol)
                account.protocol.server = self
                account.self_info = login
            logger.info(f"account updated: {account}")
            (
                account.connected.set()
                if login.status in (LoginStatus.ONLINE, LoginStatus.CONNECT)
                else account.connected.clear()
            )
            await app.account_update(account, login.status)
        elif event.type == EventType.LOGIN_REMOVED:
            if TYPE_CHECKING:
                assert isinstance(event, events.LoginEvent)
            login = event.login
            if not login.user:
                logger.warning(f"Received login-removed event without user info: {login}")
                return
            login_sn = login.identifier
            if login_sn not in app.accounts:
                logger.warning(f"Received event for unknown account: {event}")
                return
            account = app.accounts[login_sn].custom(protocol_cls=DirectAdapterProtocol)
            account.protocol.server = self
        else:
            login_sn = event.login.identifier
            if login_sn not in app.accounts:
                logger.warning(f"Received event for unknown account: {event}")
                return
            account = app.accounts[login_sn].custom(protocol_cls=DirectAdapterProtocol)
            account.protocol.server = self
        if app.event_callbacks:
            for callback in app.event_callbacks:
                add_task(callback(account, event))  # type: ignore

        if event.type == EventType.LOGIN_REMOVED:
            logger.info(f"account removed: {account}")
            account.connected.clear()
            await app.account_update(account, LoginStatus.OFFLINE)
            del app.accounts[login_sn]
