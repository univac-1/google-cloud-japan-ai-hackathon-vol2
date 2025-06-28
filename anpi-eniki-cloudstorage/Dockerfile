# Pythonの公式イメージをベースにする
FROM python:3.13-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# アプリケーションがリッスンするポートを定義
ENV PORT 8080

# アプリケーションを実行
CMD ["flask", "run", "--host=0.0.0.0","--port", "8080"]