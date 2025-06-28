#!/bin/bash

# AI Diary Get Info Service テストスクリプト
# DB接続テストと基本的なAPIテストを実行します

set -e

echo "=== AI Diary Get Info Service テスト開始 ==="

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

# 仮想環境をアクティブ化
if [[ -f "venv/bin/activate" ]]; then
    echo "仮想環境をアクティブ化中..."
    source venv/bin/activate
else
    echo "仮想環境が見つかりません"
    exit 1
fi

echo "=== DB接続テスト実行 ==="
cd get_info
python test_service.py

echo ""
echo "=== API テスト ==="
echo "Cloud SQL Proxyが起動していることを確認してください:"
echo "cloud_sql_proxy -instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306"
echo ""
echo "テスト完了" 