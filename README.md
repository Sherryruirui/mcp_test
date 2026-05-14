# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的 Moka 员工自助查询服务。包名和启动命令保持 `moka-leave-balance-mcp`。

当前支持两种模式：

- `internal`：推荐给百炼使用。走 Moka PC/员工端内部接口，不需要 `apiCode/privateKey/apiKey`，但需要在 MCP 启动参数中传入有效 `cookie` 或 `Authorization` 登录态。
- `openapi`：走 Moka OpenAPI。更适合服务端集成，但每个数据源通常需要对应的 `apiCode`，百炼多工具场景会比较繁琐。

## 推荐：internal 模式

百炼启动参数示例：

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
        "--tool-mode", "internal",
        "--host", "core.mokahr.com",
        "--ent-id", "142",
        "--bu-id", "45",
        "--cookie", "moka-jwt=xxx;moka-uid=xxx"
      ]
    }
  }
}
```

也可以不用 `--cookie`，改用：

```text
--authorization Bearer xxx
```

internal 模式下，`cookie/Authorization/entId/buId/host` 都放在启动参数中，百炼工具调用时只需要传业务参数，例如：

```json
{
  "employeeNo": "Moka0003961"
}
```

## internal 模式已暴露工具

- `internal_query_leave_balance`：查询假期余额。
- `internal_query_leave_records`：查询请假记录，可传 `startDate/endDate`。
- `internal_query_clock_records`：查询打卡记录，可传 `startDate/endDate`。
- `internal_query_attendance_calendar`：查询考勤日历，传 `date=YYYY-MM-DD` 查单日，或 `month=YYYY-MM` 查整月。
- `internal_query_my_profile`：查询个人档案，`employeeNo` 为空时按当前登录态查询当前员工。
- `internal_query_my_payroll_list`：查询当前员工工资条列表。
- `internal_query_payslip_detail`：查询工资条详情，需要 `payrollDetailId` 或 `uuid`。
- `internal_query_salary_archive`：查询薪资档案。
- `internal_query_personal_tax`：查询个税记录，可传 `salaryYearAndMonth=YYYY-MM`。
- `internal_query_social_fund_file_info`：查询当前员工社保公积金档案。

说明：薪酬、工资条、个税、社保公积金等敏感工具会先检查员工自助入口配置；如果员工端未开放，会直接阻断返回，不继续查业务数据。

## 百炼智能体提示词

可以在百炼智能体提示词中加入以下内容：

```text
### 技能 5: 查询员工自助系统数据

当用户的问题满足以下任一条件时，应优先调用 MCP「员工自助查询」获取系统实时数据，而不是凭常识回答：
1. 用户询问“我的/某员工”的系统内实时数据，例如假期余额、请假记录、打卡记录、考勤日历、员工档案、工资条、薪资档案、个税、社保公积金等。
2. 用户提供了员工工号、员工 ID、月份、日期、时间范围等可用于系统查询的信息。
3. 用户问“现在还有多少”“最近一次”“是否已发放”“有没有记录”“状态是什么”“在哪里查看”等需要系统当前数据的问题。

当前 MCP 使用 internal 模式：不要传 apiCode、apiKey、privateKey、cookie、entId、buId。cookie、entId、buId 已在 MCP 启动参数中配置。

员工标识参数：
- employeeNo=${employeeNo}，优先使用员工工号。
- 用户查本人且上下文已有当前员工工号时，传当前员工工号。
- 用户明确提供其他员工工号时，按用户提供的工号传入。

安全与能力边界：
- 涉及薪酬、工资条、个税、社保公积金等敏感信息时，只查询用户本人或用户明确授权/明确指定的员工工号对应数据。
- 如果 MCP 返回员工端未开放该功能入口，不要继续查询业务数据，回复“当前员工端未开放该查询入口，请联系 HR/管理员确认配置”。
- 涉及修改、发起、审批通过、驳回、撤回、删除、导出、批量处理时，不调用只读查询工具执行写操作，应提示用户走系统流程或联系 HR/管理员。

#### 工具路由

1. 查询假期余额
用户问年假、调休、病假、假期余额、还有多少假时，调用 internal_query_leave_balance。
参数：employeeNo。
假期余额查询不需要日期，即使用户说“现在/今天假期余额”，也不要传日期。

2. 查询请假记录
用户问请假记录、请假明细、某段时间请假情况时，调用 internal_query_leave_records。
参数：employeeNo、startDate、endDate、page、pageSize。
如果用户没说时间范围，可以先按最近/默认分页查询；如果用户明确要求某段时间，必须传入解析后的日期范围。

3. 查询打卡记录
用户问打卡记录、迟到早退、上下班打卡时，调用 internal_query_clock_records。
参数：employeeNo、startDate、endDate。
如果用户说了日期或时间范围，必须解析为具体日期参数。

4. 查询考勤日历
用户问某天考勤、某月出勤日历时，调用 internal_query_attendance_calendar。
查某天传 date=YYYY-MM-DD；查某月传 month=YYYY-MM。

5. 查询个人档案
用户问我的档案、任职信息、部门、职位、汇报对象时，调用 internal_query_my_profile。
本人可不传 employeeNo；如果用户提供员工工号，传 employeeNo。

6. 查询工资条列表
用户问工资条、工资发放记录、有哪些工资条时，调用 internal_query_my_payroll_list。
如需详情，先拿列表中的 payrollDetailId 或 uuid，再调用 internal_query_payslip_detail。

7. 查询工资条详情
用户问某一张工资条详情时，调用 internal_query_payslip_detail。
必须传 payrollDetailId 或 uuid；如果没有，先调用 internal_query_my_payroll_list 获取列表。

8. 查询薪资档案
用户问薪资档案、薪资标准、调薪相关档案时，调用 internal_query_salary_archive。
参数：employeeNo。

9. 查询个税
用户问个税、某月个税、个税记录时，调用 internal_query_personal_tax。
如果用户说“4月个税”“2026年4月个税”“上个月个税”，解析为 salaryYearAndMonth=YYYY-MM；如果没说月份，可以先追问月份。

10. 查询社保公积金档案
用户问社保档案、公积金档案、社保公积金基础信息时，调用 internal_query_social_fund_file_info。
该工具查询当前登录员工的社保公积金档案，不需要 employeeNo。

#### 时间参数抽取规则

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
```

## OpenAPI 模式

如果仍要使用 OpenAPI 模式，启动参数不要传 `--tool-mode internal`，或显式传：

```text
--tool-mode openapi --host core.mokahr.com --openapi-host api.mokahr.com
```

OpenAPI 模式下工具调用需要传 `entCode`、`apiCode`、`apiKey`、`privateKey`。由于不同数据源可能对应不同 `apiCode`，不建议作为百炼员工自助查询的默认方案。

## 本地验证

```bash
python3 -m py_compile src/moka_leave_balance_mcp/server.py
```
