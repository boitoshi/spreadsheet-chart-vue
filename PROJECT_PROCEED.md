# 📁 プロジェクト進行状況と今後の計画

## 🎯 2025年7月20日完了済み項目

### ✅ 時系列精度向上（重要）
- **時系列を正確に考慮した損益計算ロジック完成**: 取得時期以前の期間での損益計算を排除し、webサイト公開レベルの正確性を実現
- **銘柄別表示期間制御の実装**: 個別銘柄選択時に取得開始時期以降のデータのみ表示
- **データ品質保証と妥当性検証機能**: 包括的なデータ検証とリアルタイム品質監視

### 🔧 技術実装完了
- Django Cloud Run デプロイメント完成
- Google Sheets API 統合とエラーハンドリング
- Vue.js フロントエンドとCloud Run バックエンドの連携
- 3ライン表示チャート（取得価格・評価額・損益推移）

## ⚠️ 現在の課題（次回優先対応）

### 🚨 高優先度
1. **総損益推移の全銘柄統合**: 現在は任天堂のみ、DeNAとエヌビディアも含める必要あり
2. **銘柄別損益推移グラフ非表示問題**: 個別銘柄選択時にグラフが表示されない

### 📊 中優先度  
3. **フロントエンドでの個別銘柄データ取得**: 新しいAPIエンドポイントとの完全連携
4. **全銘柄統合チャートのパフォーマンス最適化**

## 🔍 既存の構成課題

### 1. 構成の課題
- バックエンドとフロントエンドが同階層で分かりにくい
- テンプレートとドキュメントの配置が散らばっている
- 環境設定ファイルの管理が複雑

### 2. ファイル管理の課題
- 重複するコンポーネント（LineChart2.vue, Spreadsheet2.vue）
- 不要なREADME.mdファイル
- サンプルファイル（hello.py）の残存

## 🎯 最適化提案

### プロポーザル A: モノレポ構成（推奨）
```
portfolio-tracker/
├── apps/                           # アプリケーション本体
│   ├── frontend/                   # Vue.js アプリ
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── charts/         # チャート系コンポーネント
│   │   │   │   │   ├── LineChart.vue
│   │   │   │   │   └── ProfitChart.vue
│   │   │   │   ├── portfolio/      # ポートフォリオ系
│   │   │   │   │   ├── PortfolioDashboard.vue
│   │   │   │   │   ├── StockTable.vue
│   │   │   │   │   └── Spreadsheet.vue
│   │   │   │   ├── export/         # エクスポート系
│   │   │   │   │   └── BlogExport.vue
│   │   │   │   └── ui/             # 共通UI
│   │   │   │       ├── Button.vue
│   │   │   │       ├── Modal.vue
│   │   │   │       └── Loading.vue
│   │   │   ├── views/              # ページコンポーネント
│   │   │   ├── composables/        # ビジネスロジック
│   │   │   ├── services/           # API通信
│   │   │   ├── types/              # TypeScript型定義
│   │   │   └── assets/
│   │   ├── public/
│   │   └── tests/                  # テストファイル
│   └── backend/                    # Django API
│       ├── config/                 # Django設定
│       │   ├── settings/
│       │   │   ├── base.py
│       │   │   ├── development.py
│       │   │   └── production.py
│       │   ├── urls.py
│       │   └── wsgi.py
│       ├── apps/                   # Django アプリ
│       │   ├── portfolio/          # ポートフォリオ管理
│       │   │   ├── models.py
│       │   │   ├── views.py
│       │   │   ├── serializers.py
│       │   │   └── urls.py
│       │   ├── reports/            # レポート生成
│       │   │   ├── models.py
│       │   │   ├── views.py
│       │   │   ├── generators.py
│       │   │   └── urls.py
│       │   └── sheets/             # Google Sheets連携
│       │       ├── services.py
│       │       ├── updater.py
│       │       └── views.py
│       ├── templates/              # HTMLテンプレート
│       └── tests/
├── tools/                          # 開発・運用ツール
│   ├── scripts/                    # 便利スクリプト
│   │   ├── setup.sh
│   │   ├── deploy.sh
│   │   └── backup.sh
│   ├── docker/                     # Docker設定
│   │   ├── Dockerfile.frontend
│   │   ├── Dockerfile.backend
│   │   └── docker-compose.yml
│   └── ci/                         # CI/CD設定
├── shared/                         # 共通リソース
│   ├── types/                      # TypeScript型定義
│   ├── constants/                  # 定数
│   └── utils/                      # 共通ユーティリティ
├── docs/                           # ドキュメント
│   ├── api/                        # API仕様書
│   ├── guides/                     # 利用ガイド
│   ├── archives/                   # 月次レポートアーカイブ
│   │   └── reports/
│   │       ├── 2024/
│   │       └── templates/
│   └── assets/                     # ドキュメント用画像
├── config/                         # プロジェクト設定
│   ├── .env.example
│   ├── .gitignore
│   └── package.json               # workspace設定
└── README.md
```

