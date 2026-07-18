"""買付履歴（purchase_history テーブルの行）から月末時点の累積ポジションを
計算する純粋関数モジュール。

DB・Sheets に一切依存しない stdlib のみの実装。report_json_builder.py が
monthly_pnl 構築時に行っている移動平均取得単価の累積計算（211〜214 行の
並び替え規約）を、単体テスト可能な形に切り出したもの。

データ規約:
- 買付 dict のキー: code, seq, shares, price, price_foreign, exchange_rate,
  purchased_at（"YYYY-MM-DD" 形式の文字列）
- 日本株: price に円単価が入り、price_foreign / exchange_rate は None
- 外国株: price は 0.0、price_foreign に外貨単価、exchange_rate に買付時の
  為替レート（USD/JPY）が入る
"""

from __future__ import annotations

from dataclasses import dataclass


def _parse_year_month(purchased_at: str) -> tuple[int, int]:
    """"YYYY-MM-DD" → (year, month) に変換する。空文字は (0, 0) 扱いにする。"""
    if not purchased_at:
        return (0, 0)
    parts = purchased_at.split("-")
    return int(parts[0]), int(parts[1])


@dataclass(frozen=True)
class CumulativePosition:
    """ある月末時点の累積ポジション（保有株数・累積コスト）。"""

    shares: float
    cost_jpy: float
    cost_native: float

    @property
    def avg_price_jpy(self) -> float:
        """円建ての移動平均取得単価。shares == 0 のときは 0.0。"""
        if self.shares == 0:
            return 0.0
        return self.cost_jpy / self.shares

    @property
    def avg_price_native(self) -> float:
        """ネイティブ通貨建ての移動平均取得単価。shares == 0 のときは 0.0。"""
        if self.shares == 0:
            return 0.0
        return self.cost_native / self.shares

    @property
    def avg_exchange_rate(self) -> float:
        """コスト加重平均為替レート（cost_jpy / cost_native）。

        買付ごとの為替レートを単純平均するのではなく、コスト加重
        （cost_jpy / cost_native）で算出する。これにより

            avg_price_jpy == avg_price_native * avg_exchange_rate

        が常に厳密成立し、円建て・ネイティブ通貨建ての平均取得単価が
        自己整合になる（単純平均だと成立しない）。
        cost_native == 0（未保有）のときは 0.0。
        """
        if self.cost_native == 0:
            return 0.0
        return self.cost_jpy / self.cost_native


def sort_purchases(purchases: list[dict]) -> list[dict]:
    """買付履歴を purchased_at の (年, 月) 昇順 → seq 昇順で並び替える。

    report_json_builder.py 211〜214 行と同一規約。
    TODO: 将来的にソートロジックを共通モジュールへ統合する。

    purchased_at が空文字の買付は (0, 0) 扱いとなり、常に先頭かつ
    常に累積対象になる。
    """
    return sorted(
        purchases,
        key=lambda p: (_parse_year_month(p["purchased_at"]), p["seq"]),
    )


def cumulative_position(
    purchases: list[dict], year: int, month: int, *, is_foreign: bool
) -> CumulativePosition:
    """指定年月の月末時点における累積ポジションを計算する。

    purchased_at の (年, 月) が (year, month) 以下の買付をすべて累積する
    （月中の買付はその月の月末残高に反映される）。

    - 日本株: ネイティブ = 円建て = price × shares
    - 外国株: ネイティブ = price_foreign × shares
             円建て = price_foreign × exchange_rate × shares

    Args:
        purchases: 買付履歴（辞書のリスト）。単一銘柄分を渡すこと。
        year: 対象年。
        month: 対象月。
        is_foreign: 外国株かどうか（True なら price_foreign / exchange_rate
            を使用する）。

    Returns:
        対象月末時点の CumulativePosition。

    Raises:
        ValueError: 外国株の買付で exchange_rate が None または 0 の場合。
            データ不備を黙って通さないための防御。
    """
    target = (year, month)
    cum_shares = 0.0
    cum_cost_jpy = 0.0
    cum_cost_native = 0.0

    for p in sort_purchases(purchases):
        if _parse_year_month(p["purchased_at"]) > target:
            continue

        shares = float(p["shares"])

        if is_foreign:
            exchange_rate = p.get("exchange_rate")
            if not exchange_rate:
                raise ValueError(
                    f"外国株の買付（code={p.get('code')!r}, seq={p.get('seq')!r}）に"
                    "有効な exchange_rate がありません。"
                )
            price_foreign = float(p["price_foreign"])
            cum_cost_native += price_foreign * shares
            cum_cost_jpy += price_foreign * float(exchange_rate) * shares
        else:
            price = float(p["price"])
            cum_cost_native += price * shares
            cum_cost_jpy += price * shares

        cum_shares += shares

    return CumulativePosition(
        shares=cum_shares, cost_jpy=cum_cost_jpy, cost_native=cum_cost_native
    )


def time_weighted_returns(series: list[tuple[str, float, float]]) -> dict[str, float]:
    """(date, 総評価額, 累積投入コスト) の昇順リストから月次連鎖の累積 TWR（%）を返す。

    追加買付（キャッシュフロー）の投入額そのものがリターンとして計上されて
    しまう単純な「(評価額 − 初月コスト) ÷ 初月コスト」方式のバグを解消する
    ための時間加重リターン（Time-Weighted Return）計算。

    数式:
        月次フロー: F_m = cost[m] − cost[m−1]（初月は F_0 = cost[0]）
            → その月に新たに投入された購入コストの増分。
        分母（期初評価額 + 当月フロー）:
            D_m = value[m−1] + F_m（初月は D_0 = cost[0]）
            → フローは「期初に投入された」とみなして分母に加える
              （Modified Dietz 法の簡易版・月次のみのフロータイミング近似）。
        月次リターン:
            r_m = value[m] / D_m − 1
            ただし D_m <= 0 のときはゼロ除算・負の分母による発散を防ぐため
            r_m = 0.0 とする（防御的フォールバック）。
        累積 TWR:
            cum = Π(1 + r_i) − 1
        戻り値は {date: round(cum × 100, 2)}（パーセント表記・小数2桁）。

    欠損月（例: 途中の月が series に存在しない）はそのまま連鎖する。
    欠損分のフローは次に存在する月の cost 差分に自然に吸収されるため、
    特別な補間は行わない。

    Args:
        series: (date, value, cost) のタプルのリスト。date 昇順であること
            （呼び出し側でソート済みを渡す）。value は総評価額、cost は
            その月末時点の累積投入コスト（いずれも円）。

    Returns:
        {date: 累積 TWR（%、小数2桁）} の辞書。series が空なら空辞書。
    """
    returns: dict[str, float] = {}
    cum = 1.0
    prev_value: float | None = None
    prev_cost: float | None = None

    for date, value, cost in series:
        flow = cost if prev_cost is None else cost - prev_cost
        denominator = cost if prev_value is None else prev_value + flow

        rate = (value / denominator - 1) if denominator > 0 else 0.0

        cum *= 1 + rate
        returns[date] = round((cum - 1) * 100, 2)

        prev_value = value
        prev_cost = cost

    return returns
