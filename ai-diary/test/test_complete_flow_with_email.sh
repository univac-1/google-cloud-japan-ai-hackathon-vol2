#!/bin/bash

# AI日記完全フロー + メール送信テスト
# ユーザー情報取得→会話履歴取得→日記生成→挿絵作成→HTML生成→メール送信

echo "=== AI日記完全フロー + メール送信テスト ==="

# 指定されたテスト用パラメータ
USER_ID="4CC0CA6A-657C-4253-99FF-C19219D30AE2"
CALL_ID="CA995a950a2b9f6623a5adc987d0b31131"

echo "使用するパラメータ:"
echo "  userID: $USER_ID"
echo "  callID: $CALL_ID"
echo "  email: 5jpbnd@gmail.com (ローカル動作確認用)"
echo

# 完全フローテスト
echo "=== 完全フロー (メール送信含む) テスト開始 ==="
curl -X POST http://localhost:8080/generate-diary \
  -H "Content-Type: application/json" \
  -d "{
    \"userID\": \"$USER_ID\",
    \"callID\": \"$CALL_ID\"
  }" | python3 -m json.tool

echo
echo "=== テスト完了 ==="
