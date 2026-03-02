# entari-plugin-server
为 Entari 提供 Satori 服务器支持，基于此为 Entari 提供 ASGI 服务、适配器连接等功能

## 示例

```yaml
plugins:
  server:
    adapters:
      - $path: package.module:AdapterClass
        # Following are adapter's configuration
        key1: value1
        key2: value2
    host: 127.0.0.1
    port: 5140
```

或者

```yaml
adapters:
  - $path: package.module:AdapterClass
    # Following are adapter's configuration
    key1: value1
    key2: value2
plugins:
  server:
    host: 127.0.0.1
    port: 5140
```

## 插件配置项
- `adapters`: 适配器配置列表。
    每个适配器配置项均为一个字典，必须包含 `$path` 键，表示适配器的路径。
    其他键值对将作为适配器的配置项传递给适配器类的构造函数。
    已知适配器请参考下方的官方适配器和社区适配器部分。
- `direct_adapter`: 是否使用直连适配器。
    直连适配器的情况下，App 将直接与 Server 插件通信，而不通过网络请求。
    也就是说，不再需要填写基础配置项 `network`
- `transfer_client`: 是否将 Entari 客户端收到的事件转发给连接到 server 的其他 Satori 客户端。
    开启转发的情况下，Server 插件将作为一个中继，转发事件给所有连接的客户端。
    并且客户端的响应调用，Server 插件也将一并转发回上游。
