"""インタラクティブHTMLチャート生成モジュール

Chart.jsベースの自己完結型HTMLチャートを生成する。
WordPressの「カスタムHTML」ブロックに貼り付け可能。
- ポートフォリオ全体チャート（月次損益）
- 銘柄別チャート（期間切替・外貨/円切替対応）
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sheets_writer import SheetsDataWriter


class InteractiveChartGenerator:
    """インタラクティブHTMLチャート生成クラス"""

    def __init__(self, sheets_writer: SheetsDataWriter) -> None:
        self.sheets_writer = sheets_writer

    def generate(
        self,
        year: int,
        month: int,
        report_data: dict,
        chart_data: dict,
    ) -> dict:
        """全チャートを生成

        Returns:
            {"portfolio": "path", "stocks": {"銘柄名": "path"}}
        """
        output_dir = os.path.join(
            "output", f"{year}_{month:02d}_charts"
        )
        os.makedirs(output_dir, exist_ok=True)
        result = {"portfolio": None, "stocks": {}}

        try:
            # 月次損益データ
            monthly = self._build_monthly_data(
                report_data, chart_data
            )
            # 日次データ取得（レポート月末まで）
            daily = self._build_daily_data(
                report_data, year, month
            )

            # ポートフォリオ全体チャート
            pf_html = self._render_portfolio_html(
                year, month, monthly
            )
            pf_path = os.path.join(
                output_dir, "interactive_chart.html"
            )
            self._write(pf_path, pf_html)
            result["portfolio"] = pf_path
            print(f"✅ ポートフォリオチャート: {pf_path}")

            # 銘柄別チャート
            for name, data in daily.items():
                safe = (
                    data["symbol"]
                    .replace(".", "_")
                    .replace("/", "_")
                )
                path = os.path.join(
                    output_dir, f"{safe}_interactive.html"
                )
                html = self._render_stock_html(
                    name, data, year, month
                )
                self._write(path, html)
                result["stocks"][name] = path
                print(f"✅ {name}チャート: {path}")

        except Exception as e:
            print(f"❌ インタラクティブチャート生成エラー: {e}")
            import traceback

            traceback.print_exc()

        return result

    def _write(self, path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    # ---- データ構築 ----

    def _build_monthly_data(
        self, report_data: dict, chart_data: dict
    ) -> dict:
        """月次損益チャート用データを構築"""
        labels = chart_data.get("labels", [])
        total_values = chart_data.get("total_values", [])
        total_costs = chart_data.get("total_costs", [])
        holdings_data = chart_data.get("holdings_data", {})

        # 銘柄別取得額推移
        holdings_costs: dict[str, list] = {}
        try:
            perf_sheet = self.sheets_writer.spreadsheet.worksheet(
                "損益レポート"
            )
            perf_records = perf_sheet.get_all_records()

            for label in labels:
                target_date = f"{label}-末"
                month_records = [
                    r
                    for r in perf_records
                    if r.get("日付") == target_date
                ]
                seen: dict[str, dict] = {}
                for r in month_records:
                    code = r.get("銘柄コード", "")
                    update = r.get("更新日時", "")
                    if code and (
                        code not in seen
                        or update
                        > seen[code].get("更新日時", "")
                    ):
                        seen[code] = r

                found = set()
                for _code, r in seen.items():
                    name = r.get("銘柄名", "")
                    cost = r.get("取得額", 0)
                    if name not in holdings_costs:
                        # 過去月分をNoneで埋める
                        idx = labels.index(label)
                        holdings_costs[name] = [None] * idx
                    holdings_costs[name].append(cost)
                    found.add(name)

                for name in holdings_costs:
                    if name not in found:
                        holdings_costs[name].append(None)

        except Exception as e:
            print(f"⚠️ 銘柄別取得額取得失敗: {e}")

        stocks = {}
        for h in report_data.get("holdings", []):
            name = h.get("name", "")
            if name in holdings_data:
                stocks[name] = {
                    "name": name,
                    "symbol": h.get("symbol", ""),
                    "values": holdings_data[name],
                    "costs": holdings_costs.get(name, []),
                    "currency": h.get("currency", "JPY"),
                    "is_foreign": h.get("is_foreign", False),
                }

        return {
            "labels": labels,
            "total": {
                "values": total_values,
                "costs": total_costs,
            },
            "stocks": stocks,
        }

    def _build_daily_data(
        self,
        report_data: dict,
        year: int,
        month: int,
    ) -> dict:
        """日次データを取得（レポート月末まで）"""
        daily_data = {}

        # レポート月末日を算出
        from datetime import timedelta

        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        # yfinanceのendは排他的なので翌日にする
        month_last = end_date - timedelta(days=1)
        end_date_yf = end_date + timedelta(days=1)

        try:
            import yfinance as yf

            portfolio_sheet = (
                self.sheets_writer.spreadsheet.worksheet(
                    "ポートフォリオ"
                )
            )
            portfolio_records = portfolio_sheet.get_all_records()

            # 為替レート履歴キャッシュ
            fx_cache: dict[str, object] = {}

            for holding in report_data.get("holdings", []):
                symbol = holding.get("symbol", "")
                name = holding.get("name", "")
                currency = holding.get("currency", "JPY")
                is_foreign = holding.get("is_foreign", False)

                entry = next(
                    (
                        p
                        for p in portfolio_records
                        if p.get("銘柄コード") == symbol
                    ),
                    {},
                )
                purchase_date = entry.get("取得日", "")
                if not purchase_date:
                    continue

                try:
                    pdt = datetime.strptime(
                        purchase_date, "%Y-%m-%d"
                    )
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(
                        start=pdt, end=end_date_yf
                    )
                    if hist.empty:
                        continue

                    # 月末日以降のデータを除外
                    cutoff = month_last.strftime("%Y-%m-%d")
                    hist = hist[
                        hist.index.strftime("%Y-%m-%d")
                        <= cutoff
                    ]
                    if hist.empty:
                        continue

                    dates = [
                        d.strftime("%Y-%m-%d") for d in hist.index
                    ]
                    closes = [
                        round(float(v), 2) for v in hist["Close"]
                    ]
                    highs = [
                        round(float(v), 2) for v in hist["High"]
                    ]
                    lows = [
                        round(float(v), 2) for v in hist["Low"]
                    ]

                    # 取得価格
                    cost = holding.get("cost_price", 0)
                    if is_foreign and holding.get(
                        "purchase_price_foreign"
                    ):
                        cost = holding["purchase_price_foreign"]

                    # 外国株: 円換算データも用意
                    closes_jpy = None
                    highs_jpy = None
                    lows_jpy = None
                    cost_jpy = None
                    if is_foreign and currency != "JPY":
                        fx_pair = f"{currency}JPY=X"
                        if fx_pair not in fx_cache:
                            try:
                                fx = yf.Ticker(fx_pair)
                                fx_hist = fx.history(
                                    start=pdt,
                                    end=end_date_yf,
                                )
                                fx_cache[fx_pair] = fx_hist
                            except Exception:
                                fx_cache[fx_pair] = None
                        fx_hist = fx_cache.get(fx_pair)
                        if fx_hist is not None and not fx_hist.empty:
                            closes_jpy = []
                            highs_jpy = []
                            lows_jpy = []
                            for i, d in enumerate(hist.index):
                                rate = self._get_fx_rate(
                                    fx_hist, d
                                )
                                closes_jpy.append(
                                    round(closes[i] * rate, 0)
                                )
                                highs_jpy.append(
                                    round(highs[i] * rate, 0)
                                )
                                lows_jpy.append(
                                    round(lows[i] * rate, 0)
                                )
                            pr = holding.get(
                                "purchase_exchange_rate", 0
                            )
                            if pr:
                                cost_jpy = round(
                                    float(cost) * float(pr), 0
                                )

                    daily_data[name] = {
                        "symbol": symbol,
                        "dates": dates,
                        "closes": closes,
                        "highs": highs,
                        "lows": lows,
                        "purchase_date": purchase_date,
                        "cost_price": cost,
                        "currency": currency,
                        "is_foreign": is_foreign,
                    }
                    if closes_jpy:
                        daily_data[name]["closes_jpy"] = closes_jpy
                        daily_data[name]["highs_jpy"] = highs_jpy
                        daily_data[name]["lows_jpy"] = lows_jpy
                        if cost_jpy:
                            daily_data[name][
                                "cost_price_jpy"
                            ] = cost_jpy

                    print(
                        f"  📊 {name}: 日次データ "
                        f"{len(dates)}件取得"
                    )

                except Exception as e:
                    print(f"  ⚠️ {name}の日次データ取得失敗: {e}")

        except ImportError:
            print("⚠️ yfinance未インストール")
        except Exception as e:
            print(f"⚠️ 日次データ取得エラー: {e}")

        return daily_data

    def _get_fx_rate(self, fx_hist: object, date: object) -> float:
        """指定日の為替レートを取得（直近値にフォールバック）"""

        if date in fx_hist.index:
            return float(fx_hist.loc[date, "Close"])
        # 直近の営業日を探す
        prior = fx_hist.index[fx_hist.index <= date]
        if len(prior) > 0:
            return float(
                fx_hist.loc[prior[-1], "Close"]
            )
        # それでもなければ最初のレート
        return float(fx_hist.iloc[0]["Close"])

    # ---- ポートフォリオHTML ----

    def _render_portfolio_html(
        self, year: int, month: int, monthly: dict
    ) -> str:
        data_json = json.dumps(monthly, ensure_ascii=False)
        return f"""{_CHARTJS_CDN}
{_CSS_COMMON}
<div class="ic-container">
    <div class="ic-title">
        {year}年{month}月 投資パフォーマンス
        <span class="ic-date-label">
            {year}年{month}月末時点</span>
    </div>
    <div class="ic-stock-tabs" id="icStockTabs"></div>
    <div class="ic-chart-wrapper">
        <canvas id="icChart"></canvas>
    </div>
    <div class="ic-info" id="icInfo"></div>
