# {{ year }}年{{ month_num }}月の投資成績 📊

{{ year }}年{{ month_num }}月の投資成績をまとめました。今月の総合損益は**{{ total_pl | format_currency }}円 ({{ total_pl_rate | format_percent }})**でした。

## ポートフォリオサマリー

| 項目 | 金額 |
|------|------|
| 合計取得額 | {{ total_cost | format_currency }}円 |
| 合計評価額 | {{ total_value | format_currency }}円 |
| {% if total_pl >= 0 %}🎉{% else %}😢{% endif %} 総合損益 | {{ total_pl | format_currency }}円 ({{ total_pl_rate | format_percent }}) |

{% if interactive_chart %}
## ポートフォリオ推移グラフ

過去6ヶ月間の評価額と取得額の推移です。

📊 **[インタラクティブチャート]({{ interactive_chart }})** をブラウザで開くと、マウスオーバーで各月の詳細データを確認できます。

{% endif %}
{% if chart_images and chart_images.portfolio %}
![ポートフォリオ推移]({{ chart_images.portfolio }})

{% endif %}

## 🇯🇵 日本株

{% set jp_stocks_list = holdings | selectattr('is_foreign', 'equalto', False) | list %}
{% if jp_stocks_list %}
{% for stock in jp_stocks_list %}
### {% if stock.pl >= 0 %}✅{% else %}⚠️{% endif %} {{ stock.name }} ({{ stock.symbol }})

| 項目 | 値 |
|------|------|
| 保有株数 | {{ stock.shares }}株 |
| 取得単価 | {{ stock.cost_price | format_currency }}円 |
| 現在価格 | {{ stock.current_price | format_currency }}円 |
| 評価額 | {{ stock.value | format_currency }}円 |
| {% if stock.pl >= 0 %}🎉{% else %}📉{% endif %} 損益 | {{ stock.pl | format_currency }}円 ({{ stock.pl_rate | format_percent }}) |

**📈 月間動向**

- 🔺 最高値: {{ stock.market_data.high | format_currency }}円
- 🔻 最安値: {{ stock.market_data.low | format_currency }}円
- 📊 月間変動率: {{ stock.market_data.change_rate | format_percent }}

{% if interactive_stock_charts and interactive_stock_charts[stock.name] %}
📊 **[インタラクティブチャート]({{ interactive_stock_charts[stock.name] }})** （期間切替・マウスオーバーで詳細表示）

{% endif %}
{% if chart_images and chart_images.stocks and chart_images.stocks[stock.symbol] %}
![{{ stock.name }}の株価推移]({{ chart_images.stocks[stock.symbol] }})

{% endif %}

{% if ai_comments and ai_comments.stock_comments and ai_comments.stock_comments[stock.symbol] %}
<div class="huki-box huki-left">
  <div class="huki-imgname">
    <img class="pf-face-img" src="https://www.pokebros.net/wp-content/uploads/2021/01/img_5545-e1610199620450.png" alt="あかブロス"/>
    <p class="huki-name">あかブロス</p>
  </div>
  <div class="huki-text" style="background-color:#ffcfcf">
    <p>{{ ai_comments.stock_comments[stock.symbol] }}</p>
    <span class="huki-text-after" style="border-right-color:#ffcfcf"></span>
  </div>
</div>
{% endif %}

---

{% endfor %}
{% else %}
*日本株の保有銘柄はありません*
{% endif %}

## 🌏 外国株

{% set foreign_stocks_list = holdings | selectattr('is_foreign', 'equalto', True) | list %}
{% if foreign_stocks_list %}
{% for stock in foreign_stocks_list %}
### {% if stock.pl >= 0 %}✅{% else %}⚠️{% endif %} {{ stock.name }} ({{ stock.symbol }})

| 項目 | 値 |
|------|------|
| 保有株数 | {{ stock.shares }}株 |
| 取得単価 | {{ stock.cost_price | format_number(2) }}{{ stock.currency }} |
| 現在価格 | {{ stock.current_price | format_number(2) }}{{ stock.currency }} |
| 評価額 | {{ stock.value | format_currency }}円（円換算）|
| {% if stock.pl >= 0 %}🎉{% else %}📉{% endif %} 損益 | {{ stock.pl | format_currency }}円 ({{ stock.pl_rate | format_percent }}) |
{% if stock.exchange_rate %}
| 為替レート | 1{{ stock.currency }} = {{ stock.exchange_rate | format_number(2) }}円 |
{% endif %}

**📈 月間動向**

- 🔺 最高値: {{ stock.market_data.high | format_number(2) }}{{ stock.currency }}
- 🔻 最安値: {{ stock.market_data.low | format_number(2) }}{{ stock.currency }}
- 📊 月間変動率: {{ stock.market_data.change_rate | format_percent }}

{% if interactive_stock_charts and interactive_stock_charts[stock.name] %}
📊 **[インタラクティブチャート]({{ interactive_stock_charts[stock.name] }})** （期間切替・外貨/円切替・マウスオーバーで詳細表示）

{% endif %}
{% if chart_images and chart_images.stocks and chart_images.stocks[stock.symbol] %}
![{{ stock.name }}の株価推移]({{ chart_images.stocks[stock.symbol] }})

{% endif %}

{% if ai_comments and ai_comments.stock_comments and ai_comments.stock_comments[stock.symbol] %}
<div class="huki-box huki-left">
  <div class="huki-imgname">
    <img class="pf-face-img" src="https://www.pokebros.net/wp-content/uploads/2021/01/img_5545-e1610199620450.png" alt="あかブロス"/>
    <p class="huki-name">あかブロス</p>
  </div>
  <div class="huki-text" style="background-color:#ffcfcf">
    <p>{{ ai_comments.stock_comments[stock.symbol] }}</p>
    <span class="huki-text-after" style="border-right-color:#ffcfcf"></span>
  </div>
</div>
{% endif %}

---

{% endfor %}
{% else %}
*外国株の保有銘柄はありません*
{% endif %}

## 📊 資産配分

現在のポートフォリオ構成は以下の通りです。

| 分類 | 比率 | 評価額 |
|------|------|------|
| 🇯🇵 日本株 | {{ jp_stocks.ratio | format_number(1) }}% | {{ jp_stocks.value | format_currency }}円 |
| 🌏 外国株 | {{ foreign_stocks.ratio | format_number(1) }}% | {{ foreign_stocks.value | format_currency }}円 |
| **合計** | **100.0%** | **{{ total_value | format_currency }}円** |

## 💭 まとめ

{% if ai_comments and ai_comments.summary %}
<div class="huki-box huki-right">
  <div class="huki-text" style="background-color:#97ffb1">
    <p>{{ ai_comments.summary }}</p>
    <span class="huki-text-after" style="border-right-color:#97ffb1"></span>
  </div>
  <div class="huki-imgname">
    <img class="pf-face-img" src="https://www.pokebros.net/wp-content/uploads/2021/01/img_9449-e1611203011189.png" alt="みどブロス"/>
    <p class="huki-name">みどブロス</p>
  </div>
</div>
{% endif %}

**今月のハイライト**:
- 総合損益: {{ total_pl | format_currency }}円 ({{ total_pl_rate | format_percent }})
- 評価額: {{ total_value | format_currency }}円
- 取得額: {{ total_cost | format_currency }}円

---

*このレポートは自動生成されました*
