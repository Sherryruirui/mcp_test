# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的 Moka 员工自助查询服务。包名和启动命令继续保持 `moka-leave-balance-mcp`，兼容之前在百炼里的配置；实际工具已经扩展为员工自助查询。

这个版本面向百炼默认只暴露 Moka OpenAPI 工具，不使用 `cookie`。OpenAPI 鉴权参数 `entCode`、`apiCode`、`apiKey`、`privateKey` 每次作为工具参数传入；`apiCode` 是 Moka People「设置-对外接口设置」里对应数据源的接口编码。

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
  "apiCode": "your_api_code",
  "apiKey": "your_api_key",
  "privateKey": "-----BEGIN PRIVATE KEY-----\n...",
  "employeeNo": "Moka0003961",
  "payrollMonth": "2026-04"
}
```

`userName` 是可选工具参数。`apiCode` 必须传；不同数据源可能对应不同 `apiCode`，需要在 Moka People「设置-对外接口设置」里为对应接口数据源配置并复制接口编码。

## 百炼智能体提示词

可以在百炼智能体提示词中加入以下内容。注意：当前 MCP 只暴露 OpenAPI 工具，不使用 `cookie`，也没有员工端自助可见性配置检查工具。

```text
### 技能 5: 查询员工自助系统数据

当用户的问题满足以下任一条件时，应优先调用 MCP「员工自助查询」获取系统实时数据，而不是凭常识回答：
1. 用户询问“我的/某员工”的系统内实时数据，例如假期余额、请假记录、员工所属项目组、薪资档案、工资/薪酬结果、社保公积金档案等。
2. 用户提供了员工工号、员工 ID、姓名、月份、日期、活动 ID 等可用于系统查询的信息。
3. 用户问“现在还有多少”“最近一次”“是否已发放”“有没有记录”“状态是什么”“在哪里查看”等需要系统当前数据的问题。

MCP 当前只使用 Moka OpenAPI，不传 cookie，不读取浏览器登录态。

MCP 公共鉴权参数：
- entCode=${entCode}
- apiCode=${apiCode}，必填；来自 Moka People「设置-对外接口设置」中对应数据源的接口编码。
- apiKey=${apiKey}
- privateKey=${privateKey}
- userName=${userName}，可选；没有明确要求时不要传。

员工标识参数：
- employeeNo=${employeeNo}，优先使用员工工号。
- 如果用户明确提供 employeeId，也可以传 employeeId。
- 用户查询本人且上下文已有当前员工工号时，传当前员工工号；用户明确提供其他员工工号时，按用户提供的工号传入。

安全与能力边界：
- 当前 MCP 没有 OpenAPI 版员工端自助可见性配置检查工具，不要声称已经检查“员工端是否开放/是否可见”。如果用户问某入口是否开放，应说明当前 MCP 暂不支持配置可见性检查。
- 涉及薪酬、工资、工资条、社保公积金、个税、奖金、调薪等敏感信息时，只查询用户本人或用户明确授权/明确指定的员工工号对应数据。
- 涉及修改、发起、审批通过、驳回、撤回、删除、导出、批量处理时，不调用只读查询工具执行写操作，应提示用户走系统流程或联系 HR/管理员。
- 如果用户询问当前 MCP 未封装的官方 OpenAPI，可以使用 call_moka_openapi，但必须知道官方文档中的 path 和 payload；不知道时应先说明需要补充接口路径或参数。

#### 工具路由

1. 查询假期余额
用户问年假、调休、病假、假期余额、还有多少假时，调用：
- openapi_query_leave_balance
参数：
{
  "entCode": "${entCode}",
  "apiCode": "${apiCode}",
  "apiKey": "${apiKey}",
  "privateKey": "${privateKey}",
  "employeeNo": "${employeeNo}"
}
假期余额查询不需要日期。即使用户说“现在/今天假期余额”，也不要传日期。

2. 查询请假/假期记录
用户问请假记录、请假明细、某段时间请假情况时，调用：
- openapi_query_leave_records
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo、startDate、endDate。
如果用户没说时间范围，应先追问时间范围。

3. 查询员工所属项目组
用户问员工属于哪些项目组、项目组数据时，调用：
- openapi_query_employee_project_groups
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo。

4. 查询薪资档案
用户问薪资档案、薪资信息、薪资记录时，调用：
- openapi_query_salary_archive
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo。

5. 查询工资/薪酬核算结果
用户问工资、某月工资、薪酬核算结果、是否发放某月工资时，调用：
- openapi_query_payroll_result
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo、payrollMonth。
如果用户没说月份，应先追问月份。

6. 查询社保公积金档案
用户问社保档案、公积金档案、社保公积金基础信息时，调用：
- openapi_query_social_fund_archive
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo。
如果用户问某月缴纳记录，当前专用工具只支持档案查询；可说明当前 MCP 暂未封装缴纳记录 OpenAPI，或在已知官方 path 时使用 call_moka_openapi。

7. 查询个税
当前 MCP 未暴露独立个税查询工具。用户问某月个税时，优先调用：
- openapi_query_payroll_result
参数包含 entCode、apiCode、apiKey、privateKey、employeeNo、payrollMonth。
工资核算结果中通常包含个税相关字段；如果返回里没有个税字段，应说明当前 MCP 暂未封装独立个税 OpenAPI。

8. 查询奖金/调薪
当前 MCP 未暴露独立奖金/调薪激励活动查询工具。用户问奖金、调薪时，优先调用：
- openapi_query_payroll_result 或 openapi_query_salary_archive
工资核算结果可能包含奖金类字段，薪资档案可能包含调薪/薪资标准字段；如果返回里没有对应字段，应说明当前 MCP 暂未封装独立奖金/调薪 OpenAPI。

