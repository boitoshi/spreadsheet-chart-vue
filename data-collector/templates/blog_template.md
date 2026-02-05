# {{ year }}年{{ month_num }}月の投資成績

## はじめに
{{ year }}年{{ month_num }}月の投資成績をまとめました。

## 目次
- [ポートフォリオサマリー](#ポートフォリオサマリー)
- [日本株](#日本株)
- [外国株](#外国株)
- [資産配分](#資産配分)
- [まとめ](#まとめ)

## ポートフォリオサマリー

| 項目 | 金額 |
|------|------|
| 合計取得額 | {{ total_cost | format_currency }}円 |
| 合計評価額 | {{ total_value | format_currency }}円 |
| 総合損益 | {{ total_pl | format_currency }}円 ({{ total_pl_rate | format_percent }}) |

## 日本株

{% set jp_stocks_list = holdings | selectattr('is_foreign', 'equalto', False) | list %}
{% if jp_stocks_list %}
{% for stock in jp_stocks_list %}
### {{ stock.name }} ({{ stock.symbol }})

| 項目 | 値 |
|------|------|
| 保有株数 | {{ stock.shares }}株 |
| 取得単価 | {{ stock.cost_price | format_currency }}円 |
| 現在価格 | {{ stock.current_price | format_currency }}円 |
| 評価額 | {{ stock.value | format_currency }}円 |
| 損益 | {{ stock.pl | format_currency }}円 ({{ stock.pl_rate | format_percent }}) |

**月間動向**:
- 最高値: {{ stock.market_data.high | format_currency }}円
- 最安値: {{ stock.market_data.low | format_currency }}円
- 月間変動率: {{ stock.market_data.change_rate | format_percent }}

<!-- 🖊️ ここに手動でコメントを追加 -->

{% endfor %}
{% else %}
*日本株の保有銘柄はありません*
{% endif %}

## 外国株

{% set foreign_stocks_list = holdings | selectattr('is_foreign', 'equalto', True) | list %}
{% if foreign_stocks_list %}
{% for stock in foreign_stocks_list %}
### {{ stock.name }} ({{ stock.symbol }})

| 項目 | 値 |
|------|------|
| 保有株数 | {{ stock.shares }}株 |
| 取得単価 | {{ stock.cost_price | format_number(2) }}{{ stock.currency }} |
| 現在価格 | {{ stock.current_price | format_number(2) }}{{ stock.currency }} |
| 評価額（円換算） | {{ stock.value | format_currency }}円 |
| 損益 | {{ stock.pl | format_currency }}円 ({{ stock.pl_rate | format_percent }}) |
{% if stock.exchange_rate %}
| 使用為替レート | 1{{ stock.currency }} = {{ stock.exchange_rate | format_number(2) }}円 |
{% endif %}

**月間動向**:
- 最高値: {{ stock.market_data.high | format_number(2) }}{{ stock.currency }}
- 最安値: {{ stock.market_data.low | format_number(2) }}{{ stock.currency }}
- 月間変動率: {{ stock.market_data.change_rate | format_percent }}

<!-- 🖊️ ここに手動でコメントを追加 -->

{% endfor %}
{% else %}
*外国株の保有銘柄はありません*
{% endif %}

## 資産配分

- 🇯🇵 日本株: {{ jp_stocks.ratio | format_number(1) }}% ({{ jp_stocks.value | format_currency }}円)
- 🌏 外国株: {{ foreign_stocks.ratio | format_number(1) }}% ({{ foreign_stocks.value | format_currency }}円)

## グラフデータ

以下のJSONデータをChart.jsなどで可視化できます。

```json
{{ chart_data | format_json }}
```

## まとめ

<!-- 🖊️ ここに手動でまとめを追加 -->

---
*このレポートは data-collector で自動生成されました*
