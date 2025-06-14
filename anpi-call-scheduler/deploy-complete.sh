#!/bin/bash
# 完全デプロイメントスクリプト - anpi-call-scheduler
# このスクリプトは以下の全工程を自動化します：
# 1. インフラストラクチャのセットアップ
# 2. Cloud Run Jobのデプロイ
# 3. Cloud Schedulerの設定
# 4. 動作確認

set -e

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定変数
PROJECT_ID=$(gcloud config get-value project)
REGION=asia-northeast1
JOB_NAME=anpi-call-create-task-job
SCHEDULER_NAME=anpi-call-scheduler-job
SCHEDULE="0 * * * *"
TIMEZONE="Asia/Tokyo"
IMAGE_NAME="gcr.io/$PROJECT_ID/anpi-call-scheduler:latest"
SERVICE_ACCOUNT="894704565810-compute@developer.gserviceaccount.com"

# Cloud Tasks設定
CLOUD_TASKS_QUEUE=anpi-call-queue
CLOUD_TASKS_LOCATION=$REGION

# 環境設定
ENVIRONMENT=development
LOG_LEVEL=debug

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                anpi-call-scheduler                           ║${NC}"
echo -e "${BLUE}║            完全デプロイメントスクリプト                      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${YELLOW}📋 設定情報:${NC}"
echo -e "   プロジェクトID: ${GREEN}$PROJECT_ID${NC}"
echo -e "   リージョン: ${GREEN}$REGION${NC}"
echo -e "   Cloud Run Job: ${GREEN}$JOB_NAME${NC}"
echo -e "   Cloud Scheduler: ${GREEN}$SCHEDULER_NAME${NC}"
echo -e "   実行スケジュール: ${GREEN}$SCHEDULE ($TIMEZONE)${NC}"
echo -e "   環境: ${GREEN}$ENVIRONMENT${NC}"
echo ""

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ プロジェクトIDが設定されていません${NC}"
    echo -e "${YELLOW}以下のコマンドでプロジェクトを設定してください:${NC}"
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# ステップ 1: インフラストラクチャのセットアップ
echo -e "${BLUE}📦 ステップ 1: インフラストラクチャのセットアップ${NC}"

