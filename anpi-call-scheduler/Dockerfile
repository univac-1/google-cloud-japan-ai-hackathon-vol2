FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# Pythonの依存関係をインストール
RUN pip install -r requirements.txt --use-feature=fast-deps

# アプリケーションコードをコピー
COPY main.py .

# 実行権限を付与
RUN chmod +x main.py

# ヘルスチェック用のコマンド
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "print('Health check passed')" || exit 1

# バッチ処理を実行
CMD ["python", "main.py"]
