from io import BytesIO

from arclet.entari import Entari
from arclet.entari.logger import log
from arclet.entari.session import EntariProtocol
from arclet.letoderea.utils import add_task
from satori import Api, Event
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
        login_sn = f"{event.login.platform}_{event.login.user.id}@{id(self):x}"
        if login_sn not in app.accounts:
            acc = Account(
                event.login,
                ApiInfo(self.host, self.port, self.path, self.token),  # type: ignore
                proxy_urls,
                DirectAdapterProtocol
            )
            acc.protocol.server = self
            app.accounts[login_sn] = acc
            logger.debug(f"account added: {acc}")
        else:
            acc = app.accounts[login_sn].custom(protocol_cls=DirectAdapterProtocol)
            acc.protocol.server = self
        add_task(app.handle_event(acc, event))
