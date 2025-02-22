# entari-plugin-server
Entari plugin for running Satori Server

## Example Usage

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
