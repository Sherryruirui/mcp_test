# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的 Moka 员工自助查询服务。包名和启动命令继续保持 `moka-leave-balance-mcp`，兼容之前在百炼里的配置；实际工具已经扩展为员工自助查询。

这个版本面向百炼默认只暴露 Moka OpenAPI 工具，不使用 `cookie`。OpenAPI 鉴权参数 `entCode`、`apiKey`、`privateKey` 每次作为工具参数传入；`apiCode` 如果租户没有配置可以不传，MCP 会按全量字段请求尝试调用。

## 百炼配置

```json
{
  "mcpServers": {
    "moka-employee-self-service": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Sherryruirui/mcp_test.git",
        "moka-leave-balance-mcp",
        "--host", "core.mokahr.com",
        "--openapi-host", "api.mokahr.com"
      ]
    }
  }
}
```

OpenAPI 鉴权参数不放启动参数里，每次调用工具时传入，便于不同租户灵活切换。

OpenAPI 工具调用时不传 cookie，传 OpenAPI 鉴权参数、员工标识和业务参数：

```json
{
  "entCode": "your_ent_code",
  "apiKey": "your_api_key",
  "privateKey": "-----BEGIN PRIVATE KEY-----\n...",
  "employeeNo": "Moka0003961",
  "payrollMonth": "2026-04"
}
```

`apiCode` 和 `userName` 是可选工具参数；如果你的租户没有 `apiCode`，不传即可。

## 查询流程

所有业务查询统一走同一条管线：

1. 用通用员工搜索/当前用户接口将 `employeeNo` 解析为 `employeeId`。
2. 查询员工自助配置，判断当前业务入口是否配置为员工可见。
3. 未配置员工可见时直接阻断，返回“当前信息不可查询”；配置可见后才调用具体业务接口。

可单独调用 `resolve_employee_id_by_no` 调试工号到 `employeeId` 的解析结果。

## 已支持工具

OpenAPI：

- `call_moka_openapi`：通用调用 Moka OpenAPI。官方文档已有但 MCP 尚未封装的接口，可以直接传 `path` 和 `payload` 调用。
- `openapi_query_leave_balance`：OpenAPI 查询假期余额。
- `openapi_query_leave_records`：OpenAPI 查询请假记录。
- `openapi_query_employee_project_groups`：OpenAPI 获取员工所属项目组数据。
- `openapi_query_salary_archive`：OpenAPI 查询薪资档案。
- `openapi_query_payroll_result`：OpenAPI 查询工资/薪酬核算结果。
- `openapi_query_social_fund_archive`：OpenAPI 查询社保公积金档案。
- `openapi_query_personal_tax`：OpenAPI 查询个税记录。
- `openapi_query_incentive_activity`：OpenAPI 查询奖金/调薪激励活动或员工明细。
- `list_openapi_migration_status`：查看哪些能力已做 OpenAPI 工具，哪些仍未完全迁移。

说明：OpenAPI 专用工具的请求路径来自当前资料整理，未用真实租户凭证做端到端验证。如果某个专用工具返回 404 或路径类错误，请先用 `call_moka_openapi` 传官方文档里的完整请求路径验证，再把路径补回专用工具。



旧的员工端/cookie 工具代码仍保留在包内用于兼容和后续排查，但默认不会暴露给百炼工具列表。

## 暂未实现

- 员工端自助可见性配置的 OpenAPI 版本：目前只找到内部员工端配置接口；如果需要“先判断员工是否可见再查 OpenAPI 数据”，仍需要 cookie 链路或补充官方配置类 OpenAPI。
- 工资条详情/隐藏状态/展示配置的 OpenAPI 版本：当前实现来自内部薪酬员工端接口；需补充官方 OpenAPI 请求地址后才能稳定迁移。
- 审批待办/审批详情的 OpenAPI 版本：当前实现来自内部审批平台接口；需补充官方 OpenAPI 请求地址。
- 薪酬配置写入、薪资发放、工资条发送、个税报送、奖金/调薪活动创建或编辑：这些是写操作或管理员操作，未封装。
- 入职自助 no-token 链路：需要 obId/token 类上下文，和当前 Cookie 员工自助链路不同，暂未放进这个包。

## 本地验证

```bash
python3 -m py_compile src/moka_leave_balance_mcp/server.py
```
