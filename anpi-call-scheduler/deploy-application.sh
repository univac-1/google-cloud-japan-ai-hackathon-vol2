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
PROJECT_ID=$(gcloud config get-value project)

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

# Cloud Tasks共通関数の読み込み
source "./cloud-tasks/tasks-functions.sh"

LOCATION=${CLOUD_TASKS_LOCATION:-$REGION}
QUEUE_NAME=${CLOUD_TASKS_QUEUE:-"anpi-call-queue"}

if check_tasks_queue_status "$QUEUE_NAME" "$LOCATION" >/dev/null 2>&1; then
    echo "✓ Cloud Tasksキューが存在します"
else
    echo "❌ Cloud Tasksキューが見つかりません"
    echo "先に ./setup-infrastructure.sh を実行してください"
    exit 1
fi

# job.yamlの環境変数置換
echo ""
echo "=== job.yamlの環境変数置換 ==="
export PROJECT_ID JOB_NAME TASK_TIMEOUT CPU MEMORY ENVIRONMENT LOG_LEVEL CLOUD_TASKS_LOCATION
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

# 共通関数の読み込み
source "./cloud-scheduler/scheduler-functions.sh"

# Cloud Schedulerの作成（OAuth認証方式）
if create_cloud_scheduler_oauth "$PROJECT_ID" "$REGION" "$SCHEDULER_NAME" "$JOB_NAME" "$SCHEDULE" "Asia/Tokyo" "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"; then
    echo "✓ Cloud Scheduler設定完了"
else
    echo "❌ Cloud Scheduler設定に失敗しました"
    exit 1
fi

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
