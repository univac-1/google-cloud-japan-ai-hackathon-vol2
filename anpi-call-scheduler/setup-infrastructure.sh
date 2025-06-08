#!/bin/bash
# インフラストラクチャ初期セットアップスクリプト
# 初回実行時またはインフラ変更時のみ実行

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

echo "=== インフラストラクチャ初期セットアップ開始 ==="

# プロジェクトIDの確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ プロジェクトIDが設定されていません"
    exit 1
fi

echo "プロジェクトID: $PROJECT_ID"
echo "リージョン: $REGION"

# 1. 必要なAPIの有効化
echo ""
echo "=== 1. 必要なAPIの有効化 ==="
REQUIRED_APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "containerregistry.googleapis.com"
    "cloudscheduler.googleapis.com"
    "cloudtasks.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo "✓ $api は有効化済み"
    else
        echo "⚠ $api を有効化中..."
        gcloud services enable "$api"
        echo "✓ $api を有効化しました"
    fi
done

# 2. IAM権限の設定
echo ""
echo "=== 2. IAM権限の設定 ==="
if [ -z "$PROJECT_NUMBER" ]; then
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    echo "プロジェクト番号を取得: $PROJECT_NUMBER"
fi

CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Cloud Build権限の設定中..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/run.admin" \
    --quiet || echo "権限は既に設定済み"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$CLOUD_BUILD_SA" \
    --role="roles/iam.serviceAccountUser" \
    --quiet || echo "権限は既に設定済み"

echo "✓ Cloud Build権限設定完了"

# 3. Cloud Tasksキューの作成
echo ""
echo "=== 3. Cloud Tasksキューの作成 ==="
LOCATION=${CLOUD_TASKS_LOCATION:-$REGION}
QUEUE_NAME=${CLOUD_TASKS_QUEUE:-"anpi-call-queue"}

echo "ロケーション: $LOCATION"
echo "キュー名: $QUEUE_NAME"

# キューが既に存在するかチェック
if gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION >/dev/null 2>&1; then
    echo "✓ キュー '$QUEUE_NAME' は既に存在します"
else
    echo "キュー '$QUEUE_NAME' を作成中..."
    gcloud tasks queues create $QUEUE_NAME \
        --location=$LOCATION \
        --max-concurrent-dispatches=100 \
        --max-retry-duration=3600s \
        --max-attempts=3 \
        --min-backoff=10s \
        --max-backoff=300s
    
    echo "✓ キューが正常に作成されました"
fi

# キューの詳細を表示
echo ""
echo "=== キューの詳細 ==="
gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION

echo ""
echo "=== インフラストラクチャセットアップ完了 ==="
echo "✓ 必要なAPIが有効化されました"
echo "✓ IAM権限が設定されました"
echo "✓ Cloud Tasksキューが作成されました"
echo ""
echo "次のステップ: ./deploy-application.sh を実行してアプリケーションをデプロイ"
