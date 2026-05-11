from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

MCP_NAME = "moka-employee-self-service"
DEFAULT_HOST = "core.mokahr.com"
SUCCESS_CODES = {0, "0", 200, "200", "00000", 1000000, "1000000"}

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

mcp = FastMCP(MCP_NAME)


@dataclass
class ServerConfig:
    host: str = DEFAULT_HOST
    cookie: str | None = None
    authorization: str | None = None


CONFIG = ServerConfig()


def _configure_from_args() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--cookie", nargs="+")
    parser.add_argument("--authorization")
    args, _ = parser.parse_known_args()

    CONFIG.host = args.host
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


def _extract_data(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return result
    response = result.get("response")
    if isinstance(response, dict):
        code = response.get("code")
        if code in SUCCESS_CODES:
            return {"ok": True, "data": response.get("data"), "raw": response}
        if code is None and ("data" in response or "success" in response):
            return {"ok": True, "data": response.get("data", response), "raw": response}
        return {"ok": False, "error": f"API failed: code={code}, msg={response.get('msg', '')}", "raw": response}
    if isinstance(response, str):
        preview = response[:500]
        if "<!DOCTYPE html" in preview or "<html" in preview:
            return {
                "ok": False,
                "error": "接口返回 HTML 页面，不是 JSON；通常表示未登录、缺少 Cookie/Authorization，或 host 没有路由到后端接口。",
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


def _require_cookie(cookie: str | list[str] | None) -> dict[str, Any] | None:
    if _normalize_cookie_arg(cookie) or CONFIG.cookie:
        return None
    return {"ok": False, "error": "缺少 cookie。该 MCP 走 Moka 员工端/PC 登录态接口，需要把当前登录用户 Cookie 作为工具参数传入。"}


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


def _resolve_current_employee_id(host: str, cookie: str | list[str] | None, authorization: str | None) -> int | None:
    result = _extract_data(_post_json(host, PATH_CURRENT_USER, {}, cookie=cookie, authorization=authorization))
    if not result.get("ok"):
        return None
    return _pick_employee_id(result.get("data"))


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
    result = _query_pc_balance_by_employee_no(host, employee_no, cookie=cookie, authorization=authorization)
    if not result.get("ok"):
        return {"ok": False, "error": f"按员工工号 {employee_no} 查询员工失败", "raw": result}
    mapped = _map_balance_records(result.get("data"), [employee_no])
    if not mapped.get("ok") or not mapped.get("records"):
        return {"ok": False, "error": "未根据员工工号查询到员工", "notFoundEmployeeNos": [employee_no], "raw": mapped}
    record = mapped["records"][0]
    return {
        "ok": True,
        "employeeId": record.get("employeeId"),
        "employeeNo": record.get("employeeNo"),
        "realName": record.get("realName"),
        "sourceEndpoint": PATH_LEAVE_BALANCE,
    }


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
) -> dict[str, Any]:
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
    payload: dict[str, Any] | None = None,
    host: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询员工考勤日历。传 date 查询某天详情，传 month 查询月列表。"""

    missing = _require_cookie(cookie)
    if missing:
        return missing
    resolved_host = host or CONFIG.host
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    path = PATH_ATTENDANCE_CALENDAR_DETAIL if date else PATH_ATTENDANCE_CALENDAR_LIST
    body = _merge_payload({"employeeId": employee["employeeId"], "date": date, "month": month}, payload)
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
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "employeeIds": [employee["employeeId"]]}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_PROFILE_DETAIL, payload=body, cookie=cookie, authorization=authorization, raw=raw)


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
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "moduleType": 1, "tabKey": "staffInfo"}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_STAFF_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


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
    employee = _resolve_employee_id(resolved_host, cookie, authorization, employee_id=employeeId, employee_no=employeeNo)
    if not employee.get("ok"):
        return employee
    body = _merge_payload({"employeeId": employee["employeeId"], "moduleType": 2, "tabKey": "jobInfo"}, payload)
    return _raw_endpoint_output(host=resolved_host, method="POST", path=PATH_JOB_INFO, payload=body, cookie=cookie, authorization=authorization, raw=raw)


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


def main() -> None:
    _configure_from_args()
    mcp.run()


if __name__ == "__main__":
    main()
