#!/bin/bash
# Cloud Scheduler設定スクリプト
# anpi-call-scheduler用のCloud Schedulerジョブを作成・管理

set -e

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定変数
PROJECT_ID=$(gcloud config get-value project)
REGION=asia-northeast1
SCHEDULER_NAME=anpi-call-scheduler-job
JOB_NAME=anpi-call-create-task-job
SCHEDULE="0 * * * *"  # 毎時0分実行
TIMEZONE="Asia/Tokyo"
SERVICE_ACCOUNT="894704565810-compute@developer.gserviceaccount.com"

echo -e "${GREEN}=== Cloud Scheduler設定開始 ===${NC}"
echo -e "${YELLOW}プロジェクトID: $PROJECT_ID${NC}"
echo -e "${YELLOW}リージョン: $REGION${NC}"
echo -e "${YELLOW}スケジューラー名: $SCHEDULER_NAME${NC}"
echo -e "${YELLOW}Cloud Run Job名: $JOB_NAME${NC}"
echo -e "${YELLOW}実行スケジュール: $SCHEDULE ($TIMEZONE)${NC}"

# プロジェクトIDの確認
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ プロジェクトIDが設定されていません${NC}"
    echo -e "${YELLOW}以下のコマンドでプロジェクトを設定してください:${NC}"
    echo "gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

# Cloud Run Jobの存在確認
echo -e "${YELLOW}Cloud Run Jobの存在確認中...${NC}"
if ! gcloud run jobs describe $JOB_NAME --region=$REGION >/dev/null 2>&1; then
    echo -e "${RED}❌ Cloud Run Job '$JOB_NAME' が見つかりません${NC}"
    echo -e "${YELLOW}先にCloud Run Jobをデプロイしてください${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Cloud Run Job が存在します${NC}"

# 必要な権限の確認・設定
echo -e "${YELLOW}サービスアカウント権限の確認・設定中...${NC}"

# Cloud Run Invoker権限
echo -e "${YELLOW}Cloud Run Invoker権限を付与中...${NC}"
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Cloud Run Invoker権限が設定されました${NC}"
else
    echo -e "${YELLOW}Warning: Cloud Run Invoker権限の設定に失敗または既に設定済み${NC}"
fi

# Cloud Run Developer権限（Job実行に必要）
echo -e "${YELLOW}Cloud Run Developer権限を付与中...${NC}"
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.developer" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Cloud Run Developer権限が設定されました${NC}"
else
    echo -e "${YELLOW}Warning: Cloud Run Developer権限の設定に失敗または既に設定済み${NC}"
fi

# 既存のスケジューラージョブの確認と削除
echo -e "${YELLOW}既存のスケジューラージョブの確認中...${NC}"
if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
    echo -e "${YELLOW}既存のスケジューラージョブを削除中...${NC}"
    gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION --quiet
    echo -e "${GREEN}✓ 既存のスケジューラージョブを削除しました${NC}"
fi

# Cloud Schedulerジョブの作成（OAuth認証方式）
echo -e "${YELLOW}Cloud Schedulerジョブを作成中...${NC}"
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

echo -e "${GREEN}✓ Cloud Schedulerジョブが作成されました${NC}"

# スケジューラーのテスト実行
echo -e "${YELLOW}スケジューラーのテスト実行中...${NC}"
gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION

echo -e "${GREEN}=== Cloud Scheduler設定完了 ===${NC}"

# 管理コマンドの表示
echo ""
echo -e "${YELLOW}=== 管理コマンド ===${NC}"
echo -e "${YELLOW}# スケジューラー状態確認:${NC}"
echo "gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION"
echo ""
echo -e "${YELLOW}# スケジューラー手動実行:${NC}"
echo "gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION"
echo ""
echo -e "${YELLOW}# Cloud Run Job実行履歴確認:${NC}"
echo "gcloud run jobs executions list --job=$JOB_NAME --region=$REGION --limit=5"
echo ""
echo -e "${YELLOW}# ログ確認:${NC}"
echo "gcloud logging read \"resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME\" --limit=20"
echo ""
echo -e "${YELLOW}# スケジューラー削除:${NC}"
echo "gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION"

echo ""
echo -e "${GREEN}🎉 設定完了！スケジューラーは毎時0分にCloud Run Jobを実行します${NC}"
