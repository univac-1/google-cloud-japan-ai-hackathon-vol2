#!/bin/bash

# ローカル開発環境セットアップスクリプト

set -e

echo "🔧 AnpiCall Email Service - ローカル開発環境セットアップ"
echo ""

# Python仮想環境の作成
if [ ! -d "venv" ]; then
    echo "📦 Python仮想環境を作成中..."
    python3.12 -m venv venv
fi

# 仮想環境のアクティベート
echo "🚀 仮想環境をアクティベート中..."
source venv/bin/activate

# パッケージのインストール
echo "📥 依存関係をインストール中..."
pip install -r requirements.txt

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "🎯 次のステップ:"
echo "   1. ローカルテスト: ./local_server.py"
echo "   2. GCPデプロイ: ./deploy.sh YOUR_SENDGRID_API_KEY"
echo "   3. APIテスト: ./test_email.py FUNCTION_URL"
echo ""
echo "💡 ローカルサーバー起動後:"
echo "   http://localhost:8080 でテスト可能"
