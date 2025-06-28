#!/bin/bash

# メール送信API単体テスト

echo "=== メール送信API単体テスト ==="

echo "テスト用メールアドレス: 5jpbnd@gmail.com"
echo

echo "=== メール送信テスト開始 ==="
curl -X GET http://localhost:8080/test-email | python3 -m json.tool

echo
echo "=== テスト完了 ==="