### プロポーザル B: シンプル構成（現行改善版）
```
portfolio-tracker/
├── client/                         # フロントエンド
│   ├── src/
│   │   ├── components/
│   │   │   ├── chart/             # チャート関連
│   │   │   ├── portfolio/         # ポートフォリオ関連
│   │   │   ├── report/            # レポート関連
│   │   │   └── common/            # 共通コンポーネント
│   │   ├── pages/                 # ページ（views → pages）
│   │   ├── hooks/                 # composables → hooks
│   │   ├── api/                   # サービス層
│   │   └── utils/
│   └── public/
├── server/                         # バックエンド
│   ├── core/                      # Django設定
│   ├── api/                       # APIアプリ
│   │   ├── portfolio/
│   │   ├── reports/
│   │   └── sheets/
│   └── templates/
├── shared/                         # 共通
│   ├── types/
│   └── constants/
├── docs/
│   ├── reports/                   # アーカイブ
│   └── guides/
├── scripts/                       # ユーティリティ
└── config/                        # 設定ファイル
```

## 🔧 実装手順

### Phase 1: 基本清理
- [x] 重複ファイルの削除（LineChart2.vue, Spreadsheet2.vue）
- [x] 不要ファイルの削除（各README.md, hello.py）
- [x] .gitignoreの統合とルート移動

### Phase 2: コンポーネント整理（推奨）
```bash
# フロントエンド構造変更
mkdir -p frontend/src/components/{charts,portfolio,export,ui}
mv frontend/src/components/LineChart.vue frontend/src/components/charts/
mv frontend/src/components/ProfitChart.vue frontend/src/components/charts/
mv frontend/src/components/PortfolioDashboard.vue frontend/src/components/portfolio/
mv frontend/src/components/StockTable.vue frontend/src/components/portfolio/
mv frontend/src/components/Spreadsheet.vue frontend/src/components/portfolio/
mv frontend/src/components/BlogExport.vue frontend/src/components/export/
```

### Phase 3: バックエンド構造変更
```bash
# Django アプリの分割
cd backend
python manage.py startapp portfolio
python manage.py startapp reports
# 既存のsheets_apiをsheetsにリネーム
```

### Phase 4: 設定ファイルの整理
```bash
# 設定ディレクトリの作成
mkdir config
mv .env.example config/
# workspace package.json作成（モノレポの場合）
```

## 📊 比較表

| 項目 | 現在 | プロポーザルA | プロポーザルB |
|------|------|---------------|---------------|
| 理解しやすさ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 保守性 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| スケーラビリティ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 移行コスト | - | ⭐⭐ | ⭐⭐⭐⭐ |
| チーム開発 | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🎯 推奨案

**プロポーザル A（モノレポ構成）** を推奨します。

### 理由
1. **明確な責任分離**: フロントエンド・バックエンドの境界が明確
2. **機能別整理**: コンポーネントが機能ごとに整理される
3. **拡張性**: 新機能追加時の構造が明確
4. **保守性**: ファイルの場所が予測しやすい
5. **チーム開発**: 複数人での開発に適している

### 次のステップ
1. コンポーネントの機能別分類実装
2. バックエンドのアプリケーション分割
3. 共通設定ファイルの整理
4. ドキュメントの再構成

## 🚨 注意点

- **段階的移行**: 一度に全てを変更せず、段階的に実装
- **import文の更新**: ファイル移動に伴うimport文の修正が必要
- **テストの更新**: ファイルパス変更に伴うテスト修正
- **CI/CDの調整**: ビルドパスの変更が必要

---

どちらの提案も現在の構成より大幅に改善されます。プロジェクトの規模と将来性を考慮して選択してください。