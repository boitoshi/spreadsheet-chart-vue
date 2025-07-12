# 投資ポートフォリオ管理ダッシュボード

Vue.js + Chart.jsで構築した投資ポートフォリオ管理システムのフロントエンド部分です。

## 🚀 主要機能

### 📊 ダッシュボード機能
- **保有銘柄一覧**: 平均取得価格・現在価格・損益を表示
- **詳細取引履歴**: 銘柄クリックで買い増しタイミングと価格を表示
- **ポートフォリオ構成**: 円グラフでパーセンテージ表示
- **総損益推移**: 期間選択可能な損益トレンド
- **銘柄別損益推移**: 個別銘柄の取得時期ベース推移

### 🎯 特徴
- **買い増し対応**: 複数回購入の平均価格自動計算
- **レスポンシブ対応**: PC・タブレット・スマホで最適表示
- **視覚的表現**: 利益=緑色、損失=赤色で直感的
- **取得時期表示**: 個別銘柄選択時に購入タイミングを強調

## 🛠️ 技術構成

- **Vue.js 3**: Composition API使用
- **Chart.js**: グラフ描画ライブラリ
- **Vite**: 開発サーバー・ビルドツール

## 📁 ファイル構成

```
src/
├── App.vue          # メインコンポーネント（全機能統合）
├── main.js          # エントリーポイント
└── style.css        # グローバルスタイル
```

## 🔧 開発環境セットアップ

### 前提条件
- Node.js 16以上
- npm

### インストール・起動
```bash
# 依存関係インストール
npm install

# 開発サーバー起動（ポート3000）
npm run dev

# ブラウザで http://localhost:3000/ にアクセス
```

### ビルド
```bash
# 本番用ビルド
npm run build

# プレビュー
npm run preview
```

## 📝 データ設定方法

### 銘柄データの変更
`src/App.vue` の `stocks` 配列を編集してください：

```javascript
const stocks = ref([
  {
    name: '銘柄名',           // 表示する銘柄名
    currentPrice: 2800,      // 現在の株価
    transactions: [          // 取引履歴（買い増し対応）
      { date: '2024/01/15', quantity: 50, price: 2400 },
      { date: '2024/03/10', quantity: 30, price: 2600 }
    ]
  }
])
```

### グラフデータの変更
損益推移のダミーデータは `profitData` と `stockProfitData` オブジェクトで設定：

```javascript
// 総損益推移用
const profitData = {
  '6months': {
    labels: ['1月', '2月', '3月', '4月', '5月', '6月'],
    data: [10000, 25000, 15000, 35000, 45000, 87500]
  }
}

// 銘柄別損益推移用  
const stockProfitData = {
  '銘柄名': {
    labels: ['2024/01/15', '2024/02/15', ...],  // 取得時期ベース
    data: [-6000, -3000, 12000, ...],           // 損益データ
    acquisitions: ['1回目購入', '', '2回目購入', ...] // 購入タイミング
  }
}
```

## 🎨 カスタマイズガイド

### 色の変更
グラフの色は以下で設定：
```javascript
const colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0']
```

### 通貨フォーマット
日本円以外に変更する場合：
```javascript
return value.toLocaleString() + '円'  // ← この部分を変更
```

### 期間選択オプション
期間選択プルダウンの変更：
```javascript
const profitData = {
  'custom_period': {  // ← 新しい期間を追加
    labels: [...],
    data: [...]
  }
}
```

## 🐛 トラブルシューティング

### よくある問題

1. **グラフが表示されない**
   - ブラウザのコンソールでエラーを確認
   - Chart.jsの登録を確認：`Chart.register(...registerables)`

2. **データが更新されない**
   - `stocks.value = newData` でリアクティブに更新
   - `ref()` で定義されているか確認

3. **レスポンシブが効かない**
   - Chart.jsオプションの `responsive: true` を確認
   - CSSの `@media` クエリを確認

4. **サーバーが起動しない**
   ```bash
   # プロセス確認・停止
   lsof -ti:3000 | xargs kill -9
   
   # 再起動
   npm run dev
   ```

## 📈 機能拡張のヒント

### APIとの連携
現在はダミーデータですが、実際のAPIと連携する場合：

1. `stocks.value` にAPI取得データを設定
2. 定期的にデータ更新する場合は `setInterval()` を使用
3. ローディング状態を `loading.value = true/false` で管理

### 新しいグラフ追加
Chart.jsの他のグラフタイプ（棒グラフ、エリアグラフ等）を追加可能：

```javascript
new Chart(canvasRef.value, {
  type: 'bar',  // 'line', 'pie', 'doughnut', 'bar' など
  data: { ... },
  options: { ... }
})
```

### データエクスポート機能
グラフ画像やCSVエクスポート機能も追加可能です。

## 📚 参考リンク

- [Vue.js 公式ドキュメント](https://vuejs.org/)
- [Chart.js 公式ドキュメント](https://www.chartjs.org/)
- [Vite 公式ドキュメント](https://vitejs.dev/)

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。