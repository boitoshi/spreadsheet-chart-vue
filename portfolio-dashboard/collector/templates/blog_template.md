# 「ポケモン投資」{{ year }}年{{ month_num }}月の状況

ポケモンファンによるお布施として、ポケモン関連銘柄に投資しています。推しへのお布施なのでそれだけでハッピーなのですが、もしかすると値上がりなんかしちゃってるかも!?

## 今月の状況【日本株】（{{ year }}/{{ month_num }}/末）

{% set jp_list = holdings | selectattr('is_foreign', 'equalto', False) | list %}
{% if jp_list %}
### 保有状況

| 銘柄 | 数量 | 平均取得価額 | 合計 |
|------|------|------------|------|
{% for stock in jp_list %}
| {{ stock.name }}（{{ stock.symbol }}） | {{ stock.shares }}株 | {{ stock.cost_price | format_currency }}円 | {{ stock.cost | format_currency }}円 |
{% endfor %}

{% for stock in jp_list %}
{% if stock.purchase_history %}
<details>
<summary>{{ stock.name }}の購入履歴を見る</summary>

| 回 | 数量 | 取得価額 | 購入日 |
|----|------|---------|--------|
{% for ph in stock.purchase_history %}
| {{ ph.seq }} | {{ ph.shares }}株 | {{ ph.price | format_currency }}円 | {{ ph.purchased_at }} |
{% endfor %}

</details>
{% endif %}
{% endfor %}

### 月末時点損益

| 銘柄 | 平均取得価額 | 現在価額 | 損益 |
|------|------------|---------|------|
{% for stock in jp_list %}
| {{ stock.name }} | {{ stock.cost_price | format_currency }}円 | {{ stock.current_price | format_currency }}円 | {{ stock.pl | format_currency }}円 |
{% endfor %}
| **合計** | - | - | **{% set jp_total_pl = jp_list | map(attribute='pl') | sum %}{{ jp_total_pl | format_currency }}円** |

{% for stock in jp_list %}
### {{ stock.name }}の値動き

{% if chart_images and chart_images.stocks and chart_images.stocks[stock.symbol] %}
![{{ stock.name }}の株価推移]({{ chart_images.stocks[stock.symbol] }})

*出典: [Yahoo!ファイナンス]({{ chart_images.citations[stock.symbol] }})*
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

{% endfor %}
{% else %}
*日本株の保有銘柄はありません*
{% endif %}

## 今月の状況【外国株】（{{ year }}/{{ month_num }}/末）

{% set foreign_list = holdings | selectattr('is_foreign', 'equalto', True) | list %}
{% if foreign_list %}
### 保有状況（外国株）

| 銘柄 | 数量 | 平均取得価額 | 為替 | 合計（円） |
|------|------|------------|------|----------|
{% for stock in foreign_list %}
| {{ stock.name }}（{{ stock.symbol }}） | {{ stock.shares }}株 | {{ stock.cost_price | format_number(2) }}{{ stock.currency }} | {{ stock.exchange_rate | format_number(2) }}円 | {{ stock.cost | format_currency }}円 |
{% endfor %}

{% for stock in foreign_list %}
{% if stock.purchase_history %}
<details>
<summary>{{ stock.name }}の購入履歴を見る</summary>

| 回 | 数量 | 取得価額 | 為替 | 購入日 |
|----|------|---------|------|--------|
{% for ph in stock.purchase_history %}
| {{ ph.seq }} | {{ ph.shares }}株 | {{ ph.price_foreign | format_number(2) }}{{ stock.currency }} | {{ ph.exchange_rate | format_number(2) }}円 | {{ ph.purchased_at }} |
{% endfor %}

</details>
{% endif %}
{% endfor %}

### 月末時点損益

| 銘柄 | 取得価額 | 現在価額 | 為替 | 損益（円） |
|------|---------|---------|------|----------|
{% for stock in foreign_list %}
| {{ stock.name }} | {{ stock.cost_price | format_number(2) }}{{ stock.currency }} | {{ stock.current_price | format_number(2) }}{{ stock.currency }} | {{ stock.exchange_rate | format_number(2) }}円 | {{ stock.pl | format_currency }}円 |
{% endfor %}

{% for stock in foreign_list %}
### {{ stock.name }}の値動き

{% if chart_images and chart_images.stocks and chart_images.stocks[stock.symbol] %}
![{{ stock.name }}の株価推移]({{ chart_images.stocks[stock.symbol] }})

*出典: [Yahoo!ファイナンス]({{ chart_images.citations[stock.symbol] }})*
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

{% endfor %}
{% else %}
*外国株の保有銘柄はありません*
{% endif %}

## まとめ

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

みなさんもポケモン銘柄へお布施投資しましょう！

---

*このレポートは自動生成されました*
