#!/bin/bash

# Cloud SQL Proxy 起動ヘルパースクリプト
# データベース接続のための前提条件を自動で起動

echo "🚀 Cloud SQL Proxy 起動ヘルパー"
echo "=" * 50

# 既に起動しているかチェック
if ps aux | grep -q "[c]loud_sql_proxy"; then
    echo "✅ Cloud SQL Proxy は既に起動しています"
    echo "📊 プロセス情報:"
    ps aux | grep "[c]loud_sql_proxy"
    exit 0
fi

echo "📋 Cloud SQL Proxy を起動します..."
echo "⚠️  このスクリプトは前台で実行されます。"
echo "⚠️  終了するには Ctrl+C を押してください。"
echo "⚠️  別のターミナルでAPIテストを実行してください。"
echo

# 認証確認
echo "🔐 Google Cloud認証確認中..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "❌ Google Cloud認証が必要です"
    echo "📋 以下のコマンドで認証してください:"
    echo "   gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo "✅ 認証済み: $ACTIVE_ACCOUNT"

# Cloud SQL Proxy起動
echo "🔄 Cloud SQL Proxy を起動中..."
echo "📍 接続先: univac-aiagent:asia-northeast1:cloudsql-01"
echo "🔌 ローカルポート: 3306"
echo

cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
