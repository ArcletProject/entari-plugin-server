import re
from functools import reduce
from importlib import import_module
from typing import Any, Callable, cast
from typing_extensions import TypeAlias

from arclet.entari import plugin
from arclet.entari import logger as log_m
from arclet.entari.config import BasicConfModel, field
from graia.amnesia.builtins import asgi
from satori.server import Adapter, Server

from .patch import DirectAdapterServer, logger

DISPOSE: TypeAlias = Callable[[], None]

asgi.LoguruHandler = log_m.LoguruHandler


class Config(BasicConfModel):
    direct_adapter: bool = False
    """是否使用直连适配器"""
    adapters: list[dict] = field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 5140
    path: str = ""
    version: str = "v1"
    token: str | None = None
    stream_threshold: int = 16 * 1024 * 1024
    stream_chunk_size: int = 64 * 1024


plugin.declare_static()
plugin.metadata(
    "server",
    ["RF-Tar-Railt <rf_tar_railt@qq.com>"],
    "0.2.1",
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
            if isinstance(attr, type) and issubclass(attr, Adapter):
                ext = attr
                break
        else:
            logger.warning(f"Could not find adapter in {module.__name__}")
            return None
    if isinstance(ext, type) and issubclass(ext, Adapter):
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


def replace_asgi(app: asgi.asgitypes.ASGI3Application) -> DISPOSE:
    """
    替换当前的 ASGI 应用

    Args:
        app (Any): 新的 ASGI 应用
    """
    if server.status.blocking:
        logger.warning("Server is blocking, cannot replace ASGI app")
        return lambda: None

    old_app = server.app
    server.app = app

    def dispose(_old=old_app):
        server.app = _old

    plugin.collect_disposes(cast(DISPOSE, dispose))
    return cast(DISPOSE, dispose)
