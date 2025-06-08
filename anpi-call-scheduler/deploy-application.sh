#!/bin/bash
# アプリケーションデプロイスクリプト
# 開発時に繰り返し実行するスクリプト

set -e

# 環境変数の設定
ENVIRONMENT=development
LOG_LEVEL=debug
JOB_NAME=anpi-call-create-task-job
REGION=asia-northeast1
SCHEDULE="0 * * * *"
SCHEDULER_NAME=anpi-call-scheduler-job
PROJECT_NUMBER=894704565810
CPU=1
MEMORY=512Mi
TASK_TIMEOUT=300
MAX_RETRIES=1
CLOUD_TASKS_LOCATION=asia-northeast1
CLOUD_TASKS_QUEUE=anpi-call-queue

echo "✓ 環境変数設定完了"

echo "=== アプリケーションデプロイメント開始 ==="

# プロジェクトIDの確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ プロジェクトIDが設定されていません"
    exit 1
fi

echo "プロジェクトID: $PROJECT_ID"
echo "リージョン: $REGION"
echo "ジョブ名: $JOB_NAME"
echo "環境: $ENVIRONMENT"

# Cloud Tasksキューの存在確認
echo ""
echo "=== 前提条件の確認 ==="
LOCATION=${CLOUD_TASKS_LOCATION:-$REGION}
QUEUE_NAME=${CLOUD_TASKS_QUEUE:-"anpi-call-queue"}

if ! gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
    echo "❌ Cloud Tasksキューが見つかりません"
    echo "先に ./setup-infrastructure.sh を実行してください"
    exit 1
fi
echo "✓ Cloud Tasksキューが存在します"

# job.yamlの環境変数置換
echo ""
echo "=== job.yamlの環境変数置換 ==="
envsubst < job.yaml > job-temp.yaml
mv job-temp.yaml job.yaml
echo "✓ job.yaml置換完了"

# Cloud Buildデプロイメント
echo ""
echo "=== Cloud Buildデプロイメント開始 ==="
gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_JOB_NAME="$JOB_NAME",_REGION="$REGION",_CPU="$CPU",_MEMORY="$MEMORY",_TASK_TIMEOUT="$TASK_TIMEOUT",_ENVIRONMENT="$ENVIRONMENT",_LOG_LEVEL="$LOG_LEVEL" \
    .

echo "✓ Cloud Buildデプロイメント完了"

# Cloud Schedulerのセットアップ
echo ""
echo "=== Cloud Scheduler設定 ==="

# 既存のスケジューラージョブの確認と削除
if gcloud scheduler jobs describe "$SCHEDULER_NAME" --location="$REGION" &>/dev/null; then
    echo "既存のスケジューラージョブを削除中..."
    gcloud scheduler jobs delete "$SCHEDULER_NAME" --location="$REGION" --quiet
fi

# プロジェクト番号の取得
if [ -z "$PROJECT_NUMBER" ]; then
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
fi

# Cloud Schedulerジョブの作成（Cloud Run Job用 - OAuth認証）
gcloud scheduler jobs create http "$SCHEDULER_NAME" \
    --location="$REGION" \
    --schedule="$SCHEDULE" \
    --time-zone="Asia/Tokyo" \
    --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
    --http-method=POST \
    --oauth-service-account-email="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
    --max-retry-attempts=1 \
    --min-backoff=10s \
    --max-backoff=60s

echo "✓ Cloud Scheduler設定完了"

echo ""
echo "=== デプロイメント完了 ==="
echo "環境: $ENVIRONMENT"
echo "次回のスケジュール実行: $SCHEDULE (Asia/Tokyo)"
echo ""
echo "=== 動作確認コマンド ==="
echo "# ジョブの手動実行:"
echo "gcloud run jobs execute $JOB_NAME --region=$REGION"
echo ""
echo "# スケジューラーの手動実行:"
echo "gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION"
echo ""
echo "# 実行履歴の確認:"
echo "gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --limit=5"
echo ""
echo "# ログの確認:"
echo "gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit=20"
