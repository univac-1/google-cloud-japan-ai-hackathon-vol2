#!/bin/bash

# AI Diary API 完全テストスクリプト

set -e

echo "=== AI Diary API 完全テスト ==="
echo

# 仮想環境と環境変数の設定
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary
source venv/bin/activate
source .env

# 利用可能なポートを探す
PORT=8090
while netstat -an | grep -q :$PORT; do
    PORT=$((PORT + 1))
done

echo "ポート $PORT を使用します"
export PORT=$PORT

# バックグラウンドでFlaskアプリを起動
echo "Flask アプリを起動中..."
python main.py &
FLASK_PID=$!

# サービスが起動するまで待機
echo "サービス起動を待機中..."
sleep 5

# ベースURL
BASE_URL="http://localhost:$PORT"

echo "=== テスト開始 ==="
echo

# 1. ヘルスチェック
echo "1. ヘルスチェック"
HEALTH_RESPONSE=$(curl -s -X GET "$BASE_URL/health" || echo "ERROR")
echo "レスポンス: $HEALTH_RESPONSE"
echo

# 2. Gemini API接続テスト
echo "2. Gemini API 接続テスト"
GEMINI_RESPONSE=$(curl -s -X GET "$BASE_URL/test-gemini" || echo "ERROR")
echo "レスポンス: $GEMINI_RESPONSE"
echo

# 3. 日記生成API テスト（ダミーデータ）
echo "3. 日記生成API テスト"
DIARY_RESPONSE=$(curl -s -X POST "$BASE_URL/generate-diary" \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "test_user_001",
    "callID": "test_call_001"
  }' || echo "ERROR")
echo "レスポンス: $DIARY_RESPONSE"
echo

# 4. ユーザー情報＋会話履歴取得テスト
echo "4. ユーザー情報＋会話履歴取得テスト"
USER_CONV_RESPONSE=$(curl -s -X POST "$BASE_URL/get-user-and-conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "test_user_001",
    "callID": "test_call_001"
  }' || echo "ERROR")
echo "レスポンス: $USER_CONV_RESPONSE"
echo

echo "=== テスト完了 ==="

# Flaskプロセスを終了
echo "Flaskアプリを終了中..."
kill $FLASK_PID 2>/dev/null || true
wait $FLASK_PID 2>/dev/null || true

echo "全てのテストが完了しました。"
