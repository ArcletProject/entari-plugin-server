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

- `direct_adapter`: 是否使用直连适配器。
    直连适配器的情况下，App 将直接与 Server 插件通信，而不通过网络请求。
    也就是说，不再需要填写基础配置项 `network`
- `transfer_client`: 是否将 Entari 客户端收到的事件转发给连接到 server 的其他 Satori 客户端。
    开启转发的情况下，Server 插件将作为一个中继，转发事件给所有连接的客户端。
    并且客户端的响应调用，Server 插件也将一并转发回上游。
- `adapters`: 适配器配置列表。
    每个适配器配置项均为一个字典，必须包含 `$path` 键，表示适配器的路径。
    其他键值对将作为适配器的配置项传递给适配器类的构造函数。
    已知适配器请参考下方的官方适配器和社区适配器部分。
- `host`: 服务器主机地址，默认为 `127.0.0.1`
- `port`: 服务器端口，默认为 `5140`
- `path`: 服务器部署路径，默认为空字符串 `""`
- `version`: 服务器使用的协议版本，默认为 `v1`
- `token`: 服务器访问令牌，如果为 `None` 则不启用令牌验证，默认为 `None`
- `options`: Uvicorn 的其他配置项，默认为 `None`。此处参考 [Uvicorn 配置项](https://www.uvicorn.org/settings/)
- `stream_threshold`: 流式传输阈值，超过此大小将使用流式传输，默认为 `16 * 1024 * 1024` (16MB)
- `stream_chunk_size`: 流式传输分块大小，流式传输时每次发送的数据大小，默认为 `64 * 1024` (64KB)

## 官方适配器

### Satori适配器

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

### OneBot V11适配器

**安装**：
```bash
pip install satori-python-adapter-onebot11
```

**路径(`$path`)**： `@onebot11.forward` 或 `@onebot11.reverse` (正向或反向适配器)

**配置(正向)**：
- `endpoint`: 连接 OneBot V11协议端的路径
- `access_token`: OneBot V11协议的访问令牌, 默认为空

**配置(反向)**：
- `prefix`: 反向适配器于 Server 的路径前缀, 默认为 `/`
- `path`: 反向适配器于 Server 的路径, 默认为 `onebot/v11`
- `endpoint`: 反向适配器于 Server 的路径端点, 默认为 `ws` (完整路径即为 `/onebot/v11/ws`)
- `access_token`: 反向适配器的访问令牌, 默认为空

### Console适配器

**安装**：
```bash
pip install satori-python-adapter-console
```

**路径(`$path`)**： `@console`

**配置**：参考 [`ConsoleSetting`](https://github.com/nonebot/nonechat/blob/main/nonechat/setting.py)


## 社区适配器

### Lagrange适配器

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
