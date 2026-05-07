# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的 Moka 员工假期余额查询服务。

这个版本不走 Moka OpenAPI，不需要 `privateKey`、`entCode`、`apiCode`。它沿用内部 client 接口形式，通过 `entId`、`buId`、`employeeNo(s)` 查询具体员工假期余额。

## 工具

- `query_leave_balance`

底层接口：

- `POST /client/v1/hr/employee/v2/searchEmployee`：先根据工号查询员工 ID。
- `POST /client/abs/account/v1/account/balance_list`

## 百炼 uvx 配置

`uvx` 从 GitHub 安装时，建议这样写：

```json
{
  "mcpServers": {
    "moka-leave-balance": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Sherryruirui/mcp_test.git",
        "moka-leave-balance-mcp",
        "--host",
        "core.mokahr.com"
      ]
    }
  }
}
```

如果接口需要登录态，也可以把 Cookie 放到启动参数里：

```json
{
  "args": [
    "--from",
    "git+https://github.com/Sherryruirui/mcp_test.git",
    "moka-leave-balance-mcp",
    "--host",
    "core.mokahr.com",
    "--cookie",
    "key=value; key2=value2"
  ]
}
```

## 启动参数

- `--host`：接口域名，默认 `core.mokahr.com`。
- `--unit-by-leave-rule`：是否按休假规则单位转换额度，默认 `false`。
- `--cookie`：可选，Moka 登录态 Cookie。
- `--authorization`：可选，Authorization 头。

## 工具参数

业务查询条件必须在工具调用时显式传入，不提供启动参数默认值。

单个员工：

```json
{
  "entId": 142,
  "buId": 45,
  "employeeNo": "E001",
  "unitByLeaveRule": false,
  "raw": false
}
```

或查询多个员工：

```json
{
  "entId": 142,
  "buId": 45,
  "employeeNos": ["E001", "E002"]
}
```

## 返回结构

主要字段：

- `leaveBalances.resultBoList`：员工假期余额列表。
- `employeeId`：员工 ID。
- `realName`：员工姓名。
- `employeeNo`：员工工号。
- `absAccountInfoList`：该员工各假期类型的余额。
- `absName`：假期类型名称。
- `availableBalance`：可用余额。
- `effectedAmount`：已生效额度。
- `unEffectedAmount`：未生效额度。
- `usedAmount`：已使用额度。
- `totalAmount`：总额度。
- `unit`：余额单位，通常 `1=天`，`2=小时`。

## 本地验证

```bash
python3 -m py_compile src/moka_leave_balance_mcp/server.py
```
