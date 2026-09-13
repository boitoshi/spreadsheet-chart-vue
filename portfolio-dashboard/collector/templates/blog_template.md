{% set intro = ai_comments.intro if ai_comments is defined and ai_comments.intro else none %}
{% set stock_comments = ai_comments.stock_comments if ai_comments is defined and ai_comments.stock_comments else {} %}
<!-- pokebros-monthly-section:start:native-intro -->
{% if intro %}
## 今月の振り返り

{{ intro | escape_markdown }}
{% endif %}
<!-- pokebros-monthly-section:end:native-intro -->
{% for holding in holdings %}
{% set comment = stock_comments.get(holding.symbol) %}
{% if comment %}
<!-- pokebros-monthly-section:start:native-stock:{{ holding.symbol }} -->
### {{ holding.name }}の振り返り

{{ comment | escape_markdown }}
<!-- pokebros-monthly-section:end:native-stock:{{ holding.symbol }} -->
{% endif %}
{% endfor %}
<!-- pokebros-monthly-section:start:native-tail -->
## 関連リンク

- ポートフォリオの全体像: [【株】ポケモンポートフォリオ](https://www.pokebros.net/pokemon-investment-portfolio/)
- 保有状況をリアルタイムで見る: [ポケモン投資ダッシュボード](https://portfolio.pokebros.net/)
- 前月のレポート: [【ポケモン投資】{{ prev_month.year }}年{{ prev_month.month }}月の状況](https://www.pokebros.net/{{ prev_month.slug }}/)
- これまでのレポート: [【ポケモン投資】の記事一覧](https://www.pokebros.net/category/%e3%83%9d%e3%82%b1%e3%83%a2%e3%83%b3%e6%8a%95%e8%b3%87/)

## 1株からポケモン関連銘柄を買うには

単元未満株が買える証券会社なら、1株からポケモン関連銘柄に投資できます。

証券会社のサイトから直接開設する前に、ポイントサイト経由の対象になっていないか確認するのがおすすめです。

ハピタスを利用する場合は、先に会員登録し、ハピタス内の証券会社ページから申し込みます。ポイント獲得条件を確認してから手続きを進めると安心です。

- 証券口座（ハピタス紹介リンク）: [SBI証券](https://m.hapitas.jp/item/detail/itemid/53979?i=22359663&route=spText&apn=itemsharelink) / [楽天証券](https://m.hapitas.jp/item/detail/itemid/35520?i=22359663&route=spText&apn=itemsharelink) / [マネックス証券](https://m.hapitas.jp/item/detail/itemid/99234?i=22359663&route=spText&apn=itemsharelink)
- ポイントサイト: [ハピタス（紹介リンク）](https://hapitas.jp/appinvite?i=22359663&route=text)

対象条件やもらえるポイントは時期によって変わるため、申し込み前に各ページの最新条件を確認してください。

上のリンクは紹介リンクです。紹介した側と紹介された側の両方が特典の対象になる場合があります。

※本記事は筆者個人の保有記録であり、特定の銘柄の売買を推奨するものではありません。投資判断はご自身の責任でお願いします。
<!-- pokebros-monthly-section:end:native-tail -->
