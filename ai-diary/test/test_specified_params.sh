#!/bin/bash

# AI Diary API 指定パラメータテスト
# userID: 4CC0CA6A-657C-4253-99FF-C19219D30AE2
# callID: CA995a950a2b9f6623a5adc987d0b31131

echo "=== AI Diary API 指定パラメータテスト ==="
echo

# 🚨 Cloud SQL Proxy起動チェック
echo "=== 🔍 前提条件チェック ==="
if ! ps aux | grep -q "[c]loud_sql_proxy"; then
    echo "❌ Cloud SQL Proxyが起動していません！"
    echo ""
    echo "📋 必要な操作："
    echo "1. 新しいターミナルを開く"
    echo "2. 以下のコマンドを実行："
    echo "   cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306"
    echo "3. 'Ready for new connections' のメッセージを確認"
    echo "4. このスクリプトを再実行"
    echo ""
    echo "⚠️  Cloud SQL Proxyなしではデータベースに接続できません"
    exit 1
else
    echo "✅ Cloud SQL Proxy は起動中です"
fi

cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary
source venv/bin/activate

# 環境変数を直接設定
export GEMINI_API_KEY="AIzaSyBINVVUZhQVP3IS1ht1RBxguS9ajibSq-c"
export GOOGLE_CLOUD_PROJECT="univac-aiagent"
export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_NAME="default"
export DB_USER="default"
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="

# テスト用パラメータ
USER_ID="4CC0CA6A-657C-4253-99FF-C19219D30AE2"
CALL_ID="CA995a950a2b9f6623a5adc987d0b31131"

# Flaskアプリをポート8095で起動（バックグラウンド）
echo "Flaskアプリをポート8095で起動中..."
export PORT=8095
python main.py &
PID=$!

# 起動待機
echo "起動待機中（10秒）..."
sleep 10

echo
echo "=== 環境変数確認 ==="
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "GOOGLE_CLOUD_PROJECT: $GOOGLE_CLOUD_PROJECT"
echo "テストパラメータ:"
echo "  userID: $USER_ID"
echo "  callID: $CALL_ID"

echo
echo "=== 1. ヘルスチェック ==="
curl -s -X GET "http://localhost:8095/health" | python -m json.tool 2>/dev/null || echo "ヘルスチェック失敗"

echo
echo "=== 2. Gemini API テスト ==="
curl -s -X GET "http://localhost:8095/test-gemini" | python -m json.tool 2>/dev/null || echo "Gemini APIテスト失敗"

echo
echo "=== 3. 日記生成API テスト（指定パラメータ） ==="
curl -s -X POST "http://localhost:8095/generate-diary" \
  -H "Content-Type: application/json" \
  -d "{\"userID\": \"$USER_ID\", \"callID\": \"$CALL_ID\"}" | \
  python -m json.tool 2>/dev/null || echo "日記生成APIテスト失敗"

echo
echo "=== 4. ユーザー情報＋会話履歴取得テスト（指定パラメータ） ==="
curl -s -X POST "http://localhost:8095/get-user-and-conversation" \
  -H "Content-Type: application/json" \
  -d "{\"userID\": \"$USER_ID\", \"callID\": \"$CALL_ID\"}" | \
  python -m json.tool 2>/dev/null || echo "ユーザー情報＋会話履歴取得テスト失敗"

echo
echo "=== テスト完了 - プロセス終了 ==="
kill $PID 2>/dev/null
wait $PID 2>/dev/null || true

echo "指定パラメータでのテストが完了しました。"
