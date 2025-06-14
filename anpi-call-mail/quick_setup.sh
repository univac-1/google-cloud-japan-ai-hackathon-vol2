#!/bin/bash

# SendGrid APIキー設定とデプロイのためのクイックセットアップ
# 
# 使用方法:
#   1. SendGridでAPIキーを取得
#   2. このスクリプトを実行
#   3. APIキーを入力してデプロイ

echo "🚀 SendGrid設定とデプロイ"
echo "========================="
echo ""

# APIキーの入力
read -p "SendGridのAPIキーを入力してください (SG.で始まる): " api_key

if [[ ! "$api_key" =~ ^SG\. ]]; then
    echo "❌ APIキーは 'SG.' で始まる必要があります"
    exit 1
fi

# 環境変数を設定
export SENDGRID_API_KEY="$api_key"
export FROM_EMAIL="thistle0420@gmail.com"

echo "✅ 環境変数を設定しました"
echo "   SENDGRID_API_KEY: ${api_key:0:10}..."
echo "   FROM_EMAIL: $FROM_EMAIL"
echo ""

# .envファイルを更新
cat > .env << EOF
export SENDGRID_API_KEY="$api_key"
export FROM_EMAIL="thistle0420@gmail.com"
EOF

echo "✅ .envファイルを更新しました"
echo ""

# デプロイ実行
echo "🚀 Cloud Functionをデプロイ中..."
./setup_and_deploy.sh

echo ""
echo "🧪 デプロイ完了後、テスト実行します..."
echo ""

# テスト実行
./test.sh "thistle0420@gmail.com" "山田" "花子" "090-1234-5678"
