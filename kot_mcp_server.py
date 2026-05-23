#!/usr/bin/env python3
"""KING OF TIME WebAPI MCP サーバー

環境変数 KOT_ACCESS_TOKEN にアクセストークンを設定してください。
"""

import json
import os
import winreg
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("KING OF TIME")

BASE_URL = "https://api.kingtime.jp/v1.0"


def _get_token() -> str:
    token = os.environ.get("KOT_ACCESS_TOKEN")
    if token:
        return token
    # Store版Claude DesktopはGUIプロセスのため環境変数を引き継がない場合があるので
    # Windowsレジストリから直接読み込む
    for root, subkey in [
        (winreg.HKEY_CURRENT_USER, "Environment"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
    ]:
        try:
            with winreg.OpenKey(root, subkey) as key:
                value, _ = winreg.QueryValueEx(key, "KOT_ACCESS_TOKEN")
                if value:
                    return value
        except OSError:
            continue
    raise RuntimeError("環境変数 KOT_ACCESS_TOKEN が設定されていません")


def _headers() -> dict[str, str]:
    token = _get_token()
    if not token:
        raise RuntimeError("環境変数 KOT_ACCESS_TOKEN が設定されていません")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _call(method: str, path: str, **kwargs) -> Any:
    with httpx.Client(timeout=30.0) as client:
        r = client.request(method, f"{BASE_URL}{path}", headers=_headers(), **kwargs)
    if r.status_code == 204 or not r.content:
        return None
    data = r.json()
    if not r.is_success:
        errors = data.get("errors", []) if isinstance(data, dict) else []
        msg = "; ".join(e.get("message", "") for e in errors) or f"HTTP {r.status_code}"
        raise RuntimeError(f"KOT APIエラー ({r.status_code}): {msg}")
    return data


def _dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


# ===========================================================================
# トークン
# ===========================================================================

@mcp.tool()
def verify_token() -> str:
    """アクセストークンの有効性を確認します。"""
    token = _get_token()
    result = _call("GET", f"/tokens/{token}/available")
    return _dump(result)


# ===========================================================================
# 企業情報
# ===========================================================================

@mcp.tool()
def get_company() -> str:
    """企業（エンタープライズ）設定情報を取得します。"""
    return _dump(_call("GET", "/company"))


# ===========================================================================
# 管理者
# ===========================================================================

@mcp.tool()
def list_administrators() -> str:
    """管理者一覧を取得します。"""
    return _dump(_call("GET", "/administrators"))


# ===========================================================================
# 従業員
# ===========================================================================

@mcp.tool()
def list_employees(
    date: str = "",
    division: str = "",
    include_resigners: bool = False,
    additional_fields: str = "",
) -> str:
    """従業員一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。省略時は当日。
        division: 絞り込む所属コード。
        include_resigners: 退職者を含む場合は True。
        additional_fields: 追加フィールド (カンマ区切り)。
            指定可能値: hiredDate, birthDate, resignationDate,
                        lastNamePhonetics, firstNamePhonetics,
                        emailAddresses, allDayRegardingWorkInMinute
    """
    params: dict[str, Any] = {}
    if date:
        params["date"] = date
    if division:
        params["division"] = division
    if include_resigners:
        params["includeResigner"] = "true"
    if additional_fields:
        params["additionalFields"] = additional_fields
    return _dump(_call("GET", "/employees", params=params))


@mcp.tool()
def get_employee(employee_code: str, additional_fields: str = "") -> str:
    """特定の従業員情報を取得します。

    Args:
        employee_code: 従業員コード。
        additional_fields: 追加フィールド (カンマ区切り)。
    """
    params: dict[str, Any] = {}
    if additional_fields:
        params["additionalFields"] = additional_fields
    return _dump(_call("GET", f"/employees/{employee_code}", params=params))


# ===========================================================================
# 所属（部署）
# ===========================================================================

@mcp.tool()
def list_divisions() -> str:
    """所属（部署）一覧を取得します。"""
    return _dump(_call("GET", "/divisions"))


# ===========================================================================
# 雇用区分
# ===========================================================================

@mcp.tool()
def list_working_types() -> str:
    """雇用区分一覧を取得します。"""
    return _dump(_call("GET", "/working-types"))


# ===========================================================================
# 従業員グループ
# ===========================================================================

@mcp.tool()
def list_employee_groups() -> str:
    """従業員グループ一覧を取得します。"""
    return _dump(_call("GET", "/employee-groups"))


# ===========================================================================
# 休暇区分
# ===========================================================================

@mcp.tool()
def list_holidays() -> str:
    """休暇区分一覧を取得します。"""
    return _dump(_call("GET", "/holidays"))


# ===========================================================================
# 日別勤怠
# ===========================================================================

@mcp.tool()
def list_daily_workings(
    start: str = "",
    end: str = "",
    division: str = "",
    on_division: bool = False,
    additional_fields: str = "",
) -> str:
    """日別勤怠一覧を取得します。

    Args:
        start: 開始日 (YYYY-MM-DD)。
        end: 終了日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
        on_division: True の場合、出勤先所属で絞り込む。
        additional_fields: 追加フィールド (カンマ区切り)。
    """
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if division:
        params["division"] = division
    if on_division:
        params["ondivision"] = "true"
    if additional_fields:
        params["additionalFields"] = additional_fields
    return _dump(_call("GET", "/daily-workings", params=params))


@mcp.tool()
def get_daily_workings(
    date: str,
    division: str = "",
    on_division: bool = False,
    additional_fields: str = "",
) -> str:
    """指定日の勤怠一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
        on_division: True の場合、出勤先所属で絞り込む。
        additional_fields: 追加フィールド (カンマ区切り)。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    if on_division:
        params["ondivision"] = "true"
    if additional_fields:
        params["additionalFields"] = additional_fields
    return _dump(_call("GET", f"/daily-workings/{date}", params=params))


# ===========================================================================
# 打刻
# ===========================================================================

@mcp.tool()
def register_time_record(
    employee_key: str,
    time: str,
    date: str = "",
    code: str = "",
    division_code: str = "",
    latitude: float | None = None,
    longitude: float | None = None,
) -> str:
    """従業員の打刻を1件登録します。

    Args:
        employee_key: 従業員識別キー。
        time: 打刻時間 (HH:MM)。
        date: 対象日 (YYYY-MM-DD)。省略時は当日。
        code: 打刻区分コード。
        division_code: 出勤先所属コード。
        latitude: 緯度。
        longitude: 経度。
    """
    body: dict[str, Any] = {"time": time}
    if date:
        body["date"] = date
    if code:
        body["code"] = code
    if division_code:
        body["divisionCode"] = division_code
    if latitude is not None:
        body["latitude"] = latitude
    if longitude is not None:
        body["longitude"] = longitude
    return _dump(_call("POST", f"/daily-workings/timerecord/{employee_key}", json=body))


@mcp.tool()
def list_time_records(
    start: str = "",
    end: str = "",
    division: str = "",
) -> str:
    """打刻データ一覧を取得します。

    Args:
        start: 開始日 (YYYY-MM-DD)。
        end: 終了日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if division:
        params["division"] = division
    return _dump(_call("GET", "/daily-workings/timerecord", params=params))


@mcp.tool()
def get_time_records(date: str, division: str = "") -> str:
    """指定日の打刻データを取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/daily-workings/timerecord/{date}", params=params))


# ===========================================================================
# 日別コスト
# ===========================================================================

@mcp.tool()
def list_daily_costs(
    start: str = "",
    end: str = "",
    division: str = "",
) -> str:
    """日別コスト一覧を取得します。

    Args:
        start: 開始日 (YYYY-MM-DD)。
        end: 終了日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if division:
        params["division"] = division
    return _dump(_call("GET", "/daily-workings/cost", params=params))


@mcp.tool()
def get_daily_costs(date: str, division: str = "") -> str:
    """指定日のコストデータを取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/daily-workings/cost/{date}", params=params))


# ===========================================================================
# 月別勤怠
# ===========================================================================

@mcp.tool()
def get_monthly_workings(
    year_month: str,
    division: str = "",
    additional_fields: str = "",
) -> str:
    """月別勤怠サマリーを取得します。

    Args:
        year_month: 対象年月 (YYYY-MM)。例: 2024-06
        division: 絞り込む所属コード。
        additional_fields: 追加フィールド (カンマ区切り)。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    if additional_fields:
        params["additionalFields"] = additional_fields
    return _dump(_call("GET", f"/monthly-workings/{year_month}", params=params))


@mcp.tool()
def get_monthly_costs(year_month: str, division: str = "") -> str:
    """月別コストデータを取得します。

    Args:
        year_month: 対象年月 (YYYY-MM)。例: 2024-06
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/monthly-workings/cost/{year_month}", params=params))


@mcp.tool()
def get_monthly_remaining_holidays(
    employee_type_code: str,
    year_month: str,
) -> str:
    """月別の残余休暇を取得します。

    Args:
        employee_type_code: 雇用区分コード。
        year_month: 対象年月 (YYYY-MM)。
    """
    return _dump(
        _call("GET", f"/monthly-workings/holiday-remained/{employee_type_code}/{year_month}")
    )


@mcp.tool()
def get_yearly_holidays(employee_type_code: str, year: str) -> str:
    """年別の休暇付与・取得データを取得します。

    Args:
        employee_type_code: 雇用区分コード。
        year: 対象年 (YYYY)。
    """
    return _dump(
        _call("GET", f"/yearly-workings/holidays/{employee_type_code}/{year}")
    )


# ===========================================================================
# 日別スケジュール
# ===========================================================================

@mcp.tool()
def list_daily_schedules(
    start: str = "",
    end: str = "",
    division: str = "",
) -> str:
    """日別スケジュール一覧を取得します。

    Args:
        start: 開始日 (YYYY-MM-DD)。
        end: 終了日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if division:
        params["division"] = division
    return _dump(_call("GET", "/daily-schedules", params=params))


@mcp.tool()
def get_daily_schedules(date: str, division: str = "") -> str:
    """指定日のスケジュール一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/daily-schedules/{date}", params=params))


@mcp.tool()
def update_daily_schedule(
    employee_key: str,
    date: str,
    clock_in_schedule: str = "",
    clock_out_schedule: str = "",
    work_place_division_code: str = "",
    work_day_type_code: str = "",
    fulltime_holiday_json: str = "",
    note: str = "",
) -> str:
    """日別スケジュールを作成または更新します。

    Args:
        employee_key: 従業員識別キー。
        date: 対象日 (YYYY-MM-DD)。
        clock_in_schedule: 出勤予定時間 (HH:MM)。
        clock_out_schedule: 退勤予定時間 (HH:MM)。
        work_place_division_code: 出勤先所属コード。
        work_day_type_code: 勤務日種別コード。
        fulltime_holiday_json: 終日休暇 (JSON文字列)。例: '{"code": "1"}'
        note: 備考。
    """
    body: dict[str, Any] = {}
    if clock_in_schedule:
        body["clockInSchedule"] = clock_in_schedule
    if clock_out_schedule:
        body["clockOutSchedule"] = clock_out_schedule
    if work_place_division_code:
        body["workPlaceDivisionCode"] = work_place_division_code
    if work_day_type_code:
        body["workDayTypeCode"] = work_day_type_code
    if fulltime_holiday_json:
        body["fulltimeHoliday"] = json.loads(fulltime_holiday_json)
    if note:
        body["note"] = note
    return _dump(_call("PUT", f"/daily-schedules/{employee_key}/{date}", json=body))


@mcp.tool()
def delete_daily_schedule(employee_key: str, date: str) -> str:
    """日別スケジュールを削除します。

    Args:
        employee_key: 従業員識別キー。
        date: 対象日 (YYYY-MM-DD)。
    """
    _call("DELETE", f"/daily-schedules/{employee_key}/{date}")
    return _dump({"result": "deleted"})


@mcp.tool()
def list_daily_schedule_costs(
    start: str = "",
    end: str = "",
    division: str = "",
) -> str:
    """日別スケジュールのコスト一覧を取得します。

    Args:
        start: 開始日 (YYYY-MM-DD)。
        end: 終了日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if division:
        params["division"] = division
    return _dump(_call("GET", "/daily-schedules/cost", params=params))


@mcp.tool()
def get_monthly_schedule_costs(year_month: str, division: str = "") -> str:
    """月別スケジュールのコストデータを取得します。

    Args:
        year_month: 対象年月 (YYYY-MM)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/monthly-schedules/cost/{year_month}", params=params))


# ===========================================================================
# 申請
# ===========================================================================

@mcp.tool()
def get_schedule_requests(date: str, division: str = "") -> str:
    """スケジュール申請一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/requests/schedule/{date}", params=params))


@mcp.tool()
def get_overtime_requests(date: str, division: str = "") -> str:
    """残業申請一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/requests/overtime/{date}", params=params))


@mcp.tool()
def get_timerecord_requests(date: str, division: str = "") -> str:
    """打刻修正申請一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/requests/timerecord/{date}", params=params))


@mcp.tool()
def get_overtime_limit_requests(date: str, division: str = "") -> str:
    """時間外上限申請一覧を取得します。

    Args:
        date: 対象日 (YYYY-MM-DD)。
        division: 絞り込む所属コード。
    """
    params: dict[str, Any] = {}
    if division:
        params["division"] = division
    return _dump(_call("GET", f"/requests/overtime-limit/{date}", params=params))


if __name__ == "__main__":
    mcp.run()
