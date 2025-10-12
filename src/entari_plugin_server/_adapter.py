from typing import cast

from arclet.entari import Entari
from launart import Launart, any_completed
from launart.status import Phase
from starlette.datastructures import FormData
from starlette.responses import JSONResponse, Response

from satori import Api
from satori.exception import ActionFailed
from satori.server import Adapter as BaseAdapter
from satori.server import Request
from satori.server.adapter import LoginType


class EntariAdapter(BaseAdapter):
    def __init__(self):
        super().__init__()
        self.routes["internal/*"] = self._handle_request
        self.routes |= {api.value: self._handle_request for api in Api.__members__.values()}

    @property
    def app(self):
        return Entari.current()

    @property
    def id(self):
        return f"entari_plugin_server.transfer"

    def get_account(self, platform: str, self_id: str):
        return next((acc for acc in self.app.accounts.values() if acc.platform == platform and acc.self_id == self_id), None)

    def get_platform(self) -> str:
        return "satori"

    def ensure(self, platform: str, self_id: str) -> bool:
        return self.get_account(platform, self_id) is not None

    async def _handle_request(self, request: Request):
        if not (acc := self.get_account(request.platform, request.self_id)):
            return Response("No account found", status_code=404)
        if request.action == Api.UPLOAD_CREATE.value:
            data = cast(FormData, request.params)
            files = {
                k: (
                    v
                    if isinstance(v, str)
                    else {"value": v.file.read(), "content_type": v.content_type, "filename": v.filename}
                )
                for k, v in data.items()
            }
            return await acc.protocol.call_api(request.action, files, multipart=True)
        return await acc.protocol.call_api(request.action, request.params)

    async def handle_internal(self, request: Request, path: str) -> Response:
        if path.startswith("_api"):
            if not (acc := self.get_account(request.platform, request.self_id)):
                return Response("No account found", status_code=404)
            try:
                return JSONResponse(
                    await acc.protocol.call_api(path[5:], await request.origin.json(), method=request.origin.method)
                )
            except ActionFailed as e:
                return Response(str(e), status_code=500)
        if acc := self.get_account(request.platform, request.self_id):
            return Response(await acc.protocol.download(f"internal:{acc.platform}/{acc.self_id}/{path}"))
        async with self.server.session.get(path) as resp:
            return Response(await resp.read())

    async def get_logins(self) -> list[LoginType]:
        return [acc.self_info for acc in self.app.accounts.values()]

    @property
    def required(self) -> set[str]:
        return {
            "satori-python.server",
        }

    @property
    def stages(self) -> set[Phase]:
        return {"preparing", "blocking", "cleanup"}

    async def launch(self, manager: Launart):
        # manager.add_component(self.app.connections[0])

        async with self.stage("preparing"):
            pass

        async with self.stage("blocking"):
            @self.app.register
            async def _(acc, event):
                await self.server.post(event)

            await any_completed(
                self.app.status.wait_for("blocking-completed"),
                manager.status.wait_for_sigexit(),
            )

        async with self.stage("cleanup"):
            pass
