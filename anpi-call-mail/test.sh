#!/bin/bash

# 安否確認システム - 自治体通報テストスクリプト
# 
# 使用方法:
#   ./test.sh [自治体メールアドレス] [姓] [名] [電話番号]
#
# 例:
#   ./test.sh safety@city.tokyo.jp 田中 太郎 090-1234-5678
#   ./test.sh  # デフォルト値でテスト実行
#
# テスト用のスクリプト
# 安否確認システム: 自治体への直接訪問要請メール送信テスト
# setup_and_deploy.sh 実行後に使用してください

# Function URLを取得（ファイルから読み込み、失敗時はgcloudから取得）
if [ -f "function_url.txt" ]; then
    FUNCTION_URL=$(cat function_url.txt)
else
    PROJECT_ID="univac-aiagent"
    FUNCTION_NAME="send-mail"
    REGION="asia-northeast1"
    
    echo "function_url.txt が見つかりません。gcloud から URL を取得中..."
    FUNCTION_URL=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.uri)" 2>/dev/null)
    
    if [ -z "$FUNCTION_URL" ]; then
        echo "❌ エラー: Function URL を取得できませんでした。"
        echo "先に setup_and_deploy.sh を実行してください。"
        exit 1
    fi
fi

echo "🚨 安否確認システム - 自治体通報テスト"
echo "URL: $FUNCTION_URL"
echo ""

# テスト用の安否確認対象者情報
TO_EMAIL=${1:-"safety-check@city.example.jp"}
LAST_NAME=${2:-"田中"}
FIRST_NAME=${3:-"太郎"}
PHONE_NUMBER=${4:-"090-1234-5678"}
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "📞 安否確認対象者情報:"
echo "  氏名: $LAST_NAME $FIRST_NAME 様"
echo "  電話番号: $PHONE_NUMBER"
echo "  自治体連絡先: $TO_EMAIL"
echo "  通報時刻: $TIMESTAMP"
echo ""
echo "🚨 直接訪問要請メールを送信中..."
echo ""

# HTTPリクエストを送信
response=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{
        \"to\": \"$TO_EMAIL\",
        \"last_name\": \"$LAST_NAME\",
        \"first_name\": \"$FIRST_NAME\",
        \"phone_number\": \"$PHONE_NUMBER\",
        \"timestamp\": \"$TIMESTAMP\"
    }" \
    "$FUNCTION_URL")

# レスポンスを解析
http_body=$(echo "$response" | sed -E '$d')
http_status=$(echo "$response" | tail -n1 | sed -E 's/.*:([0-9]+)$/\1/')

echo "📋 レスポンス:"
echo "  ステータス: $http_status"
echo "  レスポンス: $http_body"

if [ "$http_status" -eq 200 ]; then
    echo ""
    echo "✅ 安否確認通報成功！自治体にメールが送信されました。"
    echo "📧 自治体担当者による直接訪問が要請されました。"
    echo "👥 対象者: $LAST_NAME $FIRST_NAME 様 ($PHONE_NUMBER)"
else
    echo ""
    echo "❌ 通報失敗。上記のレスポンスを確認してください。"
    echo ""
    echo "💡 トラブルシューティング:"
    echo "  - Google Service Account キーが正しく設定されているか確認"
    echo "  - Gmail APIが有効になっているか確認"
    echo "  - サービスアカウントに適切な権限が設定されているか確認"
    echo "  - 必須パラメータ(to, last_name, first_name, phone_number)が正しく設定されているか確認"
    echo "  - Cloud Functionのログを確認: gcloud functions logs read send-mail --region=asia-northeast1"
fi
