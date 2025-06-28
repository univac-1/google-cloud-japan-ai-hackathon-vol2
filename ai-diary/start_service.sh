#!/bin/bash

# AI Diary Get Info Service 起動スクリプト
# 必要な環境変数を設定してサービスを起動します

set -e

echo "=== AI Diary Get Info Service 起動準備 ==="

# 基本設定の読み込み
if [[ -f "config.env" ]]; then
    echo "config.envを読み込み中..."
    source config.env
else
    echo "config.envファイルが見つかりません"
    exit 1
fi

# 必要な環境変数を設定
export GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
export DB_HOST=${DB_HOST}
export DB_PORT=${DB_PORT}
export DB_NAME=${DB_NAME}
export DB_USER=${DB_USER}
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="

echo "=== 環境変数確認 ==="
echo "GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT}"
echo "DB_HOST: ${DB_HOST}"
echo "DB_PORT: ${DB_PORT}"
echo "DB_NAME: ${DB_NAME}"
echo "DB_USER: ${DB_USER}"
echo "DB_PASSWORD: ***"

# 仮想環境をアクティブ化
if [[ -f "venv/bin/activate" ]]; then
    echo "仮想環境をアクティブ化中..."
    source venv/bin/activate
else
    echo "仮想環境が見つかりません。まず以下を実行してください:"
    echo "python3 -m venv venv"
    echo "source venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

echo "=== AI Diary Get Info Service 起動 ==="
python main.py 