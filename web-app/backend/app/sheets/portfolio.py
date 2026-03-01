from app.sheets.client import get_sheet
from app.sheets.utils import to_float, to_float_or_none


def fetch_portfolio() -> list[dict]:
    """ポートフォリオシートから全保有銘柄を取得"""
    sheet = get_sheet("PORTFOLIO")
    records = sheet.get_all_records()
    result = []
    for r in records:
        # 空行スキップ
        if not r.get("銘柄コード"):
            continue

        acquired_price_foreign = to_float_or_none(r.get("取得単価（外貨）"))
        acquired_exchange_rate = to_float_or_none(r.get("取得時為替レート"))
        shares = to_float(r.get("保有株数", 0))

        # D列（取得単価（円））は数式 =E*F のため未評価時は外貨×為替でフォールバック
        acquired_price_jpy = to_float(r.get("取得単価（円）", 0))
        if (acquired_price_jpy == 0
                and acquired_price_foreign and acquired_exchange_rate):
            acquired_price_jpy = acquired_price_foreign * acquired_exchange_rate

        # H列（取得額合計）は数式 =D*G のため未評価時は単価×株数でフォールバック
        total_cost = to_float(r.get("取得額合計", 0))
        if total_cost == 0:
            total_cost = acquired_price_jpy * shares

        # 外国株フラグは Unicode コードポイント不一致や空白混入に備えて正規化
        flag_raw = str(r.get("外国株フラグ", "")).strip()
        is_foreign = flag_raw in ("○", "〇", "True", "true", "1")

        result.append({
            "code": r["銘柄コード"],
            "name": r["銘柄名"],
            "acquiredDate": str(r.get("取得日", "")),
            "acquiredPriceJpy": acquired_price_jpy,
            "acquiredPriceForeign": acquired_price_foreign,
            "acquiredExchangeRate": acquired_exchange_rate,
            "shares": shares,
            "totalCost": total_cost,
            "currency": str(r.get("通貨", "JPY")),
            "isForeign": is_foreign,
        })
    return result
