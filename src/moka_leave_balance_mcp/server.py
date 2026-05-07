from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from typing import Any

from mcp.server.fastmcp import FastMCP

MCP_NAME = "moka-leave-balance"
DEFAULT_HOST = os.getenv("MOKA_HOST", "core.mokahr.com")
ENDPOINT_PATH = "/client/abs/account/v1/leaveInfo/listAllLeaveBalance"
SUCCESS_CODES = {200, "200", "00000", 1000000, "1000000"}

mcp = FastMCP(MCP_NAME)


def _auth_headers(cookie: str | None = None, authorization: str | None = None) -> dict[str, str]:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
    }
    cookie = cookie or os.getenv("MOKA_COOKIE")
    authorization = authorization or os.getenv("MOKA_AUTHORIZATION")
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
                data = json.loads(text)
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
    body = data if isinstance(data, dict) else {}
    balance = body.get("balance")
    legacy_balance = body.get("banlance")
    output = {
        "balance": balance if balance is not None else legacy_balance,
        "legacyField": "banlance" if legacy_balance is not None else None,
        "sourceEndpoint": ENDPOINT_PATH,
        "fieldMeaning": {
            "balance": "Map<fieldKey, label>，例如假期余额日报/月报中动态假种余额字段。",
            "legacyField": "后端 DTO 字段历史拼写为 banlance；MCP 统一输出 balance。",
        },
    }
    if raw:
        output["rawData"] = data
    return output


@mcp.tool()
def query_leave_balance(
    entId: int,
    buId: int,
    isIncludeDisable: bool = False,
    isLimited: bool | None = None,
    host: str = DEFAULT_HOST,
    cookie: str | None = None,
    authorization: str | None = None,
    raw: bool = False,
) -> dict[str, Any]:
    """查询 Moka 假期余额动态字段映射。

    底层调用 POST /client/abs/account/v1/leaveInfo/listAllLeaveBalance。
    可通过参数 cookie / authorization 显式传入认证信息；如果未传，再读取环境变量
    MOKA_COOKIE / MOKA_AUTHORIZATION。
    """

    payload: dict[str, Any] = {
        "entId": int(entId),
        "buId": int(buId),
        "isIncludeDisable": bool(isIncludeDisable),
    }
    if isLimited is not None:
        payload["isLimited"] = bool(isLimited)

    result = _extract_data(
        _post_json(
            host=host,
            path=ENDPOINT_PATH,
            payload=payload,
            cookie=cookie,
            authorization=authorization,
        )
    )
    if not result.get("ok"):
        return result

    output = _normalize_balance(result.get("data"), raw=raw)
    output.update({"ok": True, "request": payload, "host": host})
    return output


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