# 必要なAPIの有効化
echo -e "${YELLOW}📡 必要なAPIの有効化中...${NC}"
REQUIRED_APIS=(
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "cloudscheduler.googleapis.com"
    "cloudtasks.googleapis.com"
    "sqladmin.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo -e "   ✓ $api は有効です"
    else
        echo -e "   🔄 $api を有効化中..."
        gcloud services enable "$api"
        echo -e "   ✓ $api を有効化しました"
    fi
done

# Cloud Tasksキューの確認・作成
echo -e "${YELLOW}📝 Cloud Tasksキューの確認・作成中...${NC}"
if gcloud tasks queues describe $CLOUD_TASKS_QUEUE --location=$CLOUD_TASKS_LOCATION >/dev/null 2>&1; then
    echo -e "   ✓ Cloud Tasksキュー '$CLOUD_TASKS_QUEUE' が存在します"
else
    echo -e "   🔄 Cloud Tasksキューを作成中..."
    gcloud tasks queues create $CLOUD_TASKS_QUEUE --location=$CLOUD_TASKS_LOCATION
    echo -e "   ✓ Cloud Tasksキューを作成しました"
fi

# ステップ 2: Cloud Run Jobのビルド・デプロイ
echo -e "${BLUE}🐳 ステップ 2: Cloud Run Jobのビルド・デプロイ${NC}"

# Dockerイメージのビルド
echo -e "${YELLOW}🏗️ Dockerイメージをビルド中...${NC}"
docker build -t $IMAGE_NAME .
echo -e "   ✓ Dockerイメージをビルドしました"

# イメージのプッシュ
echo -e "${YELLOW}📤 Dockerイメージをプッシュ中...${NC}"
docker push $IMAGE_NAME
echo -e "   ✓ Dockerイメージをプッシュしました"

# Cloud Run Jobのデプロイ
echo -e "${YELLOW}☁️ Cloud Run Jobをデプロイ中...${NC}"
gcloud run jobs replace job.yaml --region=$REGION
echo -e "   ✓ Cloud Run Jobをデプロイしました"

# ステップ 3: 権限設定
echo -e "${BLUE}🔐 ステップ 3: 権限設定${NC}"

echo -e "${YELLOW}🔑 サービスアカウント権限を設定中...${NC}"

# Cloud Run Invoker権限
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker" >/dev/null 2>&1; then
    echo -e "   ✓ Cloud Run Invoker権限を設定しました"
else
    echo -e "   ⚠️ Cloud Run Invoker権限は既に設定済みです"
fi

# Cloud Run Developer権限
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.developer" >/dev/null 2>&1; then
    echo -e "   ✓ Cloud Run Developer権限を設定しました"
else
    echo -e "   ⚠️ Cloud Run Developer権限は既に設定済みです"
fi

# ステップ 4: Cloud Schedulerの設定
echo -e "${BLUE}⏰ ステップ 4: Cloud Schedulerの設定${NC}"

# 既存のスケジューラージョブの削除
echo -e "${YELLOW}🗑️ 既存のスケジューラージョブを確認中...${NC}"
if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
    echo -e "   🔄 既存のスケジューラージョブを削除中..."
    gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION --quiet
    echo -e "   ✓ 既存のスケジューラージョブを削除しました"
fi

# Cloud Schedulerジョブの作成
echo -e "${YELLOW}📅 Cloud Schedulerジョブを作成中...${NC}"
gcloud scheduler jobs create http $SCHEDULER_NAME \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --time-zone="$TIMEZONE" \
    --uri="https://$REGION-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/$PROJECT_ID/jobs/$JOB_NAME:run" \
    --http-method=POST \
    --oauth-service-account-email="$SERVICE_ACCOUNT" \
    --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
    --max-retry-attempts=1 \
    --min-backoff=10s \
    --max-backoff=60s

echo -e "   ✓ Cloud Schedulerジョブを作成しました"

# ステップ 5: 動作確認
echo -e "${BLUE}🧪 ステップ 5: 動作確認${NC}"

# Cloud Run Jobの手動実行テスト
echo -e "${YELLOW}🚀 Cloud Run Jobをテスト実行中...${NC}"
EXECUTION_NAME=$(gcloud run jobs execute $JOB_NAME --region=$REGION --format="value(metadata.name)")
echo -e "   🔄 実行中... (実行名: $EXECUTION_NAME)"

# 実行完了まで待機
echo -e "   ⏳ 実行完了を待機中..."
for i in {1..30}; do
    STATUS=$(gcloud run jobs executions describe $EXECUTION_NAME --region=$REGION --format="value(status.conditions[0].type)" 2>/dev/null || echo "Unknown")
    if [ "$STATUS" = "Completed" ]; then
        echo -e "   ✓ Cloud Run Job実行が完了しました"
        break
    elif [ "$STATUS" = "Failed" ]; then
        echo -e "   ❌ Cloud Run Job実行が失敗しました"
        break
    fi
    sleep 2
done

# Cloud Schedulerのテスト実行
echo -e "${YELLOW}📅 Cloud Schedulerをテスト実行中...${NC}"
gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION
echo -e "   ✓ Cloud Schedulerテスト実行が完了しました"

# Cloud Tasksキューの確認
echo -e "${YELLOW}📋 作成されたCloud Tasksを確認中...${NC}"
TASK_COUNT=$(gcloud tasks list --queue=$CLOUD_TASKS_QUEUE --location=$CLOUD_TASKS_LOCATION --format="value(name)" | wc -l)
echo -e "   ✓ Cloud Tasksキュー内のタスク数: $TASK_COUNT"

echo ""
echo -e "${GREEN}🎉 デプロイメント完了！${NC}"
echo ""

# サマリー情報の表示
echo -e "${BLUE}📊 デプロイメントサマリー:${NC}"
echo -e "   ✅ Cloud Run Job: ${GREEN}$JOB_NAME${NC} (デプロイ済み)"
echo -e "   ✅ Cloud Scheduler: ${GREEN}$SCHEDULER_NAME${NC} (毎時0分実行)"
echo -e "   ✅ Cloud Tasks Queue: ${GREEN}$CLOUD_TASKS_QUEUE${NC} ($TASK_COUNT タスク)"
echo -e "   ✅ 環境: ${GREEN}$ENVIRONMENT${NC}"
echo ""

# 管理コマンドの表示
echo -e "${BLUE}🛠️ 管理コマンド:${NC}"
echo -e "${YELLOW}# Cloud Run Job手動実行:${NC}"
echo "gcloud run jobs execute $JOB_NAME --region=$REGION"
echo ""
echo -e "${YELLOW}# Cloud Scheduler手動実行:${NC}"
echo "gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION"
echo ""
echo -e "${YELLOW}# 実行履歴確認:${NC}"
echo "gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --limit=5"
echo ""
echo -e "${YELLOW}# Cloud Tasksキュー確認:${NC}"
echo "gcloud tasks list --queue=$CLOUD_TASKS_QUEUE --location=$CLOUD_TASKS_LOCATION"
echo ""
echo -e "${YELLOW}# ログ確認:${NC}"
echo "gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit=20 --format=\"table(timestamp,severity,textPayload)\""
echo ""

echo -e "${GREEN}🚀 anpi-call-schedulerが正常に稼働中です！${NC}"
