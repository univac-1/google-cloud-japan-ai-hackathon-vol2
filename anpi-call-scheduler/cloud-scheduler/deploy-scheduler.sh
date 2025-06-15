#!/bin/bash
# Cloud Scheduler専用デプロイスクリプト
# anpi-call-scheduler/cloud-scheduler/deploy-scheduler.sh

set -e

# スクリプトディレクトリの取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 共通関数の読み込み
source "$SCRIPT_DIR/scheduler-functions.sh"

# 設定変数
PROJECT_ID=$(gcloud config get-value project)
REGION=asia-northeast1
SCHEDULER_NAME=anpi-call-scheduler-job
JOB_NAME=anpi-call-create-task-job
SCHEDULE="*/15 * * * *"  # 15分間隔実行
TIMEZONE="Asia/Tokyo"
SERVICE_ACCOUNT="894704565810-compute@developer.gserviceaccount.com"
DESCRIPTION="安否確認コールスケジューラー - 15分間隔でCloud Run Jobを実行してタスクを作成"

echo -e "${BLUE}=== Cloud Scheduler デプロイ開始 ===${NC}"
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

# Cloud Schedulerの作成（OIDC認証）
if create_cloud_scheduler "$PROJECT_ID" "$REGION" "$SCHEDULER_NAME" "$JOB_NAME" "$SCHEDULE" "$TIMEZONE" "$SERVICE_ACCOUNT" "$DESCRIPTION"; then
    echo -e "${GREEN}✓ Cloud Schedulerの設定が完了しました${NC}"
else
    echo -e "${RED}❌ Cloud Schedulerの設定に失敗しました${NC}"
    exit 1
fi

# スケジューラーの状態確認
check_scheduler_status "$SCHEDULER_NAME" "$REGION"

# スケジューラーのテスト実行
if test_scheduler "$SCHEDULER_NAME" "$REGION"; then
    echo -e "${GREEN}✓ テスト実行が完了しました${NC}"
else
    echo -e "${YELLOW}⚠ テスト実行に失敗しましたが、スケジューラーは作成されました${NC}"
fi

echo -e "${GREEN}=== Cloud Scheduler デプロイ完了 ===${NC}"

# 管理コマンドの表示
echo ""
echo -e "${BLUE}=== 管理コマンド ===${NC}"
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
echo -e "${YELLOW}スケジュール: $SCHEDULE${NC}"
echo -e "${YELLOW}タイムゾーン: $TIMEZONE${NC}"
echo -e "${YELLOW}ターゲット: $JOB_NAME${NC}"