- `host`: 服务器主机地址，默认为 `127.0.0.1`
- `port`: 服务器端口，默认为 `5140`
- `path`: 服务器部署路径，默认为空字符串 `""`
- `version`: 服务器使用的协议版本，默认为 `v1`
- `token`: 服务器 Satori 接口的访问令牌，如果为 `None` 则不启用令牌验证，默认为 `None`
- `options`: Uvicorn 的其他配置项，默认为 `None`。此处参考 [Uvicorn 配置项](https://www.uvicorn.org/settings/)
- `stream_threshold`: 流式传输阈值，超过此大小将使用流式传输，默认为 `16 * 1024 * 1024` (16MB)
- `stream_chunk_size`: 流式传输分块大小，流式传输时每次发送的数据大小，默认为 `64 * 1024` (64KB)

## 官方适配器

### Satori 适配器

**安装**：
```bash
pip install satori-python-adapter-satori
```

**路径(`$path`)**： `@satori`

**配置**：
- `host`: 对接的 Satori Server 的地址，默认为`localhost`
- `port`: 对接的 Satori Server 的端口，默认为`5140`
- `path`: 对接的 Satori Server 的路径，默认为`""`
- `token`: 对接的 Satori Server 的访问令牌，默认为空
- `post_update`: 是否接管资源上传接口，默认为`False`

### OneBot-V11 适配器

**安装**：
```bash
pip install satori-python-adapter-onebot11
```

**路径(`$path`)**： `@onebot11.forward` 或 `@onebot11.reverse` (正向或反向适配器)

**配置(正向)**：
- `endpoint`: 连接 OneBot V11协议端的路径
- `access_token`: OneBot V11协议的访问令牌, 默认为空
- `timeout`: 发送请求的超时时间，默认为 30 秒

**配置(反向)**：
- `prefix`: 反向适配器于 Server 的路径前缀, 默认为 `/`
- `path`: 反向适配器于 Server 的路径, 默认为 `onebot/v11`
- `endpoint`: 反向适配器于 Server 的路径端点, 默认为 `ws` (完整路径即为 `/onebot/v11/ws`)
- `access_token`: 反向适配器的访问令牌, 默认为空
- `timeout`: 发送请求的超时时间，默认为 30 秒

### Console 适配器

**安装**：
```bash
pip install satori-python-adapter-console
```

**路径(`$path`)**： `@console`

**配置**：参考 [`ConsoleSetting`](https://github.com/nonebot/nonechat/blob/main/nonechat/setting.py)


### Milky 适配器

**安装**：
```bash
pip install satori-python-adapter-milky
```

**路径(`$path`)**： `@milky.main`, `@milky.webhook` 或 `@milky.sse` (websocket, webhook 或 sse 适配器)

**配置(Websocket)**：
- `endpoint`: 连接 Milky 协议端的路径
- `token`: Milky 协议的访问令牌, 默认为空
- `token_in_query`: 是否将 token 放在查询参数中, 默认为`False`
- `headers`: 连接时使用的自定义请求头, 默认为空字典

**配置(SSE)**：
- `endpoint`: 连接 Milky 协议端的路径
- `token`: Milky 协议的访问令牌, 默认为空
- `token_in_query`: 是否将 token 放在查询参数中, 默认为`False`
- `headers`: 连接时使用的自定义请求头, 默认为空字典

**配置(Webhook)**：
- `endpoint`: 连接 Milky 协议端的路径 (用于发送请求)
- `token`: Milky 协议的访问令牌, 默认为空
- `headers`: 连接时使用的自定义请求头, 默认为空字典
- `path`: Webhook 适配器于 Server 的路径, 默认为 `/milky`
- `self_token`: Webhook 适配器的访问令牌, 默认为空


### QQ 适配器

**安装**：
```bash
pip install satori-python-adapter-qq
```

**路径(`$path`)**： `@qq.main` 或 `@qq.websocket` (webhook 适配器或 websocket 适配器)

**配置(Webhook)**：
- `secrets`: QQ 机器人的 app_id 和 app_secret 的映射字典，格式为 `{app_id: app_secret}`
- `path`: Webhook 适配器于 Server 的路径, 默认为 `/qqbot`
- `certfile`: SSL 证书文件路径，默认为空 (等同于设置本插件的配置项 `options` 中的 `ssl_certfile`)
- `keyfile`: SSL 密钥文件路径，默认为空 (等同于设置本插件的配置项 `options` 中的 `ssl_keyfile`)
- `verify_payload`: 是否验证请求负载的签名，默认为`True`
- `is_sandbox`: 是否连接到 QQ 机器人的沙箱环境，默认为`False`

**配置(Websocket)**：
- `app_id`: QQ 机器人的应用 ID
- `secret`: QQ 机器人的应用密钥
- `token`: 连接 QQ 机器人的访问令牌
- `shard`: 分片信息，格式为 `(shard_id, shard_count)`，默认为空
- `intent`: 该 QQ 机器人的事件订阅掩码，具体请参考 [QQ 机器人文档](https://bot.q.qq.com/wiki/develop/api-v2/dev-prepare/interface-framework/event-emit.html#%E4%BA%8B%E4%BB%B6%E8%AE%A2%E9%98%85intents):
  - `guilds`: 频道和子频道相关事件，默认开启
  - `guild_members`: 频道成员相关事件，默认开启
  - `guild_messages`: 私域机器人下的频道消息事件，默认**关闭**
  - `guild_message_reactions`: 频道消息表态事件，默认**开启**
  - `direct_message`: 频道私信事件，默认**关闭**
  - `c2c_group_at_messages`: 单聊和群聊事件 (单聊消息、群 @ 消息等)，默认**关闭**
  - `interaction`: 按钮互动事件，默认**关闭**
  - `message_audit`: 频道消息审核事件，默认**开启**
  - `forum_event`: 论坛频道相关事件，仅 *私域* 机器人能够设置此 intents，默认**关闭**
  - `audio_action`: 语音频道相关事件，默认**关闭**
  - `at_messages`: 公域机器人下的频道消息事件，默认**开启**
- `is_sandbox`: 是否连接到 QQ 机器人的沙箱环境，默认为`False`

## 社区适配器

### Lagrange 适配器

**安装**：
```bash
pip install nekobox
```

**路径(`$path`)**： `nekobox.main`

**配置**：
- `uin`: 登录的QQ号
- `sign_url`: 签名服务器的URL
- `protocol`: 使用的协议类型，默认为`linux`，可选值为 `linux`，`macos`, `windows`, `remote`
- `log_level`: 日志级别，默认为`INFO`
- `use_png`: 登录二维码是否保存为PNG图片，默认为`False`
