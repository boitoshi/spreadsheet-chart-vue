# 月次レポートアーカイブ

このディレクトリには、過去の月次投資成績レポートが保存されています。

## ディレクトリ構成

```
monthly-reports/
├── README.md                 # このファイル
├── 2024/
│   ├── 2024-01/
│   │   ├── report.html      # HTMLレポート
│   │   ├── report.md        # Markdownレポート
│   │   ├── data.json        # レポートデータ（JSON）
│   │   └── charts/          # チャート画像
│   │       ├── portfolio-chart.png
│   │       └── profit-chart.png
│   ├── 2024-02/
│   └── ...
└── templates/
    ├── report-template.html  # HTMLテンプレート
    └── blog-template.md      # ブログテンプレート
```

## ファイル説明

### レポートファイル
- **report.html**: ブラウザで表示可能なHTMLレポート
- **report.md**: Markdownフォーマットのレポート（ブログ投稿用）
- **data.json**: レポート生成に使用したデータ（JSON形式）

### チャート画像
- **portfolio-chart.png**: ポートフォリオ構成チャート
- **profit-chart.png**: 損益推移チャート
- **asset-chart.png**: 資産推移チャート

## 使用方法

### 新しいレポートの生成
1. Vue.jsアプリケーションの月次レポート画面でデータを確認
2. 「エクスポート」ボタンから希望の形式を選択
3. 生成されたファイルを適切なディレクトリに保存

### 過去のレポートの閲覧
- HTMLファイルをブラウザで直接開く
- Markdownファイルをテキストエディタで開く
- JSONファイルでデータを確認

## ブログ投稿手順

1. **Markdownレポートの確認**
   ```bash
   # 例: 2024年1月のレポート
   cat docs/monthly-reports/2024/2024-01/report.md
   ```

2. **画像ファイルの準備**
   - `charts/` ディレクトリの画像をブログにアップロード
   - Markdownファイル内の画像パスを更新

3. **ブログ投稿**
   - Markdownの内容をブログエディタにコピー
   - 画像を適切な位置に配置
   - タグとカテゴリを設定

## テンプレート

### HTMLテンプレート (report-template.html)
- レスポンシブデザイン対応
- 印刷対応スタイル
- ソーシャルシェア機能

### Markdownテンプレート (blog-template.md)
- ブログ投稿に最適化
- SEO対応のメタデータ
- 読みやすいフォーマット

## データ保持ポリシー

- 月次レポートは永続的に保存
- 年単位でディレクトリを分割
- 古いデータの圧縮は年末に実施

## バックアップ

重要な投資記録のため、以下の方法でバックアップを推奨：

1. **Gitリポジトリ**: このディレクトリ全体をGit管理
2. **クラウドストレージ**: Google Drive, Dropbox等で同期
3. **外部メディア**: 定期的にUSBメモリ等に保存

## 注意事項

- 個人の投資情報が含まれるため、公開リポジトリでの管理は避ける
- センシティブな情報（具体的な金額等）は必要に応じてマスク
- レポートの正確性について、生成時のデータを必ず確認

## 更新履歴

- 2024-01-01: アーカイブディレクトリ作成
- 2024-01-31: 初回月次レポート保存