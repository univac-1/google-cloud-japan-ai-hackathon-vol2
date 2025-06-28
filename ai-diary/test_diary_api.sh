#!/bin/bash

# AI Diary API テストスクリプト

BASE_URL="http://localhost:8080"

echo "=== AI Diary API テスト ==="
echo

# ヘルスチェック
echo "1. ヘルスチェック"
curl -s -X GET "$BASE_URL/health" | python -m json.tool
echo
echo

# Gemini API テスト
echo "2. Gemini API 接続テスト"
curl -s -X GET "$BASE_URL/test-gemini" | python -m json.tool
echo
echo

# 日記生成API テスト（サンプルデータ）
echo "3. 日記生成API テスト"
curl -s -X POST "$BASE_URL/generate-diary" \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "callID": "CA995a950a2b9f6623a5adc987d0b31131"
  }' | python -m json.tool
echo
echo

# ユーザー情報と会話履歴のみ取得
echo "4. ユーザー情報＋会話履歴のみ取得"
curl -s -X POST "$BASE_URL/get-user-and-conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "callID": "CA995a950a2b9f6623a5adc987d0b31131"
  }' | python -m json.tool

echo
echo "=== テスト完了 ==="
