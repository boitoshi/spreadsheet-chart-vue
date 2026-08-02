#!/usr/bin/env bash
# GCE 上で実行するデプロイスクリプト
# GitHub Actions（.github/workflows/deploy.yml）から SSH 経由で標準入力渡しで実行される。
# 手動デプロイ時も GCE 上で `bash portfolio-dashboard/deploy/deploy.sh` として使える。
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"

# 非対話 SSH では fnm の node / ~/.local/bin の uv に PATH が通っていないため明示する
export PATH="$HOME/.local/share/fnm/aliases/default/bin:$HOME/.local/bin:$PATH"

# リポジトリ直下デプロイ（/app/portfolio-dashboard/...）と
# portfolio-dashboard 直置きデプロイ（/app/server など）の両レイアウトに対応
if [ -d "$APP_DIR/portfolio-dashboard" ]; then
  DASHBOARD_DIR="$APP_DIR/portfolio-dashboard"
else
  DASHBOARD_DIR="$APP_DIR"
fi

echo "=== デプロイ開始: APP_DIR=$APP_DIR DASHBOARD_DIR=$DASHBOARD_DIR ==="

# 1. DB バックアップ（失敗したらデプロイ中断。SKIP_BACKUP=1 で省略可）
if [ "${SKIP_BACKUP:-0}" != "1" ] && [ -f "$DASHBOARD_DIR/deploy/backup.sh" ]; then
  echo "[1/6] DB バックアップ"
  DB_PATH="${DB_PATH:-$DASHBOARD_DIR/data/portfolio.db}" \
    bash "$DASHBOARD_DIR/deploy/backup.sh"
else
  echo "[1/6] DB バックアップ: スキップ"
fi

# 2. 最新コードの取得
echo "[2/6] git pull"
git -C "$APP_DIR" pull --ff-only

# 3. 依存インストールとビルド
echo "[3/6] npm ci && build"
cd "$DASHBOARD_DIR"
npm ci
npm run build

# 4. DB マイグレーション（冪等）
echo "[4/6] db:migrate"
npm run db:migrate -w server

# 5. サービス再起動（deploy ユーザーに NOPASSWD 設定が必要。docs 参照）
echo "[5/6] systemctl restart portfolio"
sudo systemctl restart portfolio

# 6. collector 依存の同期（素の uv sync は extras を消すため必ず extras 付き）
echo "[6/6] uv sync --extra ai --extra charts"
cd "$DASHBOARD_DIR/collector"
uv sync --extra ai --extra charts

# ヘルスチェック（起動待ちしてから確認）
sleep 3
curl -fsS http://localhost:3000/health
echo ""
echo "=== デプロイ完了: $(date) ==="
