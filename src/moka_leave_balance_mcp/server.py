from __future__ import annotations

import argparse
import base64
import json
import random
import ssl
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date as date_type
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from mcp.server.fastmcp import FastMCP

MCP_NAME = "moka-employee-self-service"
DEFAULT_HOST = "core.mokahr.com"
DEFAULT_OPENAPI_HOST = "api.mokahr.com"
SUCCESS_CODES = {0, "0", 200, "200", "00000", 1000000, "1000000"}
AUTH_CONTEXT_ERROR_CODES = {100007, "100007"}
EMPLOYEE_CONTEXT_ERROR_CODES = {100000, "100000"}

PATH_CURRENT_USER = "/api/aggregate/employee/getUserInfo"
PATH_LEAVE_BALANCE = "/api/abs/account/v2/account/pc/balanceList"
PATH_LEAVE_ACCOUNT_DETAIL = "/api/abs/account/v2/account/pc/accountDetail"
PATH_LEAVE_RECORDS = "/api/abs/account/v1/leave/search"
PATH_LEAVE_SEND_RECORDS = "/api/abs/account/v2/account/pc/sendRecordList"
PATH_LEAVE_USE_RECORDS = "/api/abs/account/v2/account/pc/useRecordList"
PATH_CLOCK_RECORDS = "/api/abs/clock/v1/clock/getRecordList"
PATH_ATTENDANCE_CALENDAR_DETAIL = "/api/abs/attendance/calendar/v1/detail"
PATH_ATTENDANCE_CALENDAR_LIST = "/api/abs/attendance/calendar/v1/list"
PATH_ATTENDANCE_CALENDAR_PROFILE = "/api/statistics/v1/abs/profile/attendance/calendar"
PATH_EMP_ACCOUNT_INFO = "/api/abs/account/v1/account/app/empAccountInfo"
PATH_LEAVE_TYPES = "/api/abs/account/v1/leave/query_leave_types"

PATH_PROFILE_DETAIL = "/api/core/v1/hr/profileDetail"
PATH_STAFF_INFO = "/api/personnel/v1/staffInfo/tab/pc/info"
PATH_JOB_INFO = "/api/personnel/v1/jobInfo/tab/pc/info"
PATH_EMPLOYEE_INFO = "/api/core/v1/hr/employee/getEmployeeInfo"
PATH_EMPLOYEE_SEARCH = "/api/aggregate/v1/search/employee"
PATH_EMPLOYEE_LIST = "/api/core/v1/hr/employee/getList"
PATH_ROSTER_LIST = "/api/core/v1/hr/roster/rosterList"
PATH_ORG_STAFF_INFO = "/api/organization/v1/hr/staff/info"
PATH_CANDIDATE_EMPLOYEE_LIST = "/api/workflowplatform/candidate/employee/list"

PATH_PENDING_APPROVALS = "/api/workflowplatform/backlog/listAssigneeBacklogBrief"
PATH_APPROVAL_DETAIL = "/api/workflow/v1/instance/detail"
PATH_FLOW_DETAIL_PC = "/api/workflow/m/v1/getFlowDetailsOnPC"
PATH_FLOW_TASK_DETAILS = "/api/workflow/m/v1/getFlowTaskDetails"
PATH_APPROVAL_FORM_DATA = "/api/workflow/v1/use/getData"
PATH_FLOWINST_SEARCH_BRIEF = "/api/workflowplatform/flowInst/search/brief"
PATH_FLOWINST_LIST_BRIEF = "/api/workflowplatform/flowInst/list/brief"

PATH_SELF_SERVICE_MOBILE_LIST = "/api/universal/v1/self-service/mobile/list"
PATH_SELF_SERVICE_HOME_LIST = "/api/universal/v1/self-service/home/list"
PATH_SELF_SERVICE_COMMON_USE = "/api/universal/v1/self-service/listForCommonUse"

PATH_MY_PAYROLL_LIST = "/api/salary/v1/payroll/emp/payrollList"
PATH_MY_SALARY_INFO = "/api/salary/v1/payroll/emp/salaryInfo"
PATH_PAYROLL_AVAILABLE_ITEM = "/api/salary/v1/payroll/setting/availableItem"
PATH_PAYROLL_EMP_MULTI_INFO = "/api/salary/v1/payroll/emp/multiInfo"
PATH_PAYROLL_EMP_PASS_HIDDEN = "/api/salary/v1/payroll/emp/pass/hidden"
PATH_PAYROLL_EMP_DISPLAY_CONFIG = "/api/salary/v1/payroll/emp/display/config/get"
PATH_PAYSLIP_EMP_INFO = "/api/salary/v1/temp/getEmpInfo"
PATH_PAYSLIP_DETAIL = "/api/salary/v1/temp/fill/temp"
PATH_TAX_STAFF_REPORT_SEARCH = "/api/salary/v1/tax/staffReport/search"
PATH_TAX_STAFF_REPORT_SEARCH_FACTOR = "/api/salary/v1/tax/staffReport/searchFactor"
PATH_TAX_BONUS_WHOLE_YEAR_INCOME = "/api/salary/v1/tax/collect/report/selectWholeYearIncome"
PATH_TAX_EQUITY_INCENTIVE_INCOME = "/api/salary/v1/tax/collect/report/selectEquityIncentivesIncome"
PATH_SALARY_ARCHIVES_INFO = "/api/salary/v1/archives/page/info"
PATH_SALARY_ARCHIVES_FIELD_CHANGE = "/api/salary/v1/archives/page/filed/change"
PATH_SALARY_EMPLOYEE_INFO = "/api/salary/v1/employee/info"
PATH_INCENTIVE_ACTIVITY_LIST = "/api/salary/v1/incentive/activity/list"
PATH_INCENTIVE_ACTIVITY_INFO = "/api/salary/v1/incentive/activity/info"
PATH_INCENTIVE_EMPLOYEE_INFO = "/api/salary/v1/incentive/employee/info"
PATH_INCENTIVE_EMPLOYEE_ADJUST_DETAIL = "/api/salary/v1/incentive/employee/table/adjustDetail"
PATH_INCENTIVE_EMPLOYEE_GROWTH_RECORDS = "/api/salary/v1/incentive/employee/growth/listRecord"
PATH_INCENTIVE_ADJUST_CHART_TAGS = "/api/salary/v1/incentive/statistics/adjustChart/Tag"
PATH_INCENTIVE_ADJUST_CHART = "/api/salary/v1/incentive/statistics/adjustChart"

PATH_WELFARE_FILE_INFO = "/api/welfare/v1/mobile/fileInfo"
PATH_WELFARE_HISTORY_PAY = "/api/welfare/v1/mobile/history/pay"
PATH_WELFARE_HISTORY_PAY_DETAIL = "/api/welfare/v1/mobile/history/pay/detail"

COLLEAGUE_BASIC_KEYS = {
    "avatar",
    "avatarUrl",
    "department",
    "departmentName",
    "deptName",
    "duty",
    "dutyName",
    "employeeId",
    "employeeNo",
    "id",
    "leader",
    "leaderName",
    "name",
    "officeAddress",
    "officeLocation",
    "position",
    "positionName",
    "realName",
    "realname",
}

SALARY_KEYWORDS = ("我的薪酬", "薪酬", "工资", "工资条", "薪资")
SOCIAL_FUND_KEYWORDS = ("社保公积金", "社保", "公积金", "福利")
BUSINESS_CAPABILITY_KEYWORDS = {
    "profile": ("个人档案", "我的档案", "个人信息", "任职信息", "员工档案", "人事档案"),
    "attendance": ("假期", "假期余额", "请假", "休假", "考勤", "打卡"),
    "approval": ("审批", "待办", "流程"),
    "colleague": ("通讯录", "同事", "员工信息", "组织架构", "找人"),
    "salary": SALARY_KEYWORDS,
    "social_fund": SOCIAL_FUND_KEYWORDS,
}
BUSINESS_CAPABILITY_LABELS = {
    "profile": "个人档案/个人信息",
    "attendance": "假期/考勤",
    "approval": "审批",
    "colleague": "同事基础信息",
    "salary": "我的薪酬",
    "social_fund": "社保公积金",
}
ENDPOINT_CAPABILITIES = {
    PATH_LEAVE_BALANCE: "attendance",
    PATH_LEAVE_ACCOUNT_DETAIL: "attendance",
    PATH_LEAVE_RECORDS: "attendance",
    PATH_LEAVE_SEND_RECORDS: "attendance",
    PATH_LEAVE_USE_RECORDS: "attendance",
    PATH_CLOCK_RECORDS: "attendance",
    PATH_ATTENDANCE_CALENDAR_DETAIL: "attendance",
    PATH_ATTENDANCE_CALENDAR_LIST: "attendance",
    PATH_ATTENDANCE_CALENDAR_PROFILE: "attendance",
    PATH_EMP_ACCOUNT_INFO: "attendance",
    PATH_LEAVE_TYPES: "attendance",
    PATH_PROFILE_DETAIL: "profile",
    PATH_STAFF_INFO: "profile",
    PATH_JOB_INFO: "profile",
    PATH_EMPLOYEE_INFO: "profile",
    PATH_ORG_STAFF_INFO: "colleague",
    PATH_EMPLOYEE_SEARCH: "colleague",
    PATH_EMPLOYEE_LIST: "colleague",
    PATH_ROSTER_LIST: "colleague",
    PATH_CANDIDATE_EMPLOYEE_LIST: "colleague",
    PATH_PENDING_APPROVALS: "approval",
    PATH_APPROVAL_DETAIL: "approval",
    PATH_FLOW_DETAIL_PC: "approval",
    PATH_FLOW_TASK_DETAILS: "approval",
    PATH_APPROVAL_FORM_DATA: "approval",
    PATH_FLOWINST_SEARCH_BRIEF: "approval",
    PATH_FLOWINST_LIST_BRIEF: "approval",
    PATH_MY_PAYROLL_LIST: "salary",
    PATH_MY_SALARY_INFO: "salary",
    PATH_PAYROLL_AVAILABLE_ITEM: "salary",
    PATH_PAYROLL_EMP_MULTI_INFO: "salary",
    PATH_PAYROLL_EMP_PASS_HIDDEN: "salary",
    PATH_PAYROLL_EMP_DISPLAY_CONFIG: "salary",
    PATH_PAYSLIP_EMP_INFO: "salary",
    PATH_PAYSLIP_DETAIL: "salary",
    PATH_TAX_STAFF_REPORT_SEARCH: "salary",
    PATH_TAX_STAFF_REPORT_SEARCH_FACTOR: "salary",
    PATH_TAX_BONUS_WHOLE_YEAR_INCOME: "salary",
    PATH_TAX_EQUITY_INCENTIVE_INCOME: "salary",
    PATH_SALARY_ARCHIVES_INFO: "salary",
    PATH_SALARY_ARCHIVES_FIELD_CHANGE: "salary",
    PATH_SALARY_EMPLOYEE_INFO: "salary",
    PATH_INCENTIVE_ACTIVITY_LIST: "salary",
    PATH_INCENTIVE_ACTIVITY_INFO: "salary",
    PATH_INCENTIVE_EMPLOYEE_INFO: "salary",
    PATH_INCENTIVE_EMPLOYEE_ADJUST_DETAIL: "salary",
    PATH_INCENTIVE_EMPLOYEE_GROWTH_RECORDS: "salary",
    PATH_INCENTIVE_ADJUST_CHART_TAGS: "salary",
    PATH_INCENTIVE_ADJUST_CHART: "salary",
    PATH_WELFARE_FILE_INFO: "social_fund",
    PATH_WELFARE_HISTORY_PAY: "social_fund",
    PATH_WELFARE_HISTORY_PAY_DETAIL: "social_fund",
}

mcp = FastMCP(MCP_NAME)


@dataclass
class ServerConfig:
    host: str = DEFAULT_HOST
    openapi_host: str = DEFAULT_OPENAPI_HOST
    tool_mode: str = "openapi"
    ent_id: int | None = None
    bu_id: int | None = None
    cookie: str | None = None
    authorization: str | None = None


CONFIG = ServerConfig()


def _configure_from_args() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--openapi-host", default=DEFAULT_OPENAPI_HOST)
    parser.add_argument("--tool-mode", choices=("openapi", "internal"), default="openapi")
    parser.add_argument("--ent-id", type=int)
    parser.add_argument("--bu-id", type=int)
    parser.add_argument("--cookie", nargs="+")
    parser.add_argument("--authorization")
    args, _ = parser.parse_known_args()

    CONFIG.host = args.host
    CONFIG.openapi_host = args.openapi_host
    CONFIG.tool_mode = args.tool_mode
    CONFIG.ent_id = args.ent_id
    CONFIG.bu_id = args.bu_id
    CONFIG.cookie = _normalize_cookie_arg(args.cookie)
    CONFIG.authorization = args.authorization


def _normalize_cookie_arg(value: str | list[str] | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        value = " ".join(value)
    cookie = str(value).strip()
    if not cookie:
        return None
    return "; ".join(part.strip() for part in cookie.split(";") if part.strip())


def _auth_headers(cookie: str | list[str] | None = None, authorization: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "User-Agent": "moka-employee-self-service-mcp/0.3",
    }
    resolved_cookie = _normalize_cookie_arg(cookie) or CONFIG.cookie
    resolved_authorization = authorization or CONFIG.authorization
    if resolved_cookie:
        headers["Cookie"] = resolved_cookie
    if resolved_authorization:
        headers["Authorization"] = resolved_authorization
    return headers


def _required_openapi_credentials(
    user_name: str | None,
    ent_code: str | None,
    api_code: str | None,
    api_key: str | None,
    private_key: str | None = None,
) -> dict[str, Any] | None:
    missing: list[str] = []
    _ = user_name
    if not ent_code:
        missing.append("entCode")
    if not api_code:
        missing.append("apiCode")
    if not api_key:
        missing.append("apiKey")
    if not private_key:
        missing.append("privateKey")
    if not missing:
        return None
    return _missing_params_error(
        "openapi",
        missing,
        "缺少 Moka OpenAPI 鉴权参数。OpenAPI 不使用 cookie，需要传 entCode、apiCode、apiKey、privateKey；apiCode 是 Moka People「设置-对外接口设置」里对应数据源的接口编码。",
        examples=[{"entCode": "your_ent_code", "apiCode": "your_api_code", "apiKey": "your_api_key", "privateKey": "-----BEGIN PRIVATE KEY-----\\n..."}],
    )


def _openapi_nonce(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _normalize_private_key(private_key: str | None) -> str | None:
    if not private_key:
        return None
    text = private_key.strip().replace("\\n", "\n")
    if "BEGIN" in text:
        return text
    return f"-----BEGIN PRIVATE KEY-----\n{text}\n-----END PRIVATE KEY-----"


def _openapi_sign_params(params: dict[str, Any], private_key: str) -> str:
    normalized_key = _normalize_private_key(private_key)
    if not normalized_key:
        raise ValueError("privateKey 不能为空")
    key = serialization.load_pem_private_key(normalized_key.encode("utf-8"), password=None)
    sign_text = "&".join(f"{key}={params[key]}" for key in sorted(params) if key != "sign" and params[key] is not None).encode("utf-8")
    signature = key.sign(sign_text, padding.PKCS1v15(), hashes.MD5())
    return base64.b64encode(signature).decode("utf-8")


def _openapi_auth(
    ent_code: str,
    api_code: str | None,
    api_key: str,
    private_key: str,
    user_name: str | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    timestamp = int(time.time() * 1000)
    nonce = _openapi_nonce()
    params: dict[str, Any] = {
        "entCode": ent_code,
        "timestamp": timestamp,
        "nonce": nonce,
    }
    if api_code:
        params["apiCode"] = api_code
    if user_name:
        params["userName"] = user_name
    params["sign"] = _openapi_sign_params(params, private_key)
    basic = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("utf-8")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "moka-openapi-mcp/0.3",
        "Authorization": f"Basic {basic}",
    }
    return headers, params


def _openapi_extract_response(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        body = result.get("body")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                pass
        if _response_has_employee_context_error(body) or _response_has_employee_context_error(result.get("error")):
            return _employee_context_error_response(
                raw=body or result,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        return result
    response = result.get("response")
    if isinstance(response, dict):
        code = response.get("code")
        if code in SUCCESS_CODES or response.get("success") is True:
            return {"ok": True, "data": response.get("data", response), "raw": response}
        return {"ok": False, "error": f"OpenAPI failed: code={code}, msg={response.get('msg') or response.get('message') or ''}", "raw": response}
    return {"ok": True, "data": response, "raw": response}


def _request_openapi(
    *,
    host: str,
    path: str,
    payload: dict[str, Any] | None,
    ent_code: str,
    user_name: str | None,
    api_code: str | None,
    api_key: str,
    private_key: str,
) -> dict[str, Any]:
    body = json.dumps(payload or {}, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    try:
        headers, params = _openapi_auth(ent_code, api_code, api_key, private_key, user_name=user_name)
    except Exception as exc:
        return {"ok": False, "error": f"OpenAPI 签名生成失败：{exc}"}
    query = urllib.parse.urlencode(params)
    url = f"https://{host}{path}?{query}"
    request = urllib.request.Request(url=url, data=body, method="POST")
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return {
                "ok": True,
                "status": resp.status,
                "contentType": resp.headers.get("content-type"),
                "response": data,
                "url": url,
            }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "status": exc.code, "error": str(exc), "body": error_body, "url": url}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def _call_openapi(
    *,
    path: str,
    payload: dict[str, Any] | None = None,
    userName: str | None = None,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    missing = _required_openapi_credentials(userName, entCode, apiCode, apiKey, privateKey)
    if missing:
        return missing
    resolved_ent_code = entCode
    resolved_user_name = userName
    resolved_api_code = apiCode
    resolved_api_key = apiKey
    resolved_private_key = privateKey
    if not resolved_ent_code or not resolved_api_key or not resolved_private_key:
        return {"ok": False, "error": "缺少 OpenAPI 鉴权参数。"}
    result = _openapi_extract_response(
        _request_openapi(
            host=openapiHost or CONFIG.openapi_host,
            path=path,
            payload=payload or {},
            ent_code=resolved_ent_code,
            user_name=resolved_user_name,
            api_code=resolved_api_code,
            api_key=resolved_api_key,
            private_key=resolved_private_key,
        )
    )
    if not result.get("ok"):
        return result
    data = result.get("data")
    output = {"ok": True, "data": data, "sourceEndpoint": path}
    if data in ({}, [], None):
        output["emptyData"] = True
        output["requestPayload"] = payload or {}
        output["diagnosis"] = (
            "OpenAPI 调用成功但 data 为空。请先确认 employeeNo/employeeId 在当前 entCode 对应租户下存在；"
            "如果员工存在，则需要核对该专用工具的 OpenAPI path 和请求字段是否与 people.mokahr.com 官方文档一致。"
            "可以把 raw=true 后的 raw.code/msg/data 与官方接口文档对照，或使用 call_moka_openapi 传官方 path/payload 验证。"
        )
    if raw:
        output["raw"] = result.get("raw")
    return output


def _request_json(
    method: str,
    host: str,
    path: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    cookie: str | list[str] | None = None,
    authorization: str | None = None,
) -> dict[str, Any]:
    clean_params = {key: value for key, value in (params or {}).items() if value is not None}
    query = urllib.parse.urlencode(clean_params, doseq=True)
    url = f"https://{host}{path}"
    if query:
        url = f"{url}?{query}"

    body = None
    normalized_method = method.upper()
    if normalized_method != "GET":
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(url=url, data=body, method=normalized_method)
    for key, value in _auth_headers(cookie=cookie, authorization=authorization).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return {
                "ok": True,
                "status": resp.status,
                "contentType": resp.headers.get("content-type"),
                "response": data,
                "url": url,
            }
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "status": exc.code, "error": str(exc), "body": error_body, "url": url}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def _post_json(
    host: str,
    path: str,
    payload: dict[str, Any],
    cookie: str | list[str] | None = None,
    authorization: str | None = None,
) -> dict[str, Any]:
    return _request_json("POST", host, path, payload=payload, cookie=cookie, authorization=authorization)


def _message_has_auth_context_error(message: str) -> bool:
    return (
        "获取用户信息失败" in message
        or "未登录" in message
        or "登录态" in message
        or ("登录" in message and "失败" in message)
    )


def _response_has_auth_context_error(response: Any) -> bool:
    if isinstance(response, dict):
        code = response.get("code")
        message = str(response.get("msg") or response.get("message") or response.get("error") or "")
        return code in AUTH_CONTEXT_ERROR_CODES or _message_has_auth_context_error(message)
    if isinstance(response, str):
        return "100007" in response or _message_has_auth_context_error(response)
    return False


def _message_has_employee_context_error(message: str) -> bool:
    return (
        "获取员工信息失败" in message
        or "无法从当前登录态解析当前员工" in message
        or "当前用户信息中未找到 employeeId" in message
    )


def _response_has_employee_context_error(response: Any) -> bool:
    if isinstance(response, dict):
        code = response.get("code")
        message = str(response.get("msg") or response.get("message") or response.get("error") or "")
        return code in EMPLOYEE_CONTEXT_ERROR_CODES and _message_has_employee_context_error(message)
    if isinstance(response, str):
        return _message_has_employee_context_error(response)
    return False


def _auth_context_error_response(
    *,
    raw: Any,
    url: str | None = None,
    status: int | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "ok": False,
        "authContextError": True,
        "error": "当前 Moka 登录态不可用或已过期，后端无法获取当前用户信息。请在 MCP 工具参数 cookie 中传入当前浏览器登录 core.mokahr.com 的完整有效 Cookie 后重试。",
        "askUserFor": ["cookie"],
        "requiredCookieHint": "建议传完整 Cookie；至少应包含有效的 moka-jwt 和 moka-uid，格式如 moka-jwt=xxx;moka-uid=xxx。",
        "nextAction": "重新从 Chrome 开发者工具 Network 请求头中复制 core.mokahr.com 的 Cookie，更新百炼工具入参后再次调用。",
        "raw": raw,
    }
    if status is not None:
        output["status"] = status
    if content_type:
        output["contentType"] = content_type
    if url:
        output["url"] = url
    return output


def _employee_context_error_response(
    *,
    raw: Any,
    url: str | None = None,
    status: int | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "ok": False,
        "employeeContextError": True,
        "error": "当前登录态可用，但后端无法解析当前员工身份或当前接口要求的员工上下文。请确认 Cookie 来自 Moka 员工端已登录账号，且该账号已绑定员工档案；如果要查询指定员工，请同时传 employeeNo，必要时先调用 diagnose_moka_session。",
        "askUserFor": ["cookie", "employeeNo"],
        "nextAction": "先调用 diagnose_moka_session 检查当前用户、员工解析和员工自助配置；如果诊断里 currentUser 正常但 currentEmployee 不正常，需要换成员工本人或有员工身份的账号 Cookie。",
        "raw": raw,
    }
    if status is not None:
        output["status"] = status
    if content_type:
        output["contentType"] = content_type
    if url:
        output["url"] = url
    return output


def _employee_context_error_response(
    *,
    raw: Any,
    url: str | None = None,
    status: int | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    output: dict[str, Any] = {
        "ok": False,
        "employeeContextError": True,
        "error": "当前登录态可用，但后端无法解析当前员工身份或当前接口要求的员工上下文。请确认 Cookie 来自 Moka 员工端已登录账号，且该账号已绑定员工档案；如果要查询指定员工，请同时传 employeeNo，必要时先调用 diagnose_moka_session。",
        "askUserFor": ["cookie", "employeeNo"],
        "nextAction": "先调用 diagnose_moka_session 检查当前用户、员工解析和员工自助配置；如果诊断里 currentUser 正常但 currentEmployee 不正常，需要换成员工本人或有员工身份的账号 Cookie。",
        "raw": raw,
    }
    if status is not None:
        output["status"] = status
    if content_type:
        output["contentType"] = content_type
    if url:
        output["url"] = url
    return output


def _extract_data(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        body = result.get("body")
        if _response_has_auth_context_error(body) or _response_has_auth_context_error(result.get("error")):
            return _auth_context_error_response(
                raw=body or result,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(body) or _response_has_employee_context_error(result.get("error")):
            return _employee_context_error_response(
                raw=body or result,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(body) or _response_has_employee_context_error(result.get("error")):
            return _employee_context_error_response(
                raw=body or result,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        return result
    response = result.get("response")
    if isinstance(response, dict):
        code = response.get("code")
        if code in SUCCESS_CODES:
            return {"ok": True, "data": response.get("data"), "raw": response}
        if code is None and ("data" in response or "success" in response):
            return {"ok": True, "data": response.get("data", response), "raw": response}
        if _response_has_auth_context_error(response):
            return _auth_context_error_response(
                raw=response,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(response):
            return _employee_context_error_response(
                raw=response,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(response):
            return _employee_context_error_response(
                raw=response,
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        return {"ok": False, "error": f"API failed: code={code}, msg={response.get('msg', '')}", "raw": response}
    if isinstance(response, str):
        preview = response[:500]
        if _response_has_auth_context_error(response):
            return _auth_context_error_response(
                raw=response[:2000],
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(response):
            return _employee_context_error_response(
                raw=response[:2000],
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if _response_has_employee_context_error(response):
            return _employee_context_error_response(
                raw=response[:2000],
                url=result.get("url"),
                status=result.get("status"),
                content_type=result.get("contentType"),
            )
        if "<!DOCTYPE html" in preview or "<html" in preview:
            return {
                "ok": False,
                "authContextError": True,
                "error": "接口返回 HTML 页面，不是 JSON；通常表示未登录、缺少 Cookie/Authorization，或 host 没有路由到后端接口。",
                "askUserFor": ["cookie"],
                "status": result.get("status"),
                "contentType": result.get("contentType"),
                "url": result.get("url"),
                "responsePreview": preview,
            }
        return {
            "ok": False,
            "error": "接口返回非 JSON 内容，无法解析。",
            "status": result.get("status"),
            "contentType": result.get("contentType"),
            "url": result.get("url"),
            "responsePreview": preview,
        }
    return result


def _merge_payload(base: dict[str, Any], extra: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(base)
    if extra:
        merged.update(extra)
    return merged


def _missing_params_error(tool: str, missing: list[str], message: str, examples: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "ok": False,
        "error": message,
        "tool": tool,
        "missingRequiredParams": missing,
        "askUserFor": missing,
        "examples": examples or [],
    }


def _parse_year_month(month_value: str | None) -> tuple[int | None, int | None]:
    if not month_value:
        return None, None
    text = str(month_value).strip()
    if not text:
        return None, None
    if "-" in text:
        parts = text.split("-")
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    if len(text) == 6 and text.isdigit():
        return int(text[:4]), int(text[4:])
    return None, None


def _today_year_month() -> tuple[int, int]:
    today = date_type.today()
    return today.year, today.month


def _require_cookie(cookie: str | list[str] | None) -> dict[str, Any] | None:
    if _normalize_cookie_arg(cookie) or CONFIG.cookie:
        return None
    return {"ok": False, "error": "缺少 cookie。该 MCP 走 Moka 员工端/PC 登录态接口，需要把当前登录用户 Cookie 作为工具参数传入。"}


def _internal_context() -> dict[str, Any]:
    if not CONFIG.cookie and not CONFIG.authorization:
        return {
            "ok": False,
            "error": "缺少启动鉴权。internal 模式不需要 apiCode/privateKey/apiKey，但需要在 MCP 启动参数中配置 --cookie 或 --authorization。",
            "askUserFor": ["cookie 或 authorization"],
        }
    if CONFIG.ent_id is None or CONFIG.bu_id is None:
        return {
            "ok": False,
            "error": "缺少启动参数 entId/buId。internal 模式需要在百炼启动参数中配置 --ent-id 和 --bu-id。",
            "askUserFor": ["entId", "buId"],
        }
    return {
        "ok": True,
        "host": CONFIG.host,
        "entId": CONFIG.ent_id,
        "buId": CONFIG.bu_id,
        "cookie": CONFIG.cookie,
        "authorization": CONFIG.authorization,
    }


def _internal_employee(
    host: str,
    cookie: str | None,
    authorization: str | None,
    employee_no: str | None,
    employee_id: int | None = None,
) -> dict[str, Any]:
    return _resolve_employee_id(host, cookie, authorization, employee_id=employee_id, employee_no=employee_no)


def _pick_employee_id(value: Any) -> int | None:
    if isinstance(value, dict):
        for key in ("employeeId", "id", "userId"):
            if value.get(key) is not None:
                try:
                    return int(value[key])
                except (TypeError, ValueError):
                    pass
        for nested_key in ("employee", "user", "staff", "profile", "data"):
            nested = _pick_employee_id(value.get(nested_key))
            if nested is not None:
                return nested
    return None


def _pick_text(value: Any, keys: tuple[str, ...]) -> str | None:
    if isinstance(value, dict):
        for key in keys:
            item = value.get(key)
            if item not in (None, ""):
                return str(item)
        for child in value.values():
            found = _pick_text(child, keys)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _pick_text(child, keys)
            if found:
                return found
    return None


def _api_error_code(result: dict[str, Any]) -> Any:
    raw = result.get("raw")
    if isinstance(raw, dict):
        return raw.get("code")
    return None


def _is_auth_context_error(result: dict[str, Any]) -> bool:
    code = _api_error_code(result)
    message = str(result.get("error") or "")
    return bool(result.get("authContextError")) or code in AUTH_CONTEXT_ERROR_CODES or _message_has_auth_context_error(message)


def _current_employee(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
) -> dict[str, Any]:
    result = _extract_data(_post_json(host, PATH_CURRENT_USER, {}, cookie=cookie, authorization=authorization))
    if not result.get("ok"):
        return {"ok": False, "error": "无法从当前登录态解析当前员工", "raw": result}
    data = result.get("data")
    employee_id = _pick_employee_id(data)
    if employee_id is None:
        return {"ok": False, "error": "当前用户信息中未找到 employeeId", "raw": result}
    return {
        "ok": True,
        "employeeId": employee_id,
        "employeeNo": _pick_text(data, ("employeeNo", "employee_no", "jobEmployeeNo", "job_employee_no")),
        "realName": _pick_text(data, ("realName", "realname", "name")),
        "sourceEndpoint": PATH_CURRENT_USER,
        "raw": result,
    }


def _resolve_current_employee_id(host: str, cookie: str | list[str] | None, authorization: str | None) -> int | None:
    current = _current_employee(host, cookie, authorization)
    if not current.get("ok"):
        return None
    return current.get("employeeId")


def _map_balance_records(data: Any, employee_nos: list[str]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"ok": False, "error": "假期余额接口返回结构不是对象", "rawData": data}

    columns = data.get("columns") or []
    records = data.get("records") or []
    if not isinstance(columns, list):
        columns = []
    if not isinstance(records, list):
        records = []

    leave_name_by_id = {
        column.get("absId"): column.get("name")
        for column in columns
        if isinstance(column, dict)
    }
    requested_nos = {employee_no.strip().lower(): employee_no for employee_no in employee_nos}
    matched_records: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue
        employee_no = str(record.get("employeeNo") or "").strip()
        if requested_nos and employee_no.lower() not in requested_nos:
            continue

        balances: list[dict[str, Any]] = []
        for balance in record.get("absAccountInfos") or []:
            if not isinstance(balance, dict):
                continue
            item = dict(balance)
            item["absName"] = leave_name_by_id.get(balance.get("absId"))
            balances.append(item)

        matched_records.append(
            {
                "employeeId": record.get("employeeId"),
                "realName": record.get("realName"),
                "employeeNo": employee_no,
                "absAccountInfos": balances,
            }
        )

    found_nos = {str(record.get("employeeNo") or "").strip().lower() for record in matched_records}
    return {
        "ok": True,
        "columns": columns,
        "records": matched_records,
        "total": len(matched_records),
        "notFoundEmployeeNos": [
            employee_no
            for employee_no in employee_nos
            if employee_no.strip().lower() not in found_nos
        ],
    }


def _query_pc_balance_by_employee_no(
    host: str,
    employee_no: str,
    cookie: str | list[str] | None = None,
    authorization: str | None = None,
) -> dict[str, Any]:
    return _extract_data(
        _post_json(
            host=host,
            path=PATH_LEAVE_BALANCE,
            payload={"page": 1, "pageSize": 20, "userKeyWord": employee_no},
            cookie=cookie,
            authorization=authorization,
        )
    )


def _resolve_employee_by_no(
    host: str,
    employee_no: str,
    cookie: str | list[str] | None,
    authorization: str | None,
) -> dict[str, Any]:
    lookup_errors: list[dict[str, Any]] = []
    search_result = _resolve_employee_by_search(host, employee_no, cookie, authorization)
    if search_result.get("ok"):
        return search_result
    lookup_errors.append(search_result)

    current = _current_employee(host, cookie, authorization)
    if current.get("ok"):
        current_no = str(current.get("employeeNo") or "").strip().lower()
        requested_no = employee_no.strip().lower()
        if current_no == requested_no:
            return {
                "ok": True,
                "employeeId": current["employeeId"],
                "employeeNo": current.get("employeeNo") or employee_no,
                "realName": current.get("realName"),
                "sourceEndpoint": PATH_CURRENT_USER,
                "lookupWarnings": lookup_errors,
                "warning": "通用员工搜索未命中，已回退到当前登录用户身份。若要查非本人，请直接传 employeeId。",
            }

    return {
        "ok": False,
        "error": f"按员工工号 {employee_no} 查询员工失败",
        "notFoundEmployeeNos": [employee_no],
        "lookupErrors": lookup_errors,
    }


def _resolve_employee_by_search(
    host: str,
    employee_no: str,
    cookie: str | list[str] | None,
    authorization: str | None,
) -> dict[str, Any]:
    requests = [
        (PATH_ROSTER_LIST, {"rosterType": 1, "page": 1, "pageSize": 20, "keywords": employee_no}),
        (PATH_ROSTER_LIST, {"rosterType": 2, "page": 1, "pageSize": 20, "keywords": employee_no}),
        (PATH_EMPLOYEE_LIST, {"keyword": employee_no, "page": 1, "pageSize": 20}),
        (PATH_EMPLOYEE_LIST, {"keywords": employee_no, "page": 1, "pageSize": 20}),
        (PATH_EMPLOYEE_SEARCH, {"keywords": employee_no, "page": 1, "pageIndex": 1, "pageSize": 20}),
        (PATH_EMPLOYEE_SEARCH, {"keyword": employee_no, "searchText": employee_no, "page": 1, "pageIndex": 1, "pageSize": 20}),
    ]
    errors: list[dict[str, Any]] = []
    requested_no = employee_no.strip().lower()
    auth_errors: list[dict[str, Any]] = []
    for path, payload in requests:
        result = _extract_data(_post_json(host, path, payload, cookie=cookie, authorization=authorization))
        if not result.get("ok"):
            error = {"sourceEndpoint": path, "payload": payload, "raw": result}
            errors.append(error)
            if _is_auth_context_error(result):
                auth_errors.append(error)
            continue
        for item in _iter_dicts(result.get("data")):
            candidate_no = _pick_text(item, ("employeeNo", "employee_no", "jobEmployeeNo", "job_employee_no", "job-employee_no"))
            if candidate_no and candidate_no.strip().lower() != requested_no:
                continue
            employee_id = _pick_employee_id(item)
            if employee_id is None:
                continue
            return {
                "ok": True,
                "employeeId": employee_id,
                "employeeNo": candidate_no or employee_no,
                "realName": _pick_text(item, ("realName", "realname", "name")),
                "sourceEndpoint": path,
            }
        errors.append({"sourceEndpoint": path, "payload": payload, "raw": result, "error": "未在员工搜索结果中匹配到工号"})
    if auth_errors and len(auth_errors) == len([error for error in errors if error.get("raw")]):
        return {
            "ok": False,
            "error": "员工解析失败：当前 cookie/登录态无法在员工搜索接口中获取用户信息。请在百炼工具参数中传入有效的 Moka 登录 Cookie，或直接传 employeeId。",
            "sourceEndpoint": "employee_resolver",
            "authContextError": True,
            "lookupErrors": errors,
        }
    return {"ok": False, "error": "员工搜索接口未根据工号查询到员工", "sourceEndpoint": "employee_resolver", "lookupErrors": errors}


def _resolve_employee_by_business_search(
    host: str,
    employee_no: str,
    cookie: str | list[str] | None,
    authorization: str | None,
) -> dict[str, Any]:
    """Public resolver used by business tools after visibility is confirmed."""

    return _resolve_employee_by_search(host, employee_no, cookie, authorization)


def _resolve_employee_id(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    employee_id: int | None = None,
    employee_no: str | None = None,
) -> dict[str, Any]:
    if employee_id is not None:
        return {"ok": True, "employeeId": int(employee_id), "employeeNo": employee_no}
    if employee_no:
        return _resolve_employee_by_no(host, employee_no, cookie=cookie, authorization=authorization)
    current_employee_id = _resolve_current_employee_id(host, cookie, authorization)
    if current_employee_id is not None:
        return {"ok": True, "employeeId": current_employee_id, "sourceEndpoint": PATH_CURRENT_USER}
    return {"ok": False, "error": "缺少 employeeId 或 employeeNo，且无法从当前登录态解析当前员工。"}


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    return str(value)


def _iter_dicts(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_iter_dicts(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_iter_dicts(child))
    return found


def _compact_self_service_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: item.get(key)
        for key in ("id", "title", "name", "sourceType", "sourceId", "selfServiceType", "flowTemplateType", "canChoseBySelf", "platform", "iconUrl", "appUrl")
        if key in item
    }


def _query_self_service_sources(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    keyword: str | None = None,
) -> dict[str, Any]:
    calls: list[dict[str, Any]] = []
    endpoints = [
        ("mobileList", "POST", PATH_SELF_SERVICE_MOBILE_LIST, {}),
        ("homeList", "POST", PATH_SELF_SERVICE_HOME_LIST, {"pageNum": 1, "pageSize": 200, "keyword": keyword} if keyword else {"pageNum": 1, "pageSize": 200}),
        ("commonUse", "POST", PATH_SELF_SERVICE_COMMON_USE, {"pageNum": 1, "pageSize": 200, "keyword": keyword} if keyword else {"pageNum": 1, "pageSize": 200}),
    ]
    for name, method, path, payload in endpoints:
        raw = _request_json(method, host, path, payload=payload, cookie=cookie, authorization=authorization)
        extracted = _extract_data(raw)
        calls.append({"name": name, "path": path, "ok": extracted.get("ok"), "data": extracted.get("data"), "error": extracted.get("error")})

    if not any(call.get("ok") for call in calls):
        return {"ok": False, "error": "员工自助配置接口均调用失败。", "calls": calls}

    items: list[dict[str, Any]] = []
    for call in calls:
        if not call.get("ok"):
            continue
        for item in _iter_dicts(call.get("data")):
            compact = _compact_self_service_item(item)
            if compact and any(key in compact for key in ("title", "name", "appUrl")):
                compact["source"] = call["name"]
                items.append(compact)

    return {"ok": True, "items": items, "calls": calls}


def _check_capability_keywords(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    keywords: list[str],
) -> dict[str, Any]:
    sources = _query_self_service_sources(host, cookie, authorization, keyword=keywords[0] if keywords else None)
    if not sources.get("ok"):
        return sources
    matched: list[dict[str, Any]] = []
    normalized_keywords = [keyword.lower() for keyword in keywords if keyword]
    for item in sources.get("items", []):
        haystack = _flatten_text(item).lower()
        if any(keyword.lower() in haystack for keyword in normalized_keywords):
            matched.append(item)
    return {
        "ok": True,
        "visible": bool(matched),
        "keywords": keywords,
        "matchedItems": matched,
        "sourceEndpoints": [PATH_SELF_SERVICE_MOBILE_LIST, PATH_SELF_SERVICE_HOME_LIST, PATH_SELF_SERVICE_COMMON_USE],
    }


def _guarded_sensitive_query(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    keywords: list[str],
) -> dict[str, Any] | None:
    check = _check_capability_keywords(host, cookie, authorization, keywords)
    if not check.get("ok"):
        return {"ok": False, "error": "查询员工自助功能配置失败，未继续查询敏感信息。", "capabilityCheck": check}
    if not check.get("visible"):
        return {"ok": False, "error": "员工自助未开放该功能入口，未继续查询敏感信息。", "capabilityCheck": check}
    return None


def _guard_salary_query(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
) -> dict[str, Any] | None:
    return _guarded_sensitive_query(host, cookie, authorization, list(SALARY_KEYWORDS))


def _guard_business_capability(
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    capability: str,
) -> dict[str, Any] | None:
    keywords = list(BUSINESS_CAPABILITY_KEYWORDS.get(capability, (capability,)))
    check = _check_capability_keywords(host, cookie, authorization, keywords)
    if not check.get("ok"):
        return {
            "ok": False,
            "error": f"查询{BUSINESS_CAPABILITY_LABELS.get(capability, capability)}员工可见性配置失败，未继续查询业务数据。",
            "capability": capability,
            "capabilityCheck": check,
        }
    if not check.get("visible"):
        return {
            "ok": False,
            "error": f"当前员工自助未配置员工可见：{BUSINESS_CAPABILITY_LABELS.get(capability, capability)}，当前信息不可查询。",
            "capability": capability,
            "capabilityCheck": check,
        }
    return None


def _prepare_business_query(
    *,
    host: str,
    cookie: str | list[str] | None,
    authorization: str | None,
    capability: str,
    employee_id: int | None = None,
    employee_no: str | None = None,
    require_employee: bool = True,
) -> dict[str, Any]:
    if not require_employee:
        blocker = _guard_business_capability(host, cookie, authorization, capability)
        if blocker:
            return blocker
        return {"ok": True, "capability": capability}
    employee = _resolve_employee_id(host, cookie, authorization, employee_id=employee_id, employee_no=employee_no)
    if not employee.get("ok"):
        employee["capability"] = capability
        return employee
    blocker = _guard_business_capability(host, cookie, authorization, capability)
    if blocker:
        blocker["employee"] = {
            "employeeId": employee.get("employeeId"),
            "employeeNo": employee.get("employeeNo"),
            "realName": employee.get("realName"),
            "sourceEndpoint": employee.get("sourceEndpoint"),
        }
        return blocker
    employee["capability"] = capability
    return employee


def _raw_endpoint_output(
    *,
    host: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    cookie: str | list[str] | None = None,
    authorization: str | None = None,
    raw: bool = False,
    skip_capability_guard: bool = False,
) -> dict[str, Any]:
    if not skip_capability_guard:
        capability = ENDPOINT_CAPABILITIES.get(path)
        if capability:
            blocker = _guard_business_capability(host, cookie, authorization, capability)
            if blocker:
                blocker["sourceEndpoint"] = path
                return blocker
    result = _extract_data(
        _request_json(method, host, path, payload=payload, params=params, cookie=cookie, authorization=authorization)
    )
    if not result.get("ok"):
        return result
    output = {"ok": True, "data": result.get("data"), "sourceEndpoint": path}
    if raw:
        output["raw"] = result.get("raw")
    return output


def _project_colleague_basic(value: Any) -> Any:
    if isinstance(value, list):
        return [_project_colleague_basic(item) for item in value]
    if not isinstance(value, dict):
        return value
    projected: dict[str, Any] = {}
    for key, item in value.items():
        if key in COLLEAGUE_BASIC_KEYS:
            projected[key] = item
        elif isinstance(item, (dict, list)):
            nested = _project_colleague_basic(item)
            if nested not in ({}, []):
                projected[key] = nested
    return projected


@mcp.tool()
def query_current_user(
    entId: int,
    buId: int,
    cookie: str,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前 Cookie 对应的 Moka 登录用户/员工身份。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    return _raw_endpoint_output(
        host=host or CONFIG.host,
        method="POST",
        path=PATH_CURRENT_USER,
        payload={},
        cookie=cookie,
        authorization=authorization,
        raw=raw,
    ) | {"request": {"entId": int(entId), "buId": int(buId)}}


@mcp.tool()
def diagnose_moka_session(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    capability: str | None = None,
    keyword: str | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """诊断当前 Cookie 是否能支撑员工自助查询：登录态、员工身份、工号解析、自助功能可见性。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing

    resolved_host = host or CONFIG.host
    current_user = _raw_endpoint_output(
        host=resolved_host,
        method="POST",
        path=PATH_CURRENT_USER,
        payload={},
        cookie=cookie,
        authorization=authorization,
        raw=raw,
    )
    current_employee = _current_employee(resolved_host, cookie, authorization)
    employee_lookup: dict[str, Any] | None = None
    if employeeNo:
        employee_lookup = _resolve_employee_by_business_search(resolved_host, employeeNo, cookie, authorization)

    capability_check: dict[str, Any] | None = None
    resolved_keywords: list[str] = []
    if capability:
        resolved_keywords = list(BUSINESS_CAPABILITY_KEYWORDS.get(capability, (capability,)))
    elif keyword:
        resolved_keywords = [keyword]
    if resolved_keywords:
        capability_check = _check_capability_keywords(resolved_host, cookie, authorization, resolved_keywords)

    blockers: list[str] = []
    if current_user.get("authContextError"):
        blockers.append("cookie 无法识别当前用户，请重新复制 core.mokahr.com 请求头中的完整 Cookie。")
    if current_employee.get("employeeContextError") or not current_employee.get("ok"):
        blockers.append("当前登录态无法解析当前员工身份，请确认账号已绑定员工档案，且 Cookie 来自员工端已登录账号。")
    if employee_lookup and not employee_lookup.get("ok"):
        blockers.append("指定 employeeNo 未能解析为 employeeId，请确认工号、账号权限或改传可查询范围内的员工。")
    if capability_check and capability_check.get("ok") and not capability_check.get("visible"):
        blockers.append("员工自助配置未开放该业务入口，MCP 应阻断对应敏感信息查询。")
    if capability_check and not capability_check.get("ok"):
        blockers.append("员工自助配置查询失败，MCP 不应继续查询敏感信息。")

    output: dict[str, Any] = {
        "ok": not blockers,
        "diagnosis": "可继续调用业务查询工具。" if not blockers else "当前会话不满足稳定查询条件，请先处理 blockers。",
        "blockers": blockers,
        "request": {
            "entId": int(entId),
            "buId": int(buId),
            "employeeNo": employeeNo,
            "capability": capability,
            "keyword": keyword,
        },
        "currentUser": current_user,
        "currentEmployee": current_employee,
    }
    if employee_lookup is not None:
        output["employeeLookup"] = employee_lookup
    if capability_check is not None:
        output["capabilityCheck"] = capability_check
    if not raw:
        for key in ("currentUser", "currentEmployee", "employeeLookup", "capabilityCheck"):
            value = output.get(key)
            if isinstance(value, dict):
                value.pop("raw", None)
    return output



@mcp.tool()
def check_employee_self_service_capability(
    entId: int,
    buId: int,
    cookie: str,
    keyword: str | None = None,
    keywords: list[str] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工自助服务里某个入口/功能是否可见，例如“我的薪酬”“社保公积金”“假期”。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_keywords = [item for item in (keywords or []) if item]
    if keyword:
        resolved_keywords.insert(0, keyword)
    resolved_host = host or CONFIG.host
    sources = _query_self_service_sources(resolved_host, cookie, authorization, keyword=keyword)
    if not resolved_keywords:
        output = {
            "ok": True,
            "items": sources.get("items", []),
            "sourceEndpoints": [PATH_SELF_SERVICE_MOBILE_LIST, PATH_SELF_SERVICE_HOME_LIST, PATH_SELF_SERVICE_COMMON_USE],
            "request": {"entId": int(entId), "buId": int(buId)},
        }
        if raw:
            output["rawCalls"] = sources.get("calls")
        return output
    check = _check_capability_keywords(resolved_host, cookie, authorization, resolved_keywords)
    check["request"] = {"entId": int(entId), "buId": int(buId), "keywords": resolved_keywords}
    if raw:
        check["allItems"] = sources.get("items", [])
    return check


@mcp.tool()
def resolve_employee_id_by_no(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """通用地将员工工号解析为 employeeId。业务查询工具会先使用同一套解析逻辑。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    result = _resolve_employee_by_business_search(resolved_host, employeeNo, cookie, authorization)
    if not result.get("ok"):
        return result
    output = {
        "ok": True,
        "employeeId": result.get("employeeId"),
        "employeeNo": result.get("employeeNo") or employeeNo,
        "realName": result.get("realName"),
        "sourceEndpoint": result.get("sourceEndpoint"),
        "request": {"entId": int(entId), "buId": int(buId), "employeeNo": employeeNo},
    }
    if raw:
        output["raw"] = result
    return output


@mcp.tool()
def query_leave_balance(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeNos: list[str] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """按员工工号查询假期余额。单个员工传 employeeNo，多个员工传 employeeNos。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_employee_nos: list[str] = []
    if employeeNo:
        resolved_employee_nos.append(str(employeeNo).strip())
    if employeeNos:
        resolved_employee_nos.extend(str(employee_no).strip() for employee_no in employeeNos if str(employee_no).strip())
    if not resolved_employee_nos:
        return {"ok": False, "error": "缺少员工工号；单个员工传 employeeNo，多个员工传 employeeNos"}

    resolved_host = host or CONFIG.host
    resolved_employees: list[dict[str, Any]] = []
    for employee_no in resolved_employee_nos:
        employee = _resolve_employee_by_business_search(resolved_host, employee_no, cookie, authorization)
        if not employee.get("ok"):
            return employee
        resolved_employees.append(employee)
    blocker = _guard_business_capability(resolved_host, cookie, authorization, "attendance")
    if blocker:
        blocker["employees"] = [
            {
                "employeeId": employee.get("employeeId"),
                "employeeNo": employee.get("employeeNo"),
                "realName": employee.get("realName"),
                "sourceEndpoint": employee.get("sourceEndpoint"),
            }
            for employee in resolved_employees
        ]
        blocker["sourceEndpoint"] = PATH_LEAVE_BALANCE
        return blocker
    all_records: list[dict[str, Any]] = []
    all_columns: list[dict[str, Any]] = []
    not_found: list[str] = []
    raw_results: dict[str, Any] = {}

    for employee_no in resolved_employee_nos:
        result = _query_pc_balance_by_employee_no(resolved_host, employee_no, cookie=cookie, authorization=authorization)
        if not result.get("ok"):
            return {"ok": False, "error": f"查询员工工号 {employee_no} 的假期余额失败", "raw": result}
        mapped = _map_balance_records(result.get("data"), [employee_no])
        if not mapped.get("ok"):
            return mapped
        all_records.extend(mapped.get("records", []))
        if not all_columns:
            all_columns = mapped.get("columns", [])
        not_found.extend(mapped.get("notFoundEmployeeNos", []))
        if raw:
            raw_results[employee_no] = result.get("data")

    output = {
        "ok": not not_found,
        "leaveBalances": {"columns": all_columns, "records": all_records, "total": len(all_records)},
        "sourceEndpoint": PATH_LEAVE_BALANCE,
        "request": {"entId": int(entId), "buId": int(buId), "employeeNos": resolved_employee_nos},
        "notFoundEmployeeNos": not_found,
        "host": resolved_host,
        "fieldMeaning": {
            "columns": "假期类型列，absId 与假期名称映射。",
            "records": "员工假期余额列表。",
            "absAccountInfos": "该员工各假期类型的余额。",
            "availableBalanceText": "可用余额展示文本。",
            "unitText": "余额单位展示文本。",
        },
    }
    if raw:
        output["rawData"] = raw_results
    return output


@mcp.tool()
def query_leave_account_detail(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    absId: int | None = None,
    leaveRuleId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工某个假种的额度详情。absId/leaveRuleId 按页面接口实际需要传入。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "absId": absId, "leaveRuleId": leaveRuleId}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_LEAVE_ACCOUNT_DETAIL, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_leave_records(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    page: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """分页查询员工请假记录。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"page": page, "pageSize": pageSize, "employeeId": employee["employeeId"], "employeeIdList": [employee["employeeId"]]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_LEAVE_RECORDS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_leave_send_records(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    page: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工发假记录。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"page": page, "pageSize": pageSize, "employeeId": employee["employeeId"]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_LEAVE_SEND_RECORDS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_leave_use_records(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    page: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工假期使用明细。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"page": page, "pageSize": pageSize, "employeeId": employee["employeeId"]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_LEAVE_USE_RECORDS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_employee_leave_overview(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工假期账户总览。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    return _raw_endpoint_output(
        host=resolved_host,
        method="POST",
        path=PATH_EMP_ACCOUNT_INFO,
        payload={"employeeId": employee["employeeId"]},
        cookie=cookie,
        authorization=authorization,
        raw=raw,
    )


@mcp.tool()
def query_available_leave_types(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工可申请的假期类型及余额。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    query = _merge_payload({"employeeId": employee["employeeId"]}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_LEAVE_TYPES, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_clock_records(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    startDate: str | None = None,
    endDate: str | None = None,
    page: int = 1,
    pageSize: int = 31,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工打卡记录。日期字段可传 startDate/endDate，复杂筛选放 payload。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"page": page, "pageSize": pageSize, "employeeId": employee["employeeId"], "startDate": startDate, "endDate": endDate}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_CLOCK_RECORDS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_attendance_calendar(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    date: str | None = None,
    month: str | None = None,
    year: int | None = None,
    monthNumber: int | None = None,
    clockInDate: str | None = None,
    useCurrentMonthWhenMissing: bool = False,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工考勤日历。传 clockInDate/date 查询某天详情；传 year+monthNumber 或 month=YYYY-MM 查询月列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    resolved_date = clockInDate or date
    if resolved_date:
        path = PATH_ATTENDANCE_CALENDAR_DETAIL
        body = _merge_payload({"employeeId": employee["employeeId"], "clockInDate": resolved_date}, payload)
        body = {key: value for key, value in body.items() if value is not None}
        return _raw_endpoint_output(host=resolved_host, method="POST", path=path, payload=body, cookie=cookie, authorization=authorization, raw=raw)

    parsed_year, parsed_month = _parse_year_month(month)
    resolved_year = year or parsed_year
    resolved_month = monthNumber or parsed_month
    if (resolved_year is None or resolved_month is None) and useCurrentMonthWhenMissing:
        resolved_year, resolved_month = _today_year_month()
    if resolved_year is None or resolved_month is None:
        return _missing_params_error(
            tool="query_attendance_calendar",
            missing=["year", "monthNumber"],
            message="查询月出勤日历需要明确年份和月份。请补充 year 和 monthNumber，或传 month=YYYY-MM；如果要查某一天，请传 clockInDate/date=YYYY-MM-DD。",
            examples=[
                {"year": 2026, "monthNumber": 5},
                {"month": "2026-05"},
                {"clockInDate": "2026-05-12"},
            ],
        )

    path = PATH_ATTENDANCE_CALENDAR_LIST
    body = _merge_payload({"employeeId": employee["employeeId"], "year": resolved_year, "month": resolved_month, "inApproval": False}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=path, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_profile_attendance_calendar(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工档案页考勤日历。复杂 query 参数可放 params。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    query = _merge_payload({"employeeId": employee["employeeId"]}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_ATTENDANCE_CALENDAR_PROFILE, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def search_colleague_basic(
    entId: int,
    buId: int,
    cookie: str,
    keyword: str,
    page: int = 1,
    pageSize: int = 20,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """搜索同事基础信息，只返回姓名、工号、部门、职位、办公地、头像、直属上级等基础字段。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    body = {"keyword": keyword, "searchText": keyword, "page": page, "pageIndex": page, "pageSize": pageSize}
    result = _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_EMPLOYEE_SEARCH, payload=body, cookie=cookie, authorization=authorization, raw=True)
    if not result.get("ok"):
        result = _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_EMPLOYEE_LIST, payload=body, cookie=cookie, authorization=authorization, raw=True)
    if not result.get("ok"):
        return result
    output = {"ok": True, "data": _project_colleague_basic(result.get("data")), "sourceEndpoint": result.get("sourceEndpoint")}
    if raw:
        output["raw"] = result.get("raw")
    return output


@mcp.tool()
def query_mobile_staff_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询移动端员工详情。查同事时会收口为基础字段。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"]}, payload)
    result = _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_ORG_STAFF_INFO, payload=body, cookie=cookie, authorization=authorization, raw=True)
    if not result.get("ok"):
        return result
    output = {"ok": True, "data": _project_colleague_basic(result.get("data")), "sourceEndpoint": PATH_ORG_STAFF_INFO}
    if raw:
        output["raw"] = result.get("raw")
    return output


@mcp.tool()
def query_my_profile(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前员工个人档案详情。默认从 cookie 解析当前员工，也可显式传 employeeNo/employeeId。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _prepare_business_query(host=resolved_host, cookie=cookie, authorization=authorization, capability="profile", employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "employeeIds": [employee["employeeId"]]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_PROFILE_DETAIL, payload=body, cookie=cookie, authorization=authorization, raw=raw, skip_capability_guard=True)


@mcp.tool()
def query_my_staff_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前员工个人信息 tab。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _prepare_business_query(host=resolved_host, cookie=cookie, authorization=authorization, capability="profile", employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "moduleType": 1, "tabKey": "staffInfo"}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_STAFF_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw, skip_capability_guard=True)


@mcp.tool()
def query_my_job_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前员工任职信息 tab。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _prepare_business_query(host=resolved_host, cookie=cookie, authorization=authorization, capability="profile", employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "moduleType": 2, "tabKey": "jobInfo"}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_JOB_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw, skip_capability_guard=True)


@mcp.tool()
def query_employee_basic_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工基础信息接口。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_EMPLOYEE_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_pending_approvals(
    entId: int,
    buId: int,
    cookie: str,
    page: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前登录用户的待办审批列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    body = _merge_payload({"pageNum": page, "page": page, "pageSize": pageSize}, payload)
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_PENDING_APPROVALS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_approval_detail(
    entId: int,
    buId: int,
    cookie: str,
    instanceId: str | int | None = None,
    flowInstId: str | int | None = None,
    taskId: str | int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询审批详情。传 instanceId/flowInstId/taskId 或通过 payload 透传页面参数。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    body = _merge_payload({"instanceId": instanceId, "flowInstId": flowInstId, "taskId": taskId}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    if not body:
        return {"ok": False, "error": "缺少审批实例参数；请传 instanceId、flowInstId、taskId 或 payload。"}
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_APPROVAL_DETAIL, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_approval_flow_detail(
    entId: int,
    buId: int,
    cookie: str,
    payload: dict[str, Any],
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询审批流程详情 PC 汇总接口。payload 按页面参数透传。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_FLOW_DETAIL_PC, payload=payload, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_approval_task_details(
    entId: int,
    buId: int,
    cookie: str,
    payload: dict[str, Any],
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询审批任务节点详情。payload 按页面参数透传。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_FLOW_TASK_DETAILS, payload=payload, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_approval_form_data(
    entId: int,
    buId: int,
    cookie: str,
    payload: dict[str, Any],
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询审批表单数据。payload 按页面参数透传。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_APPROVAL_FORM_DATA, payload=payload, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def search_approval_instances(
    entId: int,
    buId: int,
    cookie: str,
    payload: dict[str, Any] | None = None,
    page: int = 1,
    pageSize: int = 20,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """搜索当前用户可见的审批实例摘要。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    body = _merge_payload({"pageNum": page, "page": page, "pageSize": pageSize}, payload)
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_FLOWINST_SEARCH_BRIEF, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def list_approval_instances(
    entId: int,
    buId: int,
    cookie: str,
    payload: dict[str, Any] | None = None,
    page: int = 1,
    pageSize: int = 20,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询当前用户可见的审批实例列表摘要。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    body = _merge_payload({"pageNum": page, "page": page, "pageSize": pageSize}, payload)
    return _raw_endpoint_output(host=host or CONFIG.host, method="POST", path=PATH_FLOWINST_LIST_BRIEF, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def list_candidate_employees(
    entId: int,
    buId: int,
    cookie: str,
    keyword: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询审批候选员工列表，只返回同事基础字段。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    query = _merge_payload({"keyword": keyword}, params)
    result = _raw_endpoint_output(host=host or CONFIG.host, method="GET", path=PATH_CANDIDATE_EMPLOYEE_LIST, params=query, cookie=cookie, authorization=authorization, raw=True)
    if not result.get("ok"):
        return result
    output = {"ok": True, "data": _project_colleague_basic(result.get("data")), "sourceEndpoint": PATH_CANDIDATE_EMPLOYEE_LIST}
    if raw:
        output["raw"] = result.get("raw")
    return output


@mcp.tool()
def query_my_payroll_list(
    entId: int,
    buId: int,
    cookie: str,
    totalMonth: int | None = None,
    thisYear: bool | None = None,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询当前员工工资条列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid, "totalMonth": totalMonth, "thisYear": thisYear}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_MY_PAYROLL_LIST, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_my_salary_info(
    entId: int,
    buId: int,
    cookie: str,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询当前员工薪资信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_MY_SALARY_INFO, params=params, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_my_salary_available_items(
    entId: int,
    buId: int,
    cookie: str,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询我的薪酬内可用功能项。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYROLL_AVAILABLE_ITEM, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_payslip_detail(
    entId: int,
    buId: int,
    cookie: str,
    payrollDetailId: int | None = None,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询当前员工工资条详情。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid, "payrollDetailId": payrollDetailId}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYSLIP_DETAIL, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_payslip_employee_info(
    entId: int,
    buId: int,
    cookie: str,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询工资条员工基础信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYSLIP_EMP_INFO, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_payslip_multi_info(
    entId: int,
    buId: int,
    cookie: str,
    payrollDetailId: int | None = None,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询工资单当月多笔信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid, "payrollDetailId": payrollDetailId}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYROLL_EMP_MULTI_INFO, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_payslip_hidden_status(
    entId: int,
    buId: int,
    cookie: str,
    uuid: str | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询工资单数字隐藏状态。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"uuid": uuid}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYROLL_EMP_PASS_HIDDEN, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_my_salary_display_config(
    entId: int,
    buId: int,
    cookie: str,
    scene: str | int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询我的薪酬展示配置。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"scene": scene}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_PAYROLL_EMP_DISPLAY_CONFIG, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_salary_archive_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询员工薪资档案详情。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    query = _merge_payload({"id": employee["employeeId"]}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_SALARY_ARCHIVES_INFO, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_salary_archive_change_history(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询员工薪资档案变更历史。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    query = _merge_payload({"employeeId": employee["employeeId"]}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_SALARY_ARCHIVES_FIELD_CHANGE, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_salary_employee_info(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询员工薪资相关基础信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_SALARY_EMPLOYEE_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_personal_tax_reports(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    salaryYearAndMonth: str | None = None,
    taxBelong: str | None = None,
    pageNumber: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询员工个税人员报送/个税记录列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload(
        {
            "salaryYearAndMonth": salaryYearAndMonth,
            "taxBelong": taxBelong,
            "employeeIdList": [employee["employeeId"]],
            "pageNumber": pageNumber,
            "pageSize": pageSize,
        },
        payload,
    )
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_TAX_STAFF_REPORT_SEARCH, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_personal_tax_search_factors(
    entId: int,
    buId: int,
    cookie: str,
    salaryYearAndMonth: str,
    taxBelong: str,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询个税筛选项。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"salaryYearAndMonth": salaryYearAndMonth, "taxBelong": taxBelong}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_TAX_STAFF_REPORT_SEARCH_FACTOR, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_annual_bonus_tax_detail(
    entId: int,
    buId: int,
    cookie: str,
    id: str | int,
    declarationId: str | int,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询全年一次性奖金个税明细。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"id": id, "declarationId": declarationId}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_TAX_BONUS_WHOLE_YEAR_INCOME, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_equity_incentive_tax_detail(
    entId: int,
    buId: int,
    cookie: str,
    id: str | int,
    declarationId: str | int,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询股权激励收入个税明细。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    query = _merge_payload({"id": id, "declarationId": declarationId}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_TAX_EQUITY_INCENTIVE_INCOME, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_incentive_activity_list(
    entId: int,
    buId: int,
    cookie: str,
    keyword: str | None = None,
    status: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询奖金/调薪激励活动列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    body = _merge_payload({"pageNum": pageNum, "pageSize": pageSize, "keyword": keyword, "status": status}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_ACTIVITY_LIST, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_incentive_activity_info(
    entId: int,
    buId: int,
    cookie: str,
    activityId: str | int,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询奖金/调薪激励活动详情。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    body = _merge_payload({"activityId": activityId}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_ACTIVITY_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_incentive_employee_info(
    entId: int,
    buId: int,
    cookie: str,
    activityId: str | int,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询奖金/调薪活动中的员工信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"activityId": activityId, "employeeId": employee["employeeId"]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_EMPLOYEE_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_adjust_salary_detail(
    entId: int,
    buId: int,
    cookie: str,
    activityId: str | int,
    type: str | int,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    params: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询员工调薪明细。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    query = _merge_payload({"activityId": activityId, "employeeId": employee["employeeId"], "type": type}, params)
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_INCENTIVE_EMPLOYEE_ADJUST_DETAIL, params=query, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_incentive_employee_growth_records(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    activityId: str | int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询激励/调薪员工成长记录。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"activityId": activityId, "employeeId": employee["employeeId"]}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_EMPLOYEE_GROWTH_RECORDS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_adjust_salary_chart_tags(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    activityId: str | int | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询调薪对比图标签。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"activityId": activityId, "employeeId": employee["employeeId"]}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_ADJUST_CHART_TAGS, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_adjust_salary_chart(
    entId: int,
    buId: int,
    cookie: str,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    activityId: str | int | None = None,
    tag: str | None = None,
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查“我的薪酬”入口，再查询调薪对比图数据。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guard_salary_query(resolved_host, cookie, authorization)
    if blocker:
        return blocker
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"activityId": activityId, "employeeId": employee["employeeId"], "tag": tag}, payload)
    body = {key: value for key, value in body.items() if value is not None}
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_INCENTIVE_ADJUST_CHART, payload=body, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_social_fund_file_info(
    entId: int,
    buId: int,
    cookie: str,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查员工自助是否开放社保/公积金/福利入口，再查询当前员工社保公积金档案信息。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guarded_sensitive_query(resolved_host, cookie, authorization, list(SOCIAL_FUND_KEYWORDS))
    if blocker:
        return blocker
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_WELFARE_FILE_INFO, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_social_fund_history_pay(
    entId: int,
    buId: int,
    cookie: str,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查员工自助是否开放社保/公积金/福利入口，再查询当前员工社保公积金缴纳记录。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guarded_sensitive_query(resolved_host, cookie, authorization, list(SOCIAL_FUND_KEYWORDS))
    if blocker:
        return blocker
    return _raw_endpoint_output(host=resolved_host, method="GET", path=PATH_WELFARE_HISTORY_PAY, cookie=cookie, authorization=authorization, raw=raw)


@mcp.tool()
def query_social_fund_history_pay_detail(
    entId: int,
    buId: int,
    cookie: str,
    detailNumber: int,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """先检查员工自助是否开放社保/公积金/福利入口，再查询当前员工某条社保公积金缴纳明细。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    blocker = _guarded_sensitive_query(resolved_host, cookie, authorization, list(SOCIAL_FUND_KEYWORDS))
    if blocker:
        return blocker
    return _raw_endpoint_output(
        host=resolved_host,
        method="GET",
        path=PATH_WELFARE_HISTORY_PAY_DETAIL,
        params={"detailNumber": detailNumber},
        cookie=cookie,
        authorization=authorization,
        raw=raw,
    )


@mcp.tool()
def internal_query_leave_balance(
    employeeNo: str,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询假期余额。鉴权从 MCP 启动参数读取，不需要 apiCode/privateKey/apiKey。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_leave_balance(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_leave_records(
    employeeNo: str,
    page: int = 1,
    pageSize: int = 20,
    startDate: str | None = None,
    endDate: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询请假记录。可传 startDate/endDate。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    payload = {key: value for key, value in {"startDate": startDate, "endDate": endDate}.items() if value is not None}
    return query_leave_records(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        page=page,
        pageSize=pageSize,
        payload=payload or None,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_clock_records(
    employeeNo: str,
    startDate: str | None = None,
    endDate: str | None = None,
    page: int = 1,
    pageSize: int = 31,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询打卡记录。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_clock_records(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        startDate=startDate,
        endDate=endDate,
        page=page,
        pageSize=pageSize,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_attendance_calendar(
    employeeNo: str,
    date: str | None = None,
    month: str | None = None,
    year: int | None = None,
    monthNumber: int | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询考勤日历。传 date=YYYY-MM-DD 查单日，或 month=YYYY-MM 查整月。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_attendance_calendar(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        date=date,
        month=month,
        year=year,
        monthNumber=monthNumber,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_my_profile(
    employeeNo: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询员工个人档案。employeeNo 为空时按当前登录态解析当前员工。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_my_profile(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_my_payroll_list(
    totalMonth: int | None = None,
    thisYear: bool | None = None,
    uuid: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询当前员工工资条列表，先检查我的薪酬入口。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_my_payroll_list(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        totalMonth=totalMonth,
        thisYear=thisYear,
        uuid=uuid,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_payslip_detail(
    payrollDetailId: int | None = None,
    uuid: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询当前员工工资条详情，先检查我的薪酬入口。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_payslip_detail(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        payrollDetailId=payrollDetailId,
        uuid=uuid,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_salary_archive(
    employeeNo: str,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询薪资档案，先检查我的薪酬入口。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_salary_archive_info(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_personal_tax(
    employeeNo: str,
    salaryYearAndMonth: str | None = None,
    taxBelong: str | None = None,
    pageNumber: int = 1,
    pageSize: int = 20,
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询个税记录，先检查我的薪酬入口。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_personal_tax_reports(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        employeeNo=employeeNo,
        salaryYearAndMonth=salaryYearAndMonth,
        taxBelong=taxBelong,
        pageNumber=pageNumber,
        pageSize=pageSize,
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def internal_query_social_fund_file_info(
    raw: bool = False,
) -> dict[str, Any]:
    """内部接口查询当前员工社保公积金档案，先检查社保公积金入口。"""

    ctx = _internal_context()
    if not ctx.get("ok"):
        return ctx
    return query_social_fund_file_info(
        entId=ctx["entId"],
        buId=ctx["buId"],
        cookie=ctx.get("cookie") or "",
        host=ctx["host"],
        authorization=ctx.get("authorization"),
        raw=raw,
    )


@mcp.tool()
def check_salary_self_service_enabled(
    entId: int,
    buId: int,
    cookie: str,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """检查员工自助是否开放“我的薪酬/工资条/薪资”入口。当前只做配置检查，不直接查询工资条数据。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    result = _check_capability_keywords(host or CONFIG.host, cookie, authorization, list(SALARY_KEYWORDS))
    if not raw:
        result.pop("allItems", None)
    result["request"] = {"entId": int(entId), "buId": int(buId), "keywords": list(SALARY_KEYWORDS)}
    return result


def _openapi_payload(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}


def _openapi_employee_filter(employee_no: str | None = None, employee_id: int | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if employee_id is not None:
        payload["employeeIdList"] = [employee_id]
    if employee_no:
        payload["employeeNoList"] = [employee_no]
    return payload


def _openapi_unverified_path_warning(path: str, label: str) -> dict[str, Any]:
    return {
        "openapiPathVerification": "unverified",
        "warning": f"{label} 的 OpenAPI 路径来自当前资料整理，未使用真实 OpenAPI 凭证做端到端验证；如果返回 404/签名外错误，请以 people.mokahr.com 文档对应章节的请求地址为准。",
        "path": path,
    }


@mcp.tool()
def call_moka_openapi(
    path: str,
    payload: dict[str, Any] | None = None,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """通用调用 Moka OpenAPI。用于官方文档已有但 MCP 尚未封装成专用工具的接口。"""

    return _call_openapi(
        path=path,
        payload=payload or {},
        entCode=entCode,
        apiCode=apiCode,
        apiKey=apiKey,
        privateKey=privateKey,
        userName=userName,
        openapiHost=openapiHost,
        raw=raw,
    )


@mcp.tool()
def openapi_query_leave_balance(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询假期余额。优先传 employeeNo；不需要 cookie。"""

    if not employeeNo and employeeId is None:
        return _missing_params_error("openapi_query_leave_balance", ["employeeNo"], "缺少员工标识，建议传 employeeNo。")
    path = "/api-platform/hcm/oapi/v2/absence/account/search"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "假期余额查询"))
    return result


@mcp.tool()
def openapi_query_leave_records(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    startDate: str | None = None,
    endDate: str | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询请假记录；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v2/absence/attendance/leave/records"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), startDate=startDate, endDate=endDate, pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "请假记录查询"))
    return result


@mcp.tool()
def openapi_query_employee_project_groups(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 获取员工所属项目组数据；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/user/batch_get_emp_project"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "员工所属项目组数据"))
    return result


@mcp.tool()
def openapi_query_salary_archive(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询薪资档案；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/salary/archives"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "薪资档案查询"))
    return result


@mcp.tool()
def openapi_query_payroll_result(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    payrollMonth: str | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询工资/薪酬核算结果；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/salary/account"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), salaryYearAndMonth=payrollMonth, pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "工资/薪酬核算结果查询"))
    return result


@mcp.tool()
def openapi_query_social_fund_archive(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询社保公积金档案；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/salary/social"
    payload = _openapi_payload(**_openapi_employee_filter(employeeNo, employeeId), pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "社保公积金档案查询"))
    return result


@mcp.tool()
def openapi_query_personal_tax(
    employeeNo: str | None = None,
    employeeId: int | None = None,
    taxMonth: str | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询个税报送/个税记录；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/salary/tax/report"
    payload = _openapi_payload(employeeNo=employeeNo, employeeId=employeeId, taxMonth=taxMonth, pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "个税记录查询"))
    return result


@mcp.tool()
def openapi_query_incentive_activity(
    activityId: int | None = None,
    employeeNo: str | None = None,
    employeeId: int | None = None,
    pageNum: int = 1,
    pageSize: int = 20,
    entCode: str | None = None,
    apiCode: str | None = None,
    apiKey: str | None = None,
    privateKey: str | None = None,
    userName: str | None = None,
    openapiHost: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """OpenAPI 查询奖金/调薪激励活动或员工明细；不需要 cookie。"""

    path = "/api-platform/hcm/oapi/v1/salary/incentive/activity"
    payload = _openapi_payload(activityId=activityId, employeeNo=employeeNo, employeeId=employeeId, pageNum=pageNum, pageSize=pageSize)
    result = _call_openapi(path=path, payload=payload, entCode=entCode, apiCode=apiCode, apiKey=apiKey, privateKey=privateKey, userName=userName, openapiHost=openapiHost, raw=raw)
    result.setdefault("notice", _openapi_unverified_path_warning(path, "奖金/调薪激励活动查询"))
    return result


@mcp.tool()
def list_openapi_migration_status() -> dict[str, Any]:
    """查看当前 MCP 中内部接口迁移到 OpenAPI 的实现状态。"""

    return {
        "ok": True,
        "implementedOpenApiTools": [
            "call_moka_openapi",
            "openapi_query_leave_balance",
            "openapi_query_leave_records",
            "openapi_query_employee_project_groups",
            "openapi_query_salary_archive",
            "openapi_query_payroll_result",
            "openapi_query_social_fund_archive",
        ],
        "notFullyMigrated": [
            {"feature": "员工端自助可见性配置", "reason": "目前只找到内部员工端配置接口；OpenAPI 是否开放需以官方文档为准。"},
            {"feature": "工资条详情/隐藏状态/展示配置", "reason": "当前实现来自内部薪酬员工端接口；需补充官方 OpenAPI 请求地址后才能稳定迁移。"},
            {"feature": "个税独立查询", "reason": "官方文档中当前只在工资核算结果里包含个税字段，未确认独立个税查询 OpenAPI。"},
            {"feature": "奖金/调薪激励活动", "reason": "未在当前官方文档中确认对应只读 OpenAPI，请使用工资核算结果或薪资档案查询相关字段。"},
            {"feature": "审批待办/审批详情", "reason": "当前实现来自内部审批平台接口；需补充官方 OpenAPI 请求地址。"},
            {"feature": "当前登录用户/当前员工", "reason": "OpenAPI 是应用鉴权，不等价于 cookie 登录态，一般应改为按 employeeNo/employeeId 查询。"},
        ],
        "authRequired": ["entCode", "apiCode", "apiKey", "privateKey"],
        "authOptional": ["userName"],
        "fieldPolicy": "MCP 不做字段裁剪，默认返回 OpenAPI 响应里的完整 data。",
        "note": "OpenAPI 工具不使用 cookie。apiCode 必须传，它是 Moka People「设置-对外接口设置」里对应数据源的接口编码。不同数据源可能有不同 apiCode；如果传错或不传，Moka 网关会返回 Required String parameter 'apiCode' is not present 或鉴权失败。",
    }


OPENAPI_TOOL_NAMES = {
    "call_moka_openapi",
    "openapi_query_leave_balance",
    "openapi_query_leave_records",
    "openapi_query_employee_project_groups",
    "openapi_query_salary_archive",
    "openapi_query_payroll_result",
    "openapi_query_social_fund_archive",
    "list_openapi_migration_status",
}


INTERNAL_TOOL_NAMES = {
    "internal_query_leave_balance",
    "internal_query_leave_records",
    "internal_query_clock_records",
    "internal_query_attendance_calendar",
    "internal_query_my_profile",
    "internal_query_my_payroll_list",
    "internal_query_payslip_detail",
    "internal_query_salary_archive",
    "internal_query_personal_tax",
    "internal_query_social_fund_file_info",
}


def _expose_tools(allowed_tool_names: set[str]) -> None:
    for tool_name in list(mcp._tool_manager._tools):
        if tool_name not in allowed_tool_names:
            mcp.remove_tool(tool_name)


def main() -> None:
    _configure_from_args()
    _expose_tools(INTERNAL_TOOL_NAMES if CONFIG.tool_mode == "internal" else OPENAPI_TOOL_NAMES)
    mcp.run()


if __name__ == "__main__":
    main()
