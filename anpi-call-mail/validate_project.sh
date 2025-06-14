#!/bin/bash

# プロジェクト検証スクリプト

set -e

echo "🔍 AnpiCall Email Service - プロジェクト検証"
echo "=" 50

# ファイル存在チェック
echo "📁 必要ファイルの確認..."
required_files=(
    "main.py"
    "requirements.txt" 
    "deploy.sh"
    "local_server.py"
    "test_email.py"
    "setup_local.sh"
    "run_tests.py"
    "Dockerfile"
    "docker-compose.yml"
    ".env.example"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (見つかりません)"
    fi
done

# 実行権限チェック
echo ""
echo "🔧 実行権限の確認..."
executable_files=(
    "deploy.sh"
    "local_server.py"
    "test_email.py"
    "setup_local.sh"
    "run_tests.py"
)

for file in "${executable_files[@]}"; do
    if [ -x "$file" ]; then
        echo "  ✅ $file (実行可能)"
    else
        echo "  ⚠️  $file (実行権限なし)"
        chmod +x "$file"
        echo "     → 実行権限を付与しました"
    fi
done

# 構文チェック
echo ""
echo "🐍 Python構文チェック..."
for py_file in *.py; do
    if python3 -m py_compile "$py_file" 2>/dev/null; then
        echo "  ✅ $py_file"
    else
        echo "  ❌ $py_file (構文エラー)"
    fi
done

echo ""
echo "📋 プロジェクト概要:"
echo "  - Python 3.12 対応"
echo "  - GCP Cloud Functions デプロイ可能"
echo "  - SendGrid API 連携"
echo "  - ローカル開発環境サポート"
echo "  - Docker コンテナ対応"
echo "  - 統合テスト機能"
echo ""
echo "🚀 次のステップ:"
echo "  1. ./setup_local.sh  # ローカル環境セットアップ"
echo "  2. ./local_server.py # ローカルサーバー起動"
echo "  3. ./deploy.sh API_KEY # GCPデプロイ"
echo ""
echo "✅ プロジェクト検証完了!"
