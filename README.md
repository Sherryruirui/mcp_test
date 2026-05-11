# moka-leave-balance-mcp

面向阿里云百炼 MCP 管理的 Moka 员工自助查询服务。包名和启动命令继续保持 `moka-leave-balance-mcp`，兼容之前在百炼里的配置；实际工具已经扩展为员工自助查询。

这个版本不走 Moka OpenAPI，不需要 `privateKey`、`entCode`、`apiCode`。它沿用 Moka PC/员工端接口形式，通过工具参数里的 `cookie` 使用当前登录态。

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
        "--host",
        "core.mokahr.com"
      ]
    }
  }
}
```

业务参数不放启动参数里，调用工具时传入：

```json
{
  "entId": 142,
  "buId": 45,
  "employeeNo": "Moka0003961",
  "cookie": "moka-jwt=xxx;moka-uid=xxx"
}
```

完整浏览器 Cookie 也可以，MCP 会自动把 `;` 后的空格规范化。

## 已支持工具

身份与配置：

- `query_current_user`：查询当前 Cookie 对应的登录用户/员工身份。
- `check_employee_self_service_capability`：查询员工自助入口是否开放，例如“我的薪酬”“社保公积金”“假期”。
- `check_salary_self_service_enabled`：专门检查“我的薪酬/工资条/薪资”入口是否可见。

假勤：

- `query_leave_balance`：按员工工号查询假期余额，已本地验证过 `POST /api/abs/account/v2/account/pc/balanceList`。
- `query_employee_leave_overview`：查询员工假期账户总览。
- `query_available_leave_types`：查询员工可申请假期类型及余额。
- `query_leave_account_detail`：查询某个假种额度详情。
- `query_leave_records`：查询请假记录。
- `query_leave_send_records`：查询发假记录。
- `query_leave_use_records`：查询假期使用明细。
- `query_clock_records`：查询打卡记录。
- `query_attendance_calendar`：查询考勤日历日详情或月列表。
- `query_profile_attendance_calendar`：查询档案页考勤日历。

员工信息：

- `search_colleague_basic`：搜索同事基础信息，只返回姓名、工号、部门、职位、办公地、头像、直属上级等基础字段。
- `list_candidate_employees`：查询审批候选员工列表，只返回基础字段。
- `query_mobile_staff_info`：查询移动端员工详情，并收口为基础字段。
- `query_my_profile`：查询当前员工个人档案详情。
- `query_my_staff_info`：查询当前员工个人信息 tab。
- `query_my_job_info`：查询当前员工任职信息 tab。
- `query_employee_basic_info`：查询员工基础信息接口。

审批：

- `query_pending_approvals`：查询当前用户待办审批。
- `query_approval_detail`：查询审批详情。
- `query_approval_flow_detail`：查询审批流程详情 PC 汇总接口。
- `query_approval_task_details`：查询审批任务节点详情。
- `query_approval_form_data`：查询审批表单数据。
- `search_approval_instances`：搜索审批实例摘要。
- `list_approval_instances`：查询审批实例列表摘要。

社保公积金：

- `query_social_fund_file_info`：先检查员工自助是否开放社保/公积金/福利入口，再查询当前员工社保公积金档案信息。
- `query_social_fund_history_pay`：先检查入口，再查询缴纳记录。
- `query_social_fund_history_pay_detail`：先检查入口，再查询缴纳明细。

## 暂未实现

- 工资条、工资、个税、奖金、调薪明细查询：目前只实现了“我的薪酬”入口可见性检查。参考资料里没有确认稳定的员工端只读查询接口，所以未直接封装业务数据查询。
- 薪资管理员接口、HR 档案接口、配置写入接口：这些不是员工自助只读能力，未封装。
- 入职自助 no-token 链路：需要 obId/token 类上下文，和当前 Cookie 员工自助链路不同，暂未放进这个包。

## 本地验证

```bash
python3 -m py_compile src/moka_leave_balance_mcp/server.py
```
