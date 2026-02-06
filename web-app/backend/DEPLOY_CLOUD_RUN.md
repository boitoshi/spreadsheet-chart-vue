# Cloud Run デプロイガイド

## 1. 前提条件

### 1.1 Google Cloud Platform 準備
- Google Cloud Platformアカウントの取得
- 新規プロジェクトの作成
- 課金アカウントの設定

### 1.2 必要なAPIの有効化
```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 1.3 gcloud CLI のインストール・認証
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 2. デプロイ手順

### 2.1 手動デプロイ（推奨）

#### Step 1: Docker イメージのビルド
```bash
cd /workspace/web-app/backend
docker build -t portfolio-backend .
```

#### Step 2: Google Container Registry へプッシュ
```bash
# プロジェクトIDを設定
export PROJECT_ID=YOUR_PROJECT_ID

# タグ付け
docker tag portfolio-backend gcr.io/$PROJECT_ID/portfolio-backend

# プッシュ
docker push gcr.io/$PROJECT_ID/portfolio-backend
```

#### Step 3: Cloud Run へデプロイ
```bash
gcloud run deploy portfolio-backend \
    --image gcr.io/$PROJECT_ID/portfolio-backend \
    --platform managed \
    --region asia-northeast1 \
    --allow-unauthenticated \
    --set-env-vars DEBUG=False \
    --set-env-vars GOOGLE_APPLICATION_CREDENTIALS=/app/my-service-account.json \
    --set-env-vars SPREADSHEET_ID=YOUR_SPREADSHEET_ID \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10
```

### 2.2 Cloud Build での自動デプロイ（オプション）

#### Step 1: Cloud Build の設定
```bash
gcloud builds submit --config cloudbuild.yaml
```

#### Step 2: GitHub連携（継続的デプロイ）
```bash
gcloud builds triggers create github \
    --repo-name YOUR_REPO_NAME \
    --repo-owner YOUR_GITHUB_USERNAME \
    --branch-pattern "^main$" \
    --build-config cloudbuild.yaml
```

## 3. 環境変数の設定

### 3.1 必要な環境変数
- `DEBUG`: False（本番環境）
- `SECRET_KEY`: Django秘密鍵（強力なものに変更）
- `ALLOWED_HOSTS`: デプロイ先のドメイン
- `GOOGLE_APPLICATION_CREDENTIALS`: サービスアカウントファイルのパス
- `SPREADSHEET_ID`: Google SheetsのID

### 3.2 環境変数の更新
```bash
gcloud run services update portfolio-backend \
    --region asia-northeast1 \
    --set-env-vars DEBUG=False,SECRET_KEY=your-secret-key
```

## 4. セキュリティ設定

### 4.1 サービスアカウントの作成
```bash
# サービスアカウント作成
gcloud iam service-accounts create portfolio-backend-sa \
    --display-name "Portfolio Backend Service Account"

# Google Sheets API 権限付与
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member serviceAccount:portfolio-backend-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --role roles/editor
```

### 4.2 Secret Manager の使用（推奨）
```bash
# Secret Manager API有効化
gcloud services enable secretmanager.googleapis.com

# シークレット作成
gcloud secrets create django-secret-key --data-file=secret-key.txt
gcloud secrets create google-service-account --data-file=my-service-account.json

# Cloud Run からのアクセス許可
gcloud secrets add-iam-policy-binding django-secret-key \
    --member serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL \
    --role roles/secretmanager.secretAccessor
```

## 5. 動作確認

### 5.1 デプロイ後の確認
1. Cloud Run コンソールでサービスの状態確認
2. 割り当てられたURLにアクセス
3. APIエンドポイントの動作確認

### 5.2 テストコマンド
```bash
# デプロイされたサービスのURL取得
SERVICE_URL=$(gcloud run services describe portfolio-backend \
    --region asia-northeast1 \
    --format "value(status.url)")

# API テスト
curl $SERVICE_URL/get_data/
```

## 6. 監視・ログ

### 6.1 ログの確認
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=portfolio-backend" --limit 50
```

### 6.2 メトリクスの確認
Cloud Consoleの「Cloud Run」→「portfolio-backend」→「メトリクス」で確認

## 7. 更新・メンテナンス

### 7.1 新しいバージョンのデプロイ
```bash
# 新しいイメージをビルド・プッシュ
docker build -t gcr.io/$PROJECT_ID/portfolio-backend:v2 .
docker push gcr.io/$PROJECT_ID/portfolio-backend:v2

# 新しいバージョンをデプロイ
gcloud run deploy portfolio-backend \
    --image gcr.io/$PROJECT_ID/portfolio-backend:v2 \
    --platform managed \
    --region asia-northeast1
```

### 7.2 ロールバック
```bash
# 以前のリビジョンにトラフィックを戻す
gcloud run services update-traffic portfolio-backend \
    --to-revisions REVISION_NAME=100 \
    --region asia-northeast1
```

## 8. 料金最適化

### 8.1 リソース設定の調整
- CPU: 1コア（軽量なAPIには十分）
- メモリ: 512Mi（スプレッドシートデータ処理に必要）
- 最小インスタンス: 0（コストを抑えるため）

### 8.2 料金監視
Cloud Consoleの「請求」で料金を監視し、予算アラートを設定

## 9. トラブルシューティング

### 9.1 よくある問題
- **CORS エラー**: CORS設定の確認
- **認証エラー**: サービスアカウントの権限確認
- **タイムアウト**: リクエストタイムアウトの設定
- **メモリ不足**: メモリ設定の増加

### 9.2 デバッグ
```bash
# コンテナ内でのデバッグ
docker run -it --entrypoint /bin/bash gcr.io/$PROJECT_ID/portfolio-backend

# 環境変数の確認
gcloud run services describe portfolio-backend --region asia-northeast1
```