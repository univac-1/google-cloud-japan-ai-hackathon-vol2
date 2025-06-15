# Cloud Run Jobs 用 Dockerfile - 安否確認呼び出しスケジューラー
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新と必要なツールのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係ファイルをコピー
COPY requirements.txt .

# Pythonの依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY main.py .

# Cloud Run Jobs の環境変数を設定
ENV IS_CLOUD_RUN_JOB=true
ENV ENVIRONMENT=production
ENV LOG_LEVEL=info

# 非rootユーザーを作成して使用
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# バッチ処理を実行
CMD ["python", "main.py"]
