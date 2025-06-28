#!/bin/bash

# AI Diary Get Info Service 起動スクリプト
# 必要な環境変数を設定してサービスを起動します

set -e

echo "=== AI Diary Get Info Service 起動準備 ==="

# 🚨 Cloud SQL Proxy起動チェック
echo "=== 🔍 データベース接続チェック ==="
if ! ps aux | grep -q "[c]loud_sql_proxy"; then
    echo "❌ Cloud SQL Proxyが起動していません！"
    echo ""
    echo "📋 データベース接続に必要な操作："
    echo "1. 新しいターミナルを開く"
    echo "2. 以下のコマンドを実行："
    echo "   cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306"
    echo "3. 'Ready for new connections' のメッセージを確認後、Enterキーを押してください"
    echo ""
    read -p "⏸️  Cloud SQL Proxyを起動後、Enterキーを押してください..."
    
    # 再チェック
    if ! ps aux | grep -q "[c]loud_sql_proxy"; then
        echo "❌ まだCloud SQL Proxyが検出されません。起動を確認してから再実行してください。"
        exit 1
    fi
fi
echo "✅ Cloud SQL Proxy は起動中です"

# 基本設定の読み込み
if [[ -f ".env" ]]; then
    echo ".envを読み込み中..."
    source .env
else
    echo ".envファイルが見つかりません"
    exit 1
fi

# 必要な環境変数を設定
export GOOGLE_CLOUD_PROJECT=${PROJECT_ID}
export DB_HOST=${DB_HOST}
export DB_PORT=${DB_PORT}
export DB_NAME=${DB_NAME}
export DB_USER=${DB_USER}
export DB_PASSWORD=${DB_PASSWORD}
export GEMINI_API_KEY=${GEMINI_API_KEY}

echo "=== 環境変数確認 ==="
echo "GOOGLE_CLOUD_PROJECT: ${GOOGLE_CLOUD_PROJECT}"
echo "DB_HOST: ${DB_HOST}"
echo "DB_PORT: ${DB_PORT}"
echo "DB_NAME: ${DB_NAME}"
echo "DB_USER: ${DB_USER}"
echo "DB_PASSWORD: ***"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."

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