#!/bin/bash

# Cloud Functions デプロイスクリプト
# 使用方法: ./deploy.sh [SENDGRID_API_KEY]

set -e

# 設定
FUNCTION_NAME="send-email"
REGION="asia-northeast1"  # 東京リージョン
RUNTIME="python312"
ENTRY_POINT="send_email"
MEMORY="256MB"
TIMEOUT="60s"

# APIキーの確認
if [ -z "$1" ]; then
    echo "⚠️  SendGrid APIキーが指定されていません"
    echo "   テスト用のダミーキーを使用します"
    SENDGRID_API_KEY="dummy-api-key-replace-with-real-key"
else
    SENDGRID_API_KEY="$1"
fi

echo "🚀 Cloud Functions をデプロイしています..."
echo "   Function名: $FUNCTION_NAME"
echo "   リージョン: $REGION"
echo "   ランタイム: $RUNTIME"

# Cloud Functions をデプロイ
gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$REGION \
    --source=. \
    --entry-point=$ENTRY_POINT \
    --trigger=http \
    --allow-unauthenticated \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --set-env-vars="SENDGRID_API_KEY=$SENDGRID_API_KEY,DEFAULT_FROM_EMAIL=noreply@example.com,DEFAULT_FROM_NAME=AnpiCall System"

echo "✅ デプロイが完了しました！"

# デプロイされた関数のURLを取得
FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.uri)")

echo ""
echo "📋 テスト方法:"
echo "   ローカルテスト: python local_server.py"
echo "   APIテスト: python test_email.py $FUNCTION_URL"
echo ""
echo "🔧 APIキー更新方法:"
echo "   gcloud functions deploy $FUNCTION_NAME \\"
echo "     --update-env-vars SENDGRID_API_KEY=YOUR_REAL_API_KEY \\"
echo "     --region=$REGION"
echo "🧪 テスト用curlコマンド:"
echo "curl -X POST $FUNCTION_URL \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"to_email\": \"test@example.com\","
echo "    \"subject\": \"テストメール\","
echo "    \"content\": \"<h1>Hello from AnpiCall!</h1><p>This is a test email.</p>\""
echo "  }'"
echo ""
echo "📝 本番環境では以下のコマンドでAPIキーを更新してください:"
echo "gcloud functions deploy $FUNCTION_NAME \\"
echo "  --update-env-vars SENDGRID_API_KEY=YOUR_REAL_API_KEY \\"
echo "  --region=$REGION"