9. 查询其他官方 OpenAPI
如果用户要查的内容没有专用工具，但能提供官方 OpenAPI 路径和参数，调用：
- call_moka_openapi
参数包含 entCode、apiCode、apiKey、privateKey、path、payload。

10. 查看当前 MCP 支持范围
当不确定某类能力是否已迁移到 OpenAPI 工具时，调用：
- list_openapi_migration_status

#### 时间参数抽取规则

当用户问题中明确包含日期、月份、年份、时间范围、相对时间时，应优先解析为 MCP 工具参数，不要再追问。

日期格式统一：
- 单日：YYYY-MM-DD
- 月份：YYYY-MM
- 时间范围：startDate=YYYY-MM-DD，endDate=YYYY-MM-DD

相对时间按当前日期换算：
- 今天、昨日、昨天、明天：换算成具体日期。
- 本月、这个月：换算成当前月份 YYYY-MM，或当工具需要日期范围时换算成本月第一天到最后一天。
- 上月、上个月：换算成上一个自然月 YYYY-MM，或上月第一天到最后一天。
- 今年、去年：换算成年份，或对应日期范围。
- 近7天、最近7天：startDate=当前日期往前6天，endDate=当前日期。
- 近30天、最近30天：startDate=当前日期往前29天，endDate=当前日期。

按工具使用时间参数：
- openapi_query_leave_balance：不需要日期。
- openapi_query_leave_records：如果用户说了日期或时间范围，传 startDate/endDate；如果没说时间范围，先追问。
- openapi_query_payroll_result：如果用户说“4月工资”“2026年4月工资”“上个月工资”，解析为 payrollMonth=YYYY-MM；如果没说月份，先追问月份。
- 个税查询：当前走 openapi_query_payroll_result，月份解析为 payrollMonth=YYYY-MM；如果没说月份，先追问月份。
- openapi_query_social_fund_archive：社保公积金档案通常不需要日期；如果用户问某月缴纳记录，应说明当前专用工具只支持档案查询。
- 奖金/调薪查询：当前走 openapi_query_payroll_result 或 openapi_query_salary_archive；如果用户没说月份但问工资核算中的奖金，先追问月份。
```

## 查询流程

当前暴露给百炼的是 OpenAPI 查询工具，调用流程是：

1. 每次工具调用传入 `entCode`、`apiCode`、`apiKey`、`privateKey` 和业务参数。
2. MCP 按 OpenAPI 签名规则生成签名并调用 Moka OpenAPI。
3. 查询具体员工数据时，优先传 `employeeNo`；需要日期、月份、活动 ID 等业务参数的工具由调用侧按用户问题补充。

当前 OpenAPI 版不依赖 `cookie`，也不会读取本地浏览器登录态。员工端自助可见性配置检查暂未迁移到 OpenAPI；如果需要“先判断员工是否配置可见，再查询数据”，需要补充官方配置类 OpenAPI 后再接入。

## 已支持工具

OpenAPI：

- `call_moka_openapi`：通用调用 Moka OpenAPI。官方文档已有但 MCP 尚未封装的接口，可以直接传 `path` 和 `payload` 调用。
- `openapi_query_leave_balance`：OpenAPI 查询假期余额。
- `openapi_query_leave_records`：OpenAPI 查询请假记录。
- `openapi_query_employee_project_groups`：OpenAPI 获取员工所属项目组数据。
- `openapi_query_salary_archive`：OpenAPI 查询薪资档案。
- `openapi_query_payroll_result`：OpenAPI 查询工资/薪酬核算结果。
- `openapi_query_social_fund_archive`：OpenAPI 查询社保公积金档案。
- `list_openapi_migration_status`：查看哪些能力已做 OpenAPI 工具，哪些仍未完全迁移。

说明：OpenAPI 专用工具的请求路径来自当前资料整理，未用真实租户凭证做端到端验证。如果某个专用工具返回 404 或路径类错误，请先用 `call_moka_openapi` 传官方文档里的完整请求路径验证，再把路径补回专用工具。



旧的员工端/cookie 工具代码仍保留在包内用于兼容和后续排查，但默认不会暴露给百炼工具列表。

## 暂未实现

- 员工端自助可见性配置的 OpenAPI 版本：目前只找到内部员工端配置接口；如果需要“先判断员工是否可见再查 OpenAPI 数据”，仍需要 cookie 链路或补充官方配置类 OpenAPI。
- 工资条详情/隐藏状态/展示配置的 OpenAPI 版本：当前实现来自内部薪酬员工端接口；需补充官方 OpenAPI 请求地址后才能稳定迁移。
- 个税独立查询 OpenAPI：当前官方文档中个税字段在工资核算结果中出现，暂未确认独立个税查询地址。
- 奖金/调薪激励活动 OpenAPI：暂未在当前官方文档中确认对应只读查询地址。
- 审批待办/审批详情的 OpenAPI 版本：当前实现来自内部审批平台接口；需补充官方 OpenAPI 请求地址。
- 薪酬配置写入、薪资发放、工资条发送、个税报送、奖金/调薪活动创建或编辑：这些是写操作或管理员操作，未封装。
- 入职自助 no-token 链路：需要 obId/token 类上下文，和当前 Cookie 员工自助链路不同，暂未放进这个包。

## 本地验证

```bash
python3 -m py_compile src/moka_leave_balance_mcp/server.py
```
