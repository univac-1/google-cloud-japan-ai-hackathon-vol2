#!/bin/bash

# データベース接続状況チェックスクリプト

echo "🔍 AI Diary サービス データベース接続状況チェック"
echo "=" * 60

# 1. Cloud SQL Proxy プロセスチェック
echo "📊 1. Cloud SQL Proxy プロセス状況"
if ps aux | grep -q "[c]loud_sql_proxy"; then
    echo "✅ Cloud SQL Proxy は起動中です"
    echo "📋 プロセス詳細:"
    ps aux | grep "[c]loud_sql_proxy" | head -1
else
    echo "❌ Cloud SQL Proxy が起動していません"
    echo "📋 起動方法:"
    echo "   ./start_cloud_sql_proxy.sh"
    echo "   または："
    echo "   cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306"
fi

echo

# 2. ポート3306のリスニング状況チェック
echo "📊 2. ポート3306 接続待機状況"
if command -v ss >/dev/null 2>&1; then
    if ss -an | grep -q ":3306.*LISTEN"; then
        echo "✅ ポート3306でサービスが待機中です"
        ss -an | grep ":3306.*LISTEN"
    else
        echo "❌ ポート3306でサービスが待機していません"
    fi
elif command -v netstat >/dev/null 2>&1; then
    if netstat -an | grep -q ":3306.*LISTEN"; then
        echo "✅ ポート3306でサービスが待機中です"
        netstat -an | grep ":3306.*LISTEN"
    else
        echo "❌ ポート3306でサービスが待機していません"
    fi
else
    echo "⚠️  ポート確認ツール（ss/netstat）が利用できません"
fi

echo

# 3. 環境変数確認
echo "📊 3. 環境変数設定状況"
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary
source venv/bin/activate
source .env

if [ -n "$GEMINI_API_KEY" ]; then
    echo "✅ GEMINI_API_KEY: 設定済み (${GEMINI_API_KEY:0:10}...)"
else
    echo "❌ GEMINI_API_KEY: 未設定"
fi

if [ -n "$GOOGLE_CLOUD_PROJECT" ]; then
    echo "✅ GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
else
    echo "❌ GOOGLE_CLOUD_PROJECT: 未設定"
fi

if [ -n "$DB_PASSWORD" ]; then
    echo "✅ DB_PASSWORD: 設定済み"
else
    echo "❌ DB_PASSWORD: 未設定"
fi

echo

# 4. 簡単な接続テスト（仮想環境内でPythonスクリプト実行）
echo "📊 4. データベース接続テスト"
python3 -c "
import sys
sys.path.append('/home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary')
try:
    from get_info.db_connection import test_connection
    if test_connection():
        print('✅ データベース接続: 成功')
    else:
        print('❌ データベース接続: 失敗')
except Exception as e:
    print(f'❌ データベース接続テストエラー: {str(e)}')
"

echo
echo "🎯 接続確認完了"
echo "📋 問題がある場合は、上記の❌項目を修正してください"
