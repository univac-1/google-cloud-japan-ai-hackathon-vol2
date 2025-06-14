#!/bin/bash

# GCP Secret Manager を使用したGmail API認証情報管理
# 本格運用時のセキュリティ強化スクリプト

PROJECT_ID="univac-aiagent"
SECRET_NAME="google-service-account-key"
FROM_EMAIL_SECRET="gmail-from-email"

echo "🔐 GCP Secret Manager セットアップ (Gmail API)"
echo "=============================================="

# Secret Manager APIの有効化
echo "📋 Secret Manager APIを有効化中..."
gcloud services enable secretmanager.googleapis.com

# Gmail APIの有効化
echo "📋 Gmail APIを有効化中..."
gcloud services enable gmail.googleapis.com

# サービスアカウントキーファイルのパス入力
read -p "サービスアカウントキーのJSONファイルパスを入力してください: " key_file_path

if [ ! -f "$key_file_path" ]; then
    echo "❌ ファイルが見つかりません: $key_file_path"
    exit 1
fi

# Secret Managerにシークレットを作成・保存
echo "🔐 サービスアカウントキーをSecret Managerに保存中..."
gcloud secrets create $SECRET_NAME --data-file="$key_file_path"

echo "🔐 送信者メールアドレスをSecret Managerに保存中..."
echo -n "thistle0420@gmail.com" | gcloud secrets create $FROM_EMAIL_SECRET --data-file=-

# Cloud Functionに必要な権限を付与
SERVICE_ACCOUNT="mail-function-sa@${PROJECT_ID}.iam.gserviceaccount.com"

echo "🔐 サービスアカウントに権限を付与中..."
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding $FROM_EMAIL_SECRET \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

echo "✅ Secret Manager セットアップ完了"
echo ""
echo "📋 次のステップ:"
echo "1. Gmail APIの認証設定を完了"
echo "2. ドメイン全体の委任設定（必要に応じて）"
echo "3. Cloud Functionを再デプロイ"
echo ""
echo "📖 詳細な設定方法は gmail_setup_guide.md を参照してください"