</div>
<script>
(function() {{
const D = {data_json};
let chart = null;
const sel = new Set(['_total']);
const ctn = document.getElementById('icStockTabs');
const names = Object.keys(D.stocks);
const palette = [
    '#2563eb','#dc2626','#16a34a',
    '#f59e0b','#8b5cf6','#ec4899',
    '#06b6d4','#84cc16'];

function fmt(v) {{
    return new Intl.NumberFormat('ja-JP', {{
        style:'currency',currency:'JPY',
        maximumFractionDigits:0
    }}).format(v);
}}

function buildTabs() {{
    ctn.innerHTML = '';
    const add = (k, l) => {{
        const b = document.createElement('button');
        b.className = 'ic-stock-tab'
            + (sel.has(k) ? ' active' : '');
        b.textContent = l;
        b.onclick = () => {{
            if (k === '_total') {{
                sel.clear(); sel.add('_total');
            }} else {{
                sel.delete('_total');
                if (sel.has(k)) sel.delete(k);
                else sel.add(k);
                if (sel.size === 0)
                    sel.add('_total');
            }}
            buildTabs(); draw();
        }};
        ctn.appendChild(b);
    }};
    add('_total', '全体');
    names.forEach(n => add(n, n));
}}

function draw() {{
    if (chart) chart.destroy();
    const labels = D.labels;
    const ds = [];
    let iV = null, iC = null;

    if (sel.has('_total')) {{
        iV = D.total.values;
        iC = D.total.costs;
        ds.push({{
            label:'評価額', data:iV,
            borderColor:'#2563eb',
            backgroundColor:'rgba(37,99,235,0.08)',
            borderWidth:2.5, tension:0, fill:false,
            spanGaps:true,
            pointRadius:5, pointHoverRadius:7,
            pointBackgroundColor:'#2563eb'
        }});
        if (iC && iC.some(v => v > 0)) {{
            ds.push({{
                label:'取得額', data:iC,
                borderColor:'#94a3b8',
                backgroundColor:
                    'rgba(148,163,184,0.08)',
                borderWidth:2, borderDash:[6,4],
                tension:0, fill:false, spanGaps:true,
                pointRadius:4, pointHoverRadius:6,
                pointBackgroundColor:'#94a3b8'
            }});
        }}
    }} else {{
        let ci = 0;
        for (const nm of sel) {{
            const s = D.stocks[nm];
            if (!s) continue;
            const col = palette[ci % palette.length];
            ds.push({{
                label:nm, data:s.values,
                borderColor:col,
                backgroundColor:col+'14',
                borderWidth:2.5, tension:0,
                fill:false, spanGaps:true,
                pointRadius:5, pointHoverRadius:7,
                pointBackgroundColor:col
            }});
            if (sel.size === 1) {{
                iV = s.values; iC = s.costs;
                if (s.costs
                    && s.costs.some(v => v > 0)) {{
                    ds.push({{
                        label:nm+' 取得額',
                        data:s.costs,
                        borderColor:'#94a3b8',
                        backgroundColor:
                            'rgba(148,163,184,0.08)',
                        borderWidth:2,
                        borderDash:[6,4],
                        tension:0, fill:false,
                        spanGaps:true,
                        pointRadius:4,
                        pointHoverRadius:6,
                        pointBackgroundColor:'#94a3b8'
                    }});
                }}
            }}
            ci++;
        }}
    }}

    const ctx = document.getElementById('icChart')
        .getContext('2d');
    chart = new Chart(ctx, {{
        type:'line',
        data:{{ labels:labels, datasets:ds }},
        options:{{
            responsive:true,
            maintainAspectRatio:false,
            plugins:{{
                legend:{{
                    display:true, position:'top',
                    align:'end'
                }},
                tooltip:{{
                    mode:'index', intersect:false,
                    callbacks:{{
                        label: c => {{
                            if (c.parsed.y == null)
                                return c.dataset.label
                                    + ': データなし';
                            return c.dataset.label
                                + ': ' + fmt(c.parsed.y);
                        }}
                    }}
                }}
            }},
            scales:{{
                x:{{
                    ticks:{{
                        callback: function(val, idx) {{
                            const d = labels[idx];
                            if (!d) return '';
                            const p = d.split('-');
                            const y = p[0];
                            const m = parseInt(p[1],10);
                            if (idx === 0)
                                return y + '/' + m;
                            const prev = labels[idx-1];
                            if (!prev) return m;
                            const py = prev.split('-')[0];
                            if (y !== py)
                                return y + '/' + m;
                            return m + '月';
                        }}
                    }}
                }},
                y:{{
                    beginAtZero:false,
                    ticks:{{ callback: v => fmt(v) }}
                }}
            }},
            interaction:{{
                mode:'nearest', axis:'x',
                intersect:false
            }}
        }}
    }});

    // 情報パネル
    const info = document.getElementById('icInfo');
    if (sel.has('_total') || sel.size === 1) {{
        const lv = iV
            ? (iV[iV.length-1] || 0) : 0;
        const lc = iC && iC.length
            ? (iC[iC.length-1] || 0) : 0;
        const pl = lv - lc;
        const rt = lc > 0
            ? ((pl/lc)*100).toFixed(2) : '0.00';
        const cl = pl >= 0
            ? 'positive' : 'negative';
        const sg = pl >= 0 ? '+' : '';
        info.innerHTML = `
            <div class="ic-info-item">
                <span class="ic-info-label">
                    取得額</span>
                <span class="ic-info-value">
                    ${{fmt(lc)}}</span></div>
            <div class="ic-info-item">
                <span class="ic-info-label">
                    評価額</span>
                <span class="ic-info-value">
                    ${{fmt(lv)}}</span></div>
            <div class="ic-info-item">
                <span class="ic-info-label">
                    評価損益</span>
                <span class="ic-info-value ${{cl}}">
                    ${{sg}}${{fmt(pl)}}</span></div>
            <div class="ic-info-item">
                <span class="ic-info-label">
                    損益率</span>
                <span class="ic-info-value ${{cl}}">
                    ${{sg}}${{rt}}%</span></div>`;
    }} else {{
        let h = '';
        let ci = 0;
        for (const nm of sel) {{
            const s = D.stocks[nm];
            if (!s) continue;
            const v = s.values;
            const c = s.costs;
            const lv = v
                ? (v[v.length-1] || 0) : 0;
            const lc = c && c.length
                ? (c[c.length-1] || 0) : 0;
            const pl = lv - lc;
            const rt = lc > 0
                ? ((pl/lc)*100).toFixed(1) : '0.0';
            const cl = pl >= 0
                ? 'positive' : 'negative';
            const sg = pl >= 0 ? '+' : '';
            const col = palette[ci % palette.length];
            h += `<div class="ic-info-item">
                <span class="ic-info-label"
                    style="color:${{col}}">${{nm}}</span>
                <span class="ic-info-value ${{cl}}">
                    ${{fmt(lv)}}
                    (${{sg}}${{rt}}%)</span>
                </div>`;
            ci++;
        }}
        info.innerHTML = h;
    }}
}}
buildTabs(); draw();
}})();
</script>"""

    # ---- 個別銘柄HTML ----

    def _render_stock_html(
        self,
        name: str,
        data: dict,
        year: int,
        month: int,
    ) -> str:
        data_json = json.dumps(data, ensure_ascii=False)
        is_foreign = data.get("is_foreign", False)
        currency = data.get("currency", "JPY")
        date_label = f"{year}年{month}月末時点"

        # 月末日付文字列（JS用）
        from datetime import timedelta

        if month == 12:
            _me = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            _me = (
                datetime(year, month + 1, 1) - timedelta(days=1)
            )
        month_end_str = _me.strftime("%Y-%m-%d")

        # 外貨切替ボタンHTML
        fx_toggle = ""
        if is_foreign and currency != "JPY":
            fx_toggle = f"""
    <div class="ic-view-tabs" id="fxToggle">
        <button class="ic-view-tab active"
            data-fx="foreign">{currency}</button>
        <button class="ic-view-tab"
            data-fx="jpy">JPY</button>
    </div>"""

        return f"""{_CHARTJS_CDN}
{_CSS_COMMON}
<div class="ic-container">
    <div class="ic-title">{name} ({data['symbol']})
        <span class="ic-date-label">{date_label}</span>
    </div>
    {fx_toggle}
    <div class="ic-period-tabs" id="periodTabs">
        <button class="ic-stock-tab" data-period="1m">
            1M</button>
        <button class="ic-stock-tab active"
            data-period="6m">6M</button>
        <button class="ic-stock-tab" data-period="1y">
            1Y</button>
        <button class="ic-stock-tab" data-period="all">
            全期間</button>
    </div>
    <div class="ic-chart-wrapper">
        <canvas id="icChart"></canvas>
    </div>
    <div class="ic-info" id="icInfo"></div>
</div>
<script>
(function() {{
const S = {data_json};
const isForeign = {str(is_foreign).lower()};
const currency = '{currency}';
const monthEnd = '{month_end_str}';
const repYear = {year};
const repMonth = {month};
let chart = null;
let period = '6m';
let showJPY = false;

function fmtJPY(v) {{
    return new Intl.NumberFormat('ja-JP', {{
        style:'currency', currency:'JPY',
        maximumFractionDigits:0
    }}).format(v);
}}
function fmtForeign(v, cur) {{
    try {{
        return new Intl.NumberFormat('en-US', {{
            style:'currency', currency:cur,
            minimumFractionDigits:2
        }}).format(v);
    }} catch {{ return v.toLocaleString(); }}
}}
function fmtP(v) {{
    if (showJPY) return fmtJPY(v);
    if (!isForeign || currency === 'JPY')
        return fmtJPY(v);
    return fmtForeign(v, currency);
}}
function pad2(n) {{ return n < 10 ? '0'+n : ''+n; }}

function startDateFor(p) {{
    const ey = parseInt(monthEnd.slice(0,4),10);
    const em = parseInt(monthEnd.slice(5,7),10);
    switch(p) {{
        case '1m':
            return monthEnd.slice(0,8) + '01';
        case '6m': {{
            let sm = em - 6; let sy = ey;
            if (sm <= 0) {{ sm += 12; sy--; }}
            return sy + '-' + pad2(sm) + '-01';
        }}
        case '1y':
            return (ey-1) + '-' + pad2(em) + '-01';
        default: return '0000-00-00';
    }}
}}

function getSlice() {{
    const sd = startDateFor(period);
    let si = 0;
    if (period !== 'all') {{
        si = S.dates.findIndex(d => d >= sd);
        if (si < 0) si = 0;
    }}
    const sl = (arr) => arr ? arr.slice(si) : null;
    return {{
        dates: sl(S.dates),
        closes: sl(showJPY && S.closes_jpy
            ? S.closes_jpy : S.closes),
        highs: sl(showJPY && S.highs_jpy
            ? S.highs_jpy : S.highs),
        lows: sl(showJPY && S.lows_jpy
            ? S.lows_jpy : S.lows),
        cost: showJPY && S.cost_price_jpy
            ? S.cost_price_jpy : S.cost_price,
    }};
}}

function draw() {{
    if (chart) chart.destroy();
    const s = getSlice();
    const costLine = s.dates.map(() => s.cost);
    const ctx = document.getElementById('icChart')
        .getContext('2d');
    chart = new Chart(ctx, {{
        type:'line',
        data:{{
            labels: s.dates,
            datasets:[
                {{
                    label:'終値', data:s.closes,
                    borderColor:'#2563eb',
                    backgroundColor:
                        'rgba(37,99,235,0.08)',
                    borderWidth:2.5, tension:0,
                    fill:false,
                    pointRadius: s.dates.length > 90
                        ? 0 : 3,
                    pointHoverRadius:5,
                    pointBackgroundColor:'#2563eb'
                }},
                {{
                    label:'取得単価', data:costLine,
                    borderColor:'#f59e0b',
                    borderWidth:2,
                    borderDash:[6,4], tension:0,
                    fill:false,
                    pointRadius:0,
                    pointHoverRadius:0
                }}
            ]
        }},
        options:{{
            responsive:true,
            maintainAspectRatio:false,
            plugins:{{
                legend:{{
                    display:true, position:'top',
                    align:'end'
                }},
                tooltip:{{
                    mode:'index', intersect:false,
                    callbacks:{{
                        title: items =>
                            s.dates[items[0].dataIndex],
                        label: c => {{
                            if (c.datasetIndex === 1)
                                return '取得単価: '
                                    + fmtP(c.parsed.y);
                            return '終値: '
                                + fmtP(c.parsed.y);
                        }},
                        afterBody: items => {{
                            const i = items[0].dataIndex;
                            const lines = [];
                            lines.push('高値: '
                                + fmtP(s.highs[i]));
                            lines.push('安値: '
                                + fmtP(s.lows[i]));
                            const d = s.closes[i]
                                - s.cost;
                            const r = s.cost > 0
                                ? ((d/s.cost)*100)
                                    .toFixed(1) : '0.0';
                            const sg = d>=0?'+':'';
                            lines.push('');
                            lines.push('取得比: '
                                + sg + r + '%');
                            return lines;
                        }}
                    }}
                }}
            }},
            scales:{{
                x:{{
                    ticks:{{
                        autoSkip: false,
                        maxRotation: 45,
                        callback: function(val, idx) {{
                            const d = s.dates[idx];
                            if (!d) return null;
                            const n = s.dates.length;
                            const p = d.split('-');
                            const y = p[0];
                            const m = parseInt(p[1],10);
                            const day = p[2]
                                ? '/'+parseInt(p[2],10)
                                : '';
                            const full = y+'/'+m+day;
                            const sh = m + day;
                            if (idx === 0
                                || idx === n - 1)
                                return full;
                            if (idx > 0) {{
                                const pv =
                                    s.dates[idx-1];
                                if (pv && pv.split(
                                    '-')[0] !== y)
                                    return full;
                            }}
                            const step = Math.max(
                                1,
                                Math.floor(n / 10));
                            if (idx % step === 0
                                && (n - idx) > step/2)
                                return sh;
                            return null;
                        }}
                    }}
                }},
                y:{{
                    beginAtZero:false,
                    ticks:{{ callback: v => fmtP(v) }}
                }}
            }},
            interaction:{{
                mode:'nearest', axis:'x',
                intersect:false
            }}
        }}
    }});
    // 情報パネル
    const lc = s.closes[s.closes.length-1];
    const cp = s.cost;
    const df = lc - cp;
    const rt = cp > 0
        ? ((df/cp)*100).toFixed(2) : '0.00';
    const cl = df >= 0 ? 'positive' : 'negative';
    const sg = df >= 0 ? '+' : '';
    const ph = Math.max(...s.highs);
    const pl2 = Math.min(...s.lows);
    let hlLbl;
    if (period === '1m')
        hlLbl = repYear+'年'+repMonth+'月 高値/安値';
    else if (period === '6m')
        hlLbl = '過去6ヶ月 高値/安値';
    else if (period === '1y')
        hlLbl = '過去1年 高値/安値';
    else hlLbl = '全期間 高値/安値';
    document.getElementById('icInfo').innerHTML = `
        <div class="ic-info-item">
            <span class="ic-info-label">取得単価</span>
            <span class="ic-info-value">
                ${{fmtP(cp)}}</span></div>
        <div class="ic-info-item">
            <span class="ic-info-label">月末終値</span>
            <span class="ic-info-value">
                ${{fmtP(lc)}}</span></div>
        <div class="ic-info-item">
            <span class="ic-info-label">取得比</span>
            <span class="ic-info-value ${{cl}}">
                ${{sg}}${{rt}}%</span></div>
        <div class="ic-info-item">
            <span class="ic-info-label">${{hlLbl}}</span>
            <span class="ic-info-value">
                ${{fmtP(ph)}} / ${{fmtP(pl2)}}</span>
        </div>`;
}}

// 期間切替
document.querySelectorAll('#periodTabs button')
    .forEach(b => {{
    b.onclick = () => {{
        document.querySelectorAll('#periodTabs button')
            .forEach(x => x.classList.remove('active'));
        b.classList.add('active');
        period = b.dataset.period;
        draw();
    }};
}});

// 外貨/円切替
const fxEl = document.getElementById('fxToggle');
if (fxEl) {{
    fxEl.querySelectorAll('button').forEach(b => {{
        b.onclick = () => {{
            fxEl.querySelectorAll('button')
                .forEach(x =>
                    x.classList.remove('active'));
            b.classList.add('active');
            showJPY = b.dataset.fx === 'jpy';
            draw();
        }};
    }});
}}

draw();
}})();
</script>"""


# ---- 共通パーツ ----

_CHARTJS_CDN = (
    '<script src="https://cdn.jsdelivr.net/npm/'
    'chart.js@4.4.1/dist/chart.umd.min.js"></script>'
)

_CSS_COMMON = """<style>
.ic-container {
    max-width: 900px; margin: 0 auto; padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont,
        "Segoe UI", Roboto, sans-serif;
}
.ic-title {
    font-size: 20px; font-weight: 700;
    margin-bottom: 16px; color: #1a1a1a;
}
.ic-date-label {
    font-size: 13px; font-weight: 400;
    color: #94a3b8; margin-left: 8px;
}
.ic-view-tabs {
    display: flex; gap: 4px; margin-bottom: 16px;
    background: #f1f5f9; border-radius: 8px;
    padding: 4px;
}
.ic-view-tab {
    flex: 1; padding: 10px 16px; background: none;
    border: none; border-radius: 6px; cursor: pointer;
    font-size: 14px; font-weight: 500; color: #64748b;
    transition: all 0.2s;
}
.ic-view-tab:hover { color: #334155; }
.ic-view-tab.active {
    background: white; color: #2563eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.ic-stock-tabs, .ic-period-tabs {
    display: flex; gap: 8px; margin-bottom: 16px;
    flex-wrap: wrap;
}
.ic-stock-tab {
    padding: 8px 18px; background: #f8fafc;
    border: 1px solid #e2e8f0; border-radius: 20px;
    cursor: pointer; font-size: 13px; font-weight: 500;
    color: #475569; transition: all 0.2s;
}
.ic-stock-tab:hover {
    border-color: #2563eb; color: #2563eb;
}
.ic-stock-tab.active {
    background: #2563eb; border-color: #2563eb;
    color: white;
}
.ic-chart-wrapper {
    position: relative; height: 400px;
    background: white; padding: 16px;
    border-radius: 12px; border: 1px solid #e2e8f0;
}
.ic-info {
    margin-top: 16px; padding: 16px;
    background: #f8fafc; border-radius: 10px;
    display: grid;
    grid-template-columns:
        repeat(auto-fit, minmax(180px, 1fr));
    gap: 12px;
}
.ic-info-item {
    display: flex; flex-direction: column;
}
.ic-info-label {
    font-size: 11px; color: #94a3b8;
    margin-bottom: 4px; text-transform: uppercase;
    letter-spacing: 0.05em;
}
.ic-info-value {
    font-size: 18px; font-weight: 600;
    color: #1e293b;
}
.ic-info-value.positive { color: #16a34a; }
.ic-info-value.negative { color: #dc2626; }
@media (max-width: 600px) {
    .ic-container { padding: 12px; }
    .ic-title { font-size: 16px; margin-bottom: 12px; }
    .ic-chart-wrapper { height: 280px; padding: 10px; }
    .ic-stock-tab {
        padding: 6px 12px; font-size: 12px;
    }
    .ic-view-tab {
        padding: 8px 10px; font-size: 13px;
    }
    .ic-info {
        grid-template-columns: 1fr 1fr;
        gap: 8px; padding: 12px;
    }
    .ic-info-value { font-size: 15px; }
    .ic-info-label { font-size: 10px; }
}
@media (max-width: 380px) {
    .ic-info {
        grid-template-columns: 1fr;
    }
}
</style>"""
