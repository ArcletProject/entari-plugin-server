from pathlib import Path
from typing import TypedDict, Literal, Any

from arclet.entari.config import BasicConfModel, model_field
from uvicorn.config import HTTPProtocolType, WSProtocolType, LifespanType


class UvicornOptions(TypedDict, total=False):
    uds: str | None
    """Bind to a UNIX domain socket. default: None"""
    fd: int | None
    """Bind to socket from this file descriptor. default: None"""
    loop: Literal["none", "auto", "asyncio", "uvloop"]
    """Event loop factory implementation. default: 'auto'"""
    http: HTTPProtocolType
    """HTTP protocol implementation. default: 'auto'"""
    ws: WSProtocolType
    """WebSocket protocol implementation. default: 'auto'"""
    ws_max_size: int
    """WebSocket max size message in bytes. default: 16 * 1024 * 1024"""
    ws_max_queue: int
    """The maximum length of the WebSocket message queue. default: 32"""
    ws_ping_interval: float | None
    """WebSocket ping interval in seconds. default: 20.0"""
    ws_ping_timeout: float | None
    """WebSocket ping timeout in seconds. default: 20.0"""
    ws_per_message_deflate: bool
    """ WebSocket per-message-deflate compression. default: True"""
    lifespan: LifespanType
    """Lifespan implementation. default: 'auto'"""
    env_file: str | Path | None
    """Environment configuration file. default: None"""
    log_config: dict[str, Any] | str | None
    """Logging configuration file. default: LOGGING_CONFIG"""
    log_level: str | int | None
    """default: None"""
    access_log: bool
    """Enable/Disable access log. default: True"""
    use_colors: bool | None
    """Enable/Disable colorized logging. default: None"""
    # interface: InterfaceType
    # """default: 'auto'"""
    workers: int | None
    """
    Number of worker processes. 
    
    default: the $WEB_CONCURRENCY environment variable if available, or 1.
    """
    proxy_headers: bool
    """
    Enable/Disable X-Forwarded-Proto, X-Forwarded-For to populate url scheme and remote address info. default: True
    """
    server_header: bool
    """Enable/Disable default Server header. default: True"""
    date_header: bool
    """Enable/Disable default Date header. default: True"""
    forwarded_allow_ips: list[str] | str | None
    """
    Comma separated list of IP Addresses, IP Networks, or literals (e.g. UNIX Socket path) to trust with proxy headers.
    
    default: the $FORWARDED_ALLOW_IPS environment variable if available, or '127.0.0.1'.
        The literal '*' means trust everything.
    """
    root_path: str
    """Set the ASGI 'root_path' for applications submounted below a given URL path. default: ''"""
    limit_concurrency: int | None
    """Maximum number of concurrent connections or tasks to allow, before issuing HTTP 503 responses. default: None"""
    limit_max_requests: int | None
    """Maximum number of requests to service before terminating the process. default: None"""
    backlog: int
    """Maximum number of connections to hold in backlog. default: 2048"""
    timeout_keep_alive: int
    """Close Keep-Alive connections if no new data is received within this timeout (in seconds).default: 5"""
    timeout_notify: int
    """default: 30"""
    timeout_graceful_shutdown: int | None
    """Maximum number of seconds to wait for graceful shutdown. default: None"""
    ssl_keyfile: str | Path | None
    """SSL key file. default: None"""
    ssl_certfile: str | Path | None
    """SSL certificate file. default: None"""
    ssl_keyfile_password: str | None
    """SSL keyfile password. default: None"""
    ssl_version: int
    """SSL version to use (see stdlib ssl module's). default: ssl.PROTOCOL_TLS"""
    ssl_cert_reqs: int
    """Whether client certificate is required (see stdlib ssl module's). default: ssl.CERT_NONE"""
    ssl_ca_certs: str | None
    """CA certificates file. default: None"""
    ssl_ciphers: str
    """Ciphers to use (see stdlib ssl module's). default: 'TLSv1'"""
    headers: list[tuple[str, str]] | None
    """Specify custom default HTTP response headers as a Name:Value pair. default: None"""
    h11_max_incomplete_event_size: int | None
    """For h11, the maximum number of bytes to buffer of an incomplete event. default: None"""


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
    options: UvicornOptions | None = None
    """Uvicorn 的其他配置项"""
    stream_threshold: int = 16 * 1024 * 1024
    """流式传输阈值，超过此大小将使用流式传输"""
    stream_chunk_size: int = 64 * 1024
    """流式传输分块大小，流式传输时每次发送的数据大小"""
