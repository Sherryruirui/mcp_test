# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的假期余额查询 MCP 服务。

## 工具

- `query_leave_balance`

底层接口：

- `POST /client/abs/account/v1/leaveInfo/listAllLeaveBalance`

## 认证方式

推荐在工具调用参数中显式传入认证信息，不自动读取本地：

- `cookie`：Moka 登录态 Cookie，例如 `key=value; key2=value2`
- `authorization`：如果网关支持 Bearer/内部 Token，可以传完整 Authorization 头值

如果不想每次工具调用都传，也可以用环境变量兜底：

- `MOKA_COOKIE`：Moka 登录态 Cookie，例如 `key=value; key2=value2`
- `MOKA_AUTHORIZATION`：如果网关支持 Bearer/内部 Token，可以传完整 Authorization 头值

其他可选变量：

- `MOKA_HOST`：默认 `core.mokahr.com`

## 百炼 uvx 配置

如果这个包已经发布到可被 `uvx` 安装的位置：

```json
{
  "mcpServers": {
    "moka-leave-balance": {
      "command": "uvx",
      "args": ["moka-leave-balance-mcp"],
      "env": {
        "MOKA_HOST": "core.mokahr.com"
      }
    }
  }
}
```

如果使用 Git 仓库地址：

```json
{
  "mcpServers": {
    "moka-leave-balance": {
      "command": "uvx",
      "args": [
        "moka-leave-balance-mcp@git+https://your.git.host/moka-leave-balance-mcp.git"
      ],
      "env": {
        "MOKA_HOST": "core.mokahr.com"
      }
    }
  }
}
```

## 工具参数

```json
{
  "entId": 123,
  "buId": 456,
  "isIncludeDisable": false,
  "isLimited": true,
  "host": "core.mokahr.com",
  "cookie": "替换为可访问 Moka 的 Cookie",
  "authorization": null,
  "raw": false
}
```

说明：

- `entId`：租户 ID，必填。
- `buId`：BU ID，必填。
- `isIncludeDisable`：是否包含已停用假期类型，默认 `false`。
- `isLimited`：是否筛选限额假期，`true` 只查限额，`false` 只查不限额，不传则不过滤。
- `cookie`：可选，但建议显式传入；传入后优先于环境变量 `MOKA_COOKIE`。
- `authorization`：可选；传入后优先于环境变量 `MOKA_AUTHORIZATION`。
- `raw`：是否返回底层接口原始 `data`。

## 注意

百炼 MCP 服务部署在阿里云 FC，不在本机运行，所以不能使用本地 Chrome Cookie 文件读取方案。请通过工具参数显式传入 `cookie` / `authorization`，或用环境变量兜底。
