#!/bin/bash

# --- 設定項目 ---
# ご自身の環境に合わせて以下の変数を変更してください
PROJECT_ID="univac-aiagent"               # あなたのGCPプロジェクトID
SERVICE_NAME="eniki-html-generator"        # Cloud Runサービス名
REGION="asia-northeast1"                   # デプロイ先のリージョン (例: asia-northeast1 は東京)
OUTPUT_BUCKET_NAME="eniki-completed"       # HTMLファイルを出力するGCSバケット名

# --- 環境チェック ---
if [ -z "$PROJECT_ID" ]; then
  echo "エラー: PROJECT_IDが設定されていません。スクリプトを編集して設定してください。"
  exit 1
fi

if [ -z "$OUTPUT_BUCKET_NAME" ]; then
  echo "エラー: OUTPUT_BUCKET_NAMEが設定されていません。スクリプトを編集して設定してください。"
  exit 1
fi

# プロジェクトを設定
echo "Google Cloudプロジェクトを ${PROJECT_ID} に設定します..."
gcloud config set project "$PROJECT_ID" || { echo "プロジェクトの設定に失敗しました。"; exit 1; }

# --- GCSバケットの存在確認と作成 (オプション) ---
# バケットが存在しない場合は作成します。必要なければこのブロックをコメントアウトしてください。
echo "GCSバケット ${OUTPUT_BUCKET_NAME} の存在を確認します..."
if ! gsutil ls "gs://${OUTPUT_BUCKET_NAME}" &> /dev/null; then
  echo "バケット ${OUTPUT_BUCKET_NAME} が見つかりません。作成します..."
  gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${OUTPUT_BUCKET_NAME}" || { echo "GCSバケットの作成に失敗しました。"; exit 1; }
  echo "バケット ${OUTPUT_BUCKET_NAME} を公開設定します..."
  # allUsersにストレージオブジェクト閲覧者の権限を付与
  gsutil iam ch allUsers:objectViewer "gs://${OUTPUT_BUCKET_NAME}" || { echo "GCSバケットの公開設定に失敗しました。"; exit 1; }
else
  echo "バケット ${OUTPUT_BUCKET_NAME} は既に存在します。"
fi

# --- Cloud Runデプロイ ---
echo "Cloud Runサービス ${SERVICE_NAME} をデプロイします..."
echo "リージョン: ${REGION}"
echo "出力バケット: ${OUTPUT_BUCKET_NAME}"

gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars OUTPUT_BUCKET_NAME="$OUTPUT_BUCKET_NAME" \
  --project "$PROJECT_ID" || { echo "Cloud Runのデプロイに失敗しました。"; exit 1; }

echo "--- デプロイ完了 ---"
echo "Cloud RunサービスのURLは上記出力で確認できます。"
echo "テストするには、以下のcurlコマンドを参考にしてください (YOUR_CLOUD_RUN_SERVICE_URLを置き換えてください):"
echo "curl -X POST -H \"Content-Type: application/json\" \\"
echo "     -d '{\"text_content\": \"これは\\n新しいテスト\\nテキストです。\"}' \\"
echo "     https://YOUR_CLOUD_RUN_SERVICE_URL/process-text"