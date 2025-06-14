#!/bin/bash

# 環境変数設定スクリプト
echo "🔧 環境変数設定"
echo "=================="

# Gmail API Service Account Keyの設定
if [ -z "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
    echo "📧 Gmail API Service Account Keyを設定してください:"
    echo ""
    echo "1. Google Cloud Console (https://console.cloud.google.com/) にログイン"
    echo "2. IAM & Admin > Service Accounts > Create Service Account"  
    echo "3. Gmail API権限を設定"
    echo "4. JSONキーファイルをダウンロード"
    echo "5. JSONファイルの内容を1行の文字列として貼り付け"
    echo ""
    echo "JSONキーファイルの内容を貼り付けてください:"
    read -p "Service Account Key (JSON): " service_key
    
    if [ -n "$service_key" ]; then
        export GOOGLE_SERVICE_ACCOUNT_KEY="$service_key"
        echo "✅ GOOGLE_SERVICE_ACCOUNT_KEY を設定しました"
    else
        echo "❌ Service Account Keyが入力されませんでした"
        exit 1
    fi
else
    echo "✅ GOOGLE_SERVICE_ACCOUNT_KEY は既に設定されています"
fi

# 送信者メールアドレスの設定
if [ -z "$FROM_EMAIL" ]; then
    echo ""
    echo "📮 送信者メールアドレスを設定してください:"
    echo "    echo "   (Google Service AccountのメールアドレスまたはGoogle Workspaceで委任設定したもの)""
    echo "   (空欄の場合は noreply@example.com を使用)"
    read -p "送信者メールアドレス: " from_email
    
    if [ -n "$from_email" ]; then
        export FROM_EMAIL="$from_email"
        echo "✅ FROM_EMAIL を $from_email に設定しました"
    else
        export FROM_EMAIL="noreply@example.com"
        echo "⚠️  FROM_EMAIL をデフォルト値に設定しました: noreply@example.com"
    fi
else
    echo "✅ FROM_EMAIL は既に設定されています: $FROM_EMAIL"
fi

echo ""
echo "📋 現在の環境変数:"
echo "  GOOGLE_SERVICE_ACCOUNT_KEY: ${GOOGLE_SERVICE_ACCOUNT_KEY:0:30}..." # 最初の30文字のみ表示
echo "  FROM_EMAIL: $FROM_EMAIL"
echo ""
echo "🚀 次のステップ:"
echo "  ./setup_and_deploy.sh を実行してデプロイしてください"

# 環境変数を.envファイルに保存（オプション）
read -p "環境変数を .env ファイルに保存しますか？ (y/n): " save_env
if [[ "$save_env" =~ ^[Yy]$ ]]; then
    cat > .env << EOF
export GOOGLE_SERVICE_ACCOUNT_KEY="$GOOGLE_SERVICE_ACCOUNT_KEY"
export FROM_EMAIL="$FROM_EMAIL"
EOF
    echo "✅ 環境変数を .env ファイルに保存しました"
    echo "   次回は 'source .env' で読み込めます"
fi
