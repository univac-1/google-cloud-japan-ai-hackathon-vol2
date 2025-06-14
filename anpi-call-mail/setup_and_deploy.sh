#!/bin/bash

# GCP リソース作成とデプロイの自動化スクリプト
set -e  # エラー時に停止

# プロジェクト設定
PROJECT_ID="univac-aiagent"
FUNCTION_NAME="send-mail"
REGION="asia-northeast1"
SERVICE_ACCOUNT_NAME="mail-function-sa"

echo "=== GCP Cloud Functions メール送信システム デプロイ開始 ==="
echo "プロジェクト: $PROJECT_ID"
echo "リージョン: $REGION"
echo "関数名: $FUNCTION_NAME"
echo ""

# 必要な環境変数の確認
if [ -z "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
    echo "❌ エラー: GOOGLE_SERVICE_ACCOUNT_KEY 環境変数が設定されていません"
    echo "以下のコマンドで設定してください:"
    echo "export GOOGLE_SERVICE_ACCOUNT_KEY='your_service_account_json_key_here'"
    exit 1
fi

if [ -z "$FROM_EMAIL" ]; then
    echo "⚠️  警告: FROM_EMAIL 環境変数が設定されていません"
    echo "デフォルト値 'noreply@example.com' を使用します"
    echo "カスタム送信者メールを設定する場合:"
    echo "export FROM_EMAIL=your_email@example.com"
    FROM_EMAIL="noreply@example.com"
fi

# GCPプロジェクトの設定
echo "🔧 GCPプロジェクトを設定中..."
gcloud config set project $PROJECT_ID

# 必要なAPIの有効化
echo "🔧 必要なAPIを有効化中..."
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable gmail.googleapis.com

# サービスアカウントの作成（既に存在する場合はスキップ）
echo "🔧 サービスアカウントを作成中..."
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="Mail Function Service Account" \
        --description="Service account for mail sending function"
    echo "✅ サービスアカウント作成完了"
else
    echo "ℹ️  サービスアカウントは既に存在します"
fi

# Cloud Functionのデプロイ
echo "🚀 Cloud Functionをデプロイ中..."
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=python311 \
    --region=$REGION \
    --source=. \
    --entry-point=send_mail \
    --trigger-http \
    --allow-unauthenticated \
    --service-account="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --set-env-vars="GOOGLE_SERVICE_ACCOUNT_KEY=$GOOGLE_SERVICE_ACCOUNT_KEY,FROM_EMAIL=$FROM_EMAIL" \
    --memory=256MB \
    --timeout=60s \
    --max-instances=10

# デプロイ結果の確認
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 デプロイ完了！"
    echo "=================================="
    
    # Function URLを取得
    FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.uri)")
    
    echo "📋 デプロイ情報:"
    echo "  関数名: $FUNCTION_NAME"
    echo "  プロジェクト: $PROJECT_ID"
    echo "  リージョン: $REGION"
    echo "  URL: $FUNCTION_URL"
    echo ""
    
    # URLをファイルに保存（テスト用）
    echo "$FUNCTION_URL" > function_url.txt
    echo "📁 Function URLを function_url.txt に保存しました"
    
    echo "🧪 テスト実行:"
    echo "  ./test.sh [メールアドレス]"
    echo ""
    echo "📧 APIの使用例:"
    echo "curl -X POST \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"to\": \"test@example.com\", \"subject\": \"テスト\", \"content\": \"テストメール\"}' \\"
    echo "  \"$FUNCTION_URL\""
    
else
    echo "❌ デプロイに失敗しました。上記のエラーメッセージを確認してください。"
    exit 1
fi
