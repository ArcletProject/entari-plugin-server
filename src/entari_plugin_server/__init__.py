import re
from functools import reduce
from importlib import import_module
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast
from typing_extensions import TypeAlias

from arclet.entari import plugin
from arclet.entari import logger as log_m
from arclet.entari.config import BasicConfModel, model_field
from arclet.letoderea.typing import TCallable
from graia.amnesia.builtins import asgi
from satori.server import Adapter, Server
from starlette.applications import Starlette
from starlette.types import ASGIApp

from .patch import DirectAdapterServer, logger

DISPOSE: TypeAlias = Callable[[], None]

asgi.LoguruHandler = log_m.LoguruHandler


class Config(BasicConfModel):
    direct_adapter: bool = False
    """是否使用直连适配器"""
    adapters: list[dict] = model_field(default_factory=list)
    """适配器配置列表"""
    host: str = "127.0.0.1"
    """服务器主机地址"""
    port: int = 5140
    """服务器端口"""
    path: str = ""
    """服务器部署路径"""
    version: str = "v1"
    """服务器使用的协议版本"""
    token: str | None = None
    """服务器访问令牌，如果为 None 则不启用令牌验证"""
    stream_threshold: int = 16 * 1024 * 1024
    """流式传输阈值，超过此大小将使用流式传输"""
    stream_chunk_size: int = 64 * 1024
    """流式传输分块大小，流式传输时每次发送的数据大小"""


plugin.declare_static()
plugin.metadata(
    "server",
    [{"name": "RF-Tar-Railt", "email": "rf_tar_railt@qq.com"}],
    "0.3.0",
    description="为 Entari 提供 Satori 服务器支持，基于此为 Entari 提供 ASGI 服务、适配器连接等功能",
    urls={
        "homepage": "https://github.com/ArcletProject/entari-plugin-server",
    },
    config=Config,
)


conf = plugin.get_config(Config)

if conf.direct_adapter:
    server = DirectAdapterServer(conf.host, conf.port, conf.path, conf.version, conf.token, None, conf.stream_threshold, conf.stream_chunk_size)
else:
    server = Server(conf.host, conf.port, conf.path, conf.version, conf.token, None, conf.stream_threshold, conf.stream_chunk_size)
ASGI = asgi.UvicornASGIService(server.host, server.port)


pattern = re.compile(r"(?P<module>[\w.]+)\s*(:\s*(?P<attr>[\w.]+)\s*)?((?P<extras>\[.*\])\s*)?$")


def _load_adapter(adapter_config: dict):
    if "$path" not in adapter_config:
        logger.warning(f"Adapter config missing `$path`: {adapter_config}")
        return None
    path = adapter_config["$path"]
    if path.startswith("@."):
        path = f"satori.adapters{path[1:]}"
    elif path.startswith("@"):
        path = f"satori.adapters.{path[1:]}"
    match = pattern.match(path)
    if not match:
        logger.warning(f"Invalid adapter path: {path}")
        return None
    try:
        module = import_module(match.group("module"))
    except ImportError:
        logger.warning(f"Could not import module {match.group('module')}")
        return None
    try:
        attrs = filter(None, (match.group("attr") or "Adapter").split("."))
        ext = reduce(getattr, attrs, module)
    except AttributeError:
        for attr in module.__dict__.values():
            if isinstance(attr, type) and issubclass(attr, Adapter) and attr is not Adapter:
                ext = attr
                break
        else:
            logger.warning(f"Could not find adapter in {module.__name__}")
            return None
    if isinstance(ext, type) and issubclass(ext, Adapter) and ext is not Adapter:
        return ext(**{k: (log_m.logger_id if v == "$logger_id" else v) for k, v in adapter_config.items() if k != "$path"})  # type: ignore
    elif isinstance(ext, Adapter):
        return ext
    logger.warning(f"Invalid adapter in {module.__name__}")
    return None


adapters: list[Adapter] = [*filter(None, map(_load_adapter, conf.adapters))]

for adapter in adapters:
    logger.debug(f"Applying adapter {adapter}")
    server.apply(adapter)

plugin.add_service(ASGI)
plugin.add_service(server)


def get_asgi() -> Any:
    return server.app


def replace_asgi(app: Union[ASGIApp, asgi.asgitypes.ASGI3Application]) -> DISPOSE:
    """
    替换当前的 ASGI 应用

    Args:
        app (Any): 新的 ASGI 应用
    """
    if server.status.blocking:
        logger.warning("Server is blocking, cannot replace ASGI app")
        return lambda: None

    old_app = server.app
    old_routes = cast(Starlette, old_app).router.routes.copy()
    server.app = app
    server.app.router.routes[:0] = old_routes  # type: ignore

    def remove_subsequence(seq, subseq):
        # 找到子序列的起始索引
        for i in range(len(seq) - len(subseq) + 1):
            if seq[i:i + len(subseq)] == subseq:
                return seq[:i] + seq[i + len(subseq):]
        return seq  # 如果没找到，返回原序列

    def dispose(_old=old_app, _old_routes=old_routes):
        server.app.router.routes = remove_subsequence(  # type: ignore
            cast(Starlette, server.app).router.routes, _old_routes
        )
        server.app = _old

    plugin.collect_disposes(cast(DISPOSE, dispose))
    return cast(DISPOSE, dispose)


def add_route(
    path: str,
    *,
    methods: Optional[list[str]] = None,
    name: Optional[str] = None,
    include_in_schema: bool = True,
    **kwargs: Any,
) -> Callable[[TCallable], TCallable]:
    """注册一个 ASGI 路由

    Args:
        path (str): 路由路径
        methods (list[str], optional): 支持的 HTTP 方法，默认为 None，表示 ["GET"]
        name (str, optional): 路由名称，默认为 None
        include_in_schema (bool, optional): 是否包含在 OpenAPI 文档中，默认为 True
        kwargs (Any): 其他参数，例如 FastAPI 的路由参数
    """

    def wrapper(endpoint: TCallable, /) -> TCallable:
        app = cast(Starlette, server.app)
        fn = getattr(app.router, "add_api_route", app.router.add_route)
        fn(
            path, endpoint, methods=methods, name=name, include_in_schema=include_in_schema, **kwargs
        )
        route = app.router.routes[-1]
        plug = plugin.get_plugin(1)
        plug.collect(lambda: app.router.routes.remove(route))
        return endpoint

    return wrapper


def add_websocket_route(
    path: str,
    *,
    name: Optional[str] = None,
    **kwargs: Any,
) -> Callable[[TCallable], TCallable]:
    """注册一个 ASGI WebSocket 路由

    Args:
        path (str): 路由路径
        name (str, optional): 路由名称，默认为 None
        kwargs (Any): 其他参数，例如 FastAPI 的路由参数
    """

    def wrapper(endpoint: TCallable, /) -> TCallable:
        app = cast(Starlette, server.app)
        fn = getattr(app.router, "add_api_websocket_route", app.router.add_websocket_route)
        fn(
            path, endpoint, name=name, **kwargs
        )
        route = app.router.routes[-1]
        plug = plugin.get_plugin(1)
        plug.collect(lambda: app.router.routes.remove(route))
        return endpoint

    return wrapper


if TYPE_CHECKING:
    from fastapi import FastAPI
    from tarina import init_spec

    @init_spec(FastAPI)
    def replace_fastapi(data: FastAPI) -> DISPOSE:
        ...
else:
    def replace_fastapi(**kwargs):
        try:
            from fastapi import FastAPI
        except ImportError:
            logger.warning("FastAPI is not installed, cannot replace ASGI app with FastAPI")
            return lambda: None
        return replace_asgi(FastAPI(**kwargs))  # type: ignore

__all__ = [
    "ASGI",
    "server",
    "get_asgi",
    "replace_asgi",
    "add_route",
    "add_websocket_route",
    "replace_fastapi",
    "Config",
]
