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
