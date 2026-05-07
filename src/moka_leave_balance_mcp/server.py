from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from mcp.server.fastmcp import FastMCP

MCP_NAME = "moka-leave-balance"
DEFAULT_HOST = "core.mokahr.com"
ENDPOINT_PATH = "/client/abs/account/v1/account/balance_list"
SUCCESS_CODES = {200, "200", "00000", 1000000, "1000000"}

mcp = FastMCP(MCP_NAME)


@dataclass
class ServerConfig:
    host: str = DEFAULT_HOST
    unit_by_leave_rule: bool = False
    cookie: str | None = None
    authorization: str | None = None


CONFIG = ServerConfig()


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _configure_from_args() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--unit-by-leave-rule", default=False)
    parser.add_argument("--cookie")
    parser.add_argument("--authorization")
    args, _ = parser.parse_known_args()

    CONFIG.host = args.host
    CONFIG.unit_by_leave_rule = _parse_bool(args.unit_by_leave_rule)
    CONFIG.cookie = args.cookie
    CONFIG.authorization = args.authorization


def _auth_headers(cookie: str | None = None, authorization: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }
    cookie = cookie or CONFIG.cookie
    authorization = authorization or CONFIG.authorization
    if cookie:
        headers["Cookie"] = cookie
    if authorization:
        headers["Authorization"] = authorization
    return headers


def _post_json(
    host: str,
    path: str,
    payload: dict[str, Any],
    cookie: str | None = None,
    authorization: str | None = None,
) -> dict[str, Any]:
    url = f"https://{host}{path}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url=url, data=body, method="POST")
    for key, value in _auth_headers(cookie=cookie, authorization=authorization).items():
        request.add_header(key, value)

    try:
        with urllib.request.urlopen(request, context=ssl.create_default_context(), timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                data: Any = json.loads(text)
            except json.JSONDecodeError:
                data = text
            return {"ok": True, "status": resp.status, "response": data, "url": url}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")[:2000]
        return {"ok": False, "status": exc.code, "error": str(exc), "body": error_body, "url": url}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def _extract_data(result: dict[str, Any]) -> dict[str, Any]:
    if not result.get("ok"):
        return result
    response = result.get("response")
    if isinstance(response, dict):
        code = response.get("code")
        if code in SUCCESS_CODES:
            return {"ok": True, "data": response.get("data"), "raw": response}
        return {"ok": False, "error": f"API failed: code={code}, msg={response.get('msg', '')}", "raw": response}
    return result


def _normalize_balance(data: Any, raw: bool) -> dict[str, Any]:
    output: dict[str, Any] = {
        "ok": True,
        "leaveBalances": data,
        "sourceEndpoint": ENDPOINT_PATH,
        "fieldMeaning": {
            "resultBoList": "员工假期余额列表。",
            "employeeId": "员工 ID。",
            "realName": "员工姓名。",
            "employeeNo": "员工工号。",
            "absAccountInfoList": "该员工各假期类型的余额。",
            "absName": "假期类型名称。",
            "availableBalance": "可用余额。",
            "effectedAmount": "已生效额度。",
            "unEffectedAmount": "未生效额度。",
            "usedAmount": "已使用额度。",
            "totalAmount": "总额度。",
            "unit": "余额单位，通常 1=天，2=小时。",
        },
    }
    if raw:
        output["rawData"] = data
    return output


@mcp.tool()
def query_leave_balance(
    entId: int,
    buId: int,
    employeeId: int | None = None,
    employeeIds: list[int] | None = None,
    unitByLeaveRule: bool | None = None,
    host: str | None = None,
    cookie: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询具体员工的 Moka 假期余额。

    entId、buId 必须由工具调用显式传入。单个员工传 employeeId，多个员工传
    employeeIds；启动参数不提供业务查询条件默认值。
    """

    resolved_employee_ids: list[int] = []
    if employeeId is not None:
        resolved_employee_ids.append(int(employeeId))
    if employeeIds:
        resolved_employee_ids.extend(int(employee_id) for employee_id in employeeIds)
    resolved_unit_by_leave_rule = CONFIG.unit_by_leave_rule if unitByLeaveRule is None else bool(unitByLeaveRule)
    resolved_host = host or CONFIG.host

    if not resolved_employee_ids:
        return {"ok": False, "error": "缺少员工 ID；单个员工传 employeeId，多个员工传 employeeIds"}

    payload = {
        "entId": int(entId),
        "buId": int(buId),
        "employeeIds": resolved_employee_ids,
        "unitByLeaveRule": resolved_unit_by_leave_rule,
    }
    result = _extract_data(
        _post_json(
            host=resolved_host,
            path=ENDPOINT_PATH,
            payload=payload,
            cookie=cookie,
            authorization=authorization,
        )
    )
    if not result.get("ok"):
        return result

    output = _normalize_balance(result.get("data"), raw=raw)
    output.update({"request": payload, "host": resolved_host})
    return output


def main() -> None:
    _configure_from_args()
    mcp.run()


if __name__ == "__main__":
    main()
