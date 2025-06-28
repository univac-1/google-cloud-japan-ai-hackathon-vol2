#!/bin/bash
set -e

echo "=== 完全な一連処理のテスト ==="
echo "ユーザー情報取得→会話履歴取得→日記生成→挿絵作成の統合テスト"
echo

# サーバーが起動していることを確認
echo "サーバーの起動状況を確認中..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ サーバーが起動していません。main.pyを実行してください。"
    exit 1
fi
echo "✅ サーバーが起動中"

# 完全な処理をテスト
echo
echo "=== 完全な日記生成APIテスト ==="
python3 test_complete_flow.py

echo
echo "=== テスト完了 ==="
