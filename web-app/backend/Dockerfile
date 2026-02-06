# Python公式イメージを使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージをインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# uvをインストール
RUN pip install uv

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# アプリケーションコードをコピー
COPY . .

# 静的ファイルを収集
RUN uv run python manage.py collectstatic --noinput

# 本番環境用の設定
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ポート8000で起動
EXPOSE 8000

# Gunicornで本番起動（シェル形式で環境変数展開を有効化）
CMD uv run gunicorn --bind 0.0.0.0:${PORT:-8000} backend.wsgi:application
