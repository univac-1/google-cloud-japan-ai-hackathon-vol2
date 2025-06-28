#!/bin/bash

# AI Diary API シンプルテスト

echo "=== AI Diary API テスト開始 ==="

cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary
source venv/bin/activate
source .env

# Flaskアプリをポート8090で起動（バックグラウンド）
echo "Flaskアプリをポート8090で起動中..."
export PORT=8090
python main.py &
PID=$!

# 起動待機
echo "起動待機中..."
sleep 8

echo
echo "=== 1. ヘルスチェック ==="
curl -s -X GET "http://localhost:8090/health" | python -m json.tool 2>/dev/null || echo "ヘルスチェック失敗"

echo
echo "=== 2. Gemini API テスト ==="
curl -s -X GET "http://localhost:8090/test-gemini" | python -m json.tool 2>/dev/null || echo "Gemini APIテスト失敗"

echo
echo "=== 3. 日記生成API テスト ==="
curl -s -X POST "http://localhost:8090/generate-diary" \
  -H "Content-Type: application/json" \
  -d '{"userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2", "callID": "CA995a950a2b9f6623a5adc987d0b31131"}' | \
  python -m json.tool 2>/dev/null || echo "日記生成APIテスト失敗"

echo
echo "=== テスト完了 - プロセス終了 ==="
kill $PID 2>/dev/null
wait $PID 2>/dev/null || true
