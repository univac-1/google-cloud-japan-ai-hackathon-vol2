#!/bin/bash

# 完全な日記生成API（HTML生成含む）のテスト

echo "=== 完全な日記生成API（HTML生成含む）テスト ==="

# テスト用パラメータ（READMEで指定された固定値）
USER_ID="4CC0CA6A-657C-4253-99FF-C19219D30AE2"
CALL_ID="CA995a950a2b9f6623a5adc987d0b31131"

echo "ユーザーID: $USER_ID"
echo "コールID: $CALL_ID"
echo ""

# APIサーバーのベースURL
BASE_URL="http://localhost:8080"

echo "1. ヘルスチェック"
curl -s "$BASE_URL/health" | jq '.'
echo ""

echo "2. DB接続テスト"
curl -s "$BASE_URL/test-db" | jq '.'
echo ""

echo "3. Gemini API接続テスト"
curl -s "$BASE_URL/test-gemini" | jq '.'
echo ""

echo "4. HTML生成API接続テスト"
curl -s "$BASE_URL/test-html" | jq '.'
echo ""

echo "5. 完全な日記生成（ユーザー情報→会話履歴→日記→挿絵→HTML）"
curl -X POST "$BASE_URL/generate-diary" \
  -H "Content-Type: application/json" \
  -d "{\"userID\": \"$USER_ID\", \"callID\": \"$CALL_ID\"}" | jq '.'
echo ""

echo "=== テスト完了 ==="
