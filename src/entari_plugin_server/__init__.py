from satori.server import Server, Adapter
from functools import reduce
from importlib import import_module
import re

from arclet.entari import plugin
from arclet.entari.logger import log
from arclet.entari.config import BasicConfModel, field


class Config(BasicConfModel):
    use_direct_adapter: bool = False
    """是否使用直连适配器"""
    adapters: list[dict] = field(default_factory=list)
    host: str = "127.0.0.1"
    port: int = 5140
    path: str = "satori"
    version: str = "v1"
    token: str | None = None
    stream_threshold: int = 16 * 1024 * 1024
    stream_chunk_size: int = 64 * 1024


conf = plugin.get_config(Config)
logger = log.wrapper("[Server]")
server = Server(
    conf.host,
    conf.port,
    conf.path,
    conf.version,
    conf.token,
    stream_threshold=conf.stream_threshold,
    stream_chunk_size=conf.stream_chunk_size,
)

pattern = re.compile(r"(?P<module>[\w.]+)\s*(:\s*(?P<attr>[\w.]+)\s*)?((?P<extras>\[.*\])\s*)?$")


def _load_adapter(adapter_config: dict):
    if "path" not in adapter_config:
        logger.warning(f"Adapter config missing `path`: {adapter_config}")
        return None
    path = adapter_config["path"]
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
        logger.warning(f"Could not find adapter in {module.__name__}")
        return None
    if isinstance(ext, type) and issubclass(ext, Adapter):
        return ext(**{k: v for k, v in adapter_config.items() if k != "path"})  # type: ignore
    elif isinstance(ext, Adapter):
        return ext
    logger.warning(f"Invalid adapter in {module.__name__}")
    return None


adapters: list[Adapter] = [*filter(None, map(_load_adapter, conf.adapters))]

for adapter in adapters:
    server.apply(adapter)

plugin.add_service(server)
