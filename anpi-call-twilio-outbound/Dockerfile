# Python 3.11 slim イメージを使用
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムの依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# requirements.txtをコピーして依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY app/ .

# ポート設定（Cloud Runは動的にポートを割り当てるため、環境変数を使用）
EXPOSE 8080

# アプリケーションの起動
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
