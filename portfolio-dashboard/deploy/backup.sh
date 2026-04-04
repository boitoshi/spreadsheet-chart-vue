#!/bin/bash
# SQLite → GCS 日次バックアップ
set -euo pipefail

DB_PATH="${DB_PATH:-/app/data/portfolio.db}"
BUCKET="${GCS_BACKUP_BUCKET:-gs://portfolio-backup}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_TMP="/tmp/portfolio_backup.db"

# DB ファイルの存在確認
if [ ! -f "$DB_PATH" ]; then
    echo "ERROR: DB ファイルが見つかりません: $DB_PATH"
    exit 1
fi

# SQLite の安全なバックアップ（.backup コマンドで一貫性保証）
sqlite3 "$DB_PATH" ".backup $BACKUP_TMP"
echo "バックアップ作成完了: $BACKUP_TMP"

# GCS にアップロード
gsutil cp "$BACKUP_TMP" "$BUCKET/portfolio_${TIMESTAMP}.db"
echo "GCS アップロード完了: $BUCKET/portfolio_${TIMESTAMP}.db"

# 30日以前のバックアップを削除（最新30件を保持）
OLD_FILES=$(gsutil ls "$BUCKET/portfolio_*.db" 2>/dev/null | sort | head -n -30)
if [ -n "$OLD_FILES" ]; then
    echo "$OLD_FILES" | xargs gsutil rm
    echo "古いバックアップを削除しました"
fi

# 一時ファイル削除
rm -f "$BACKUP_TMP"
echo "バックアップ完了: $(date)"
