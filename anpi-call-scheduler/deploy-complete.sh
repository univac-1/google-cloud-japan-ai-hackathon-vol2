#!/bin/bash
# 統合デプロイメントスクリプト - anpi-call-scheduler（即時実行専用）
# このスクリプトは以下の全工程を自動化します：
# 1. インフラストラクチャのセットアップ
# 2. Cloud Run Jobのデプロイ（即時実行専用）
# 3. Cloud Schedulerの設定（毎分実行で即時対応）
# 4. 動作確認

set -e

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# デフォルト設定変数
PROJECT_ID=$(gcloud config get-value project)
REGION="${REGION:-asia-northeast1}"
JOB_NAME="${JOB_NAME:-anpi-call-create-task-job}"
SCHEDULER_NAME="${SCHEDULER_NAME:-anpi-call-scheduler-job}"
SCHEDULE="${SCHEDULE:-*/15 * * * *}"  # 15分間隔実行（即時実行対応）
TIMEZONE="${TIMEZONE:-Asia/Tokyo}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT:-894704565810-compute@developer.gserviceaccount.com}"

# Cloud Tasks設定
CLOUD_TASKS_QUEUE="${CLOUD_TASKS_QUEUE:-anpi-call-queue}"
CLOUD_TASKS_LOCATION="${CLOUD_TASKS_LOCATION:-$REGION}"

# 環境設定
ENVIRONMENT="${ENVIRONMENT:-development}"
LOG_LEVEL="${LOG_LEVEL:-debug}"

# 使用方法表示
show_usage() {
    echo -e "${BLUE}使用方法: $0 [オプション]${NC}"
    echo ""
    echo -e "${YELLOW}オプション:${NC}"
    echo "  --infrastructure-only   インフラストラクチャのセットアップのみ実行"
    echo "  --deploy-only          アプリケーションのデプロイのみ実行"
    echo "  --skip-test           動作確認テストをスキップ"
    echo "  --production          本番環境設定でデプロイ"
    echo "  --help                このヘルプを表示"
    echo ""
    echo -e "${YELLOW}環境変数での設定例:${NC}"
    echo "  ENVIRONMENT=production LOG_LEVEL=info $0"
    echo "  REGION=us-central1 JOB_NAME=my-job $0"
    echo ""
}

# オプション処理
INFRASTRUCTURE_ONLY=false
DEPLOY_ONLY=false
SKIP_TEST=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --infrastructure-only)
            INFRASTRUCTURE_ONLY=true
            shift
            ;;
        --deploy-only)
            DEPLOY_ONLY=true
            shift
            ;;
        --skip-test)
            SKIP_TEST=true
            shift
            ;;
        --production)
            ENVIRONMENT=production
            LOG_LEVEL=info
            shift
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ 不明なオプション: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# インフラストラクチャセットアップ関数
setup_infrastructure() {
    echo -e "${BLUE}📦 インフラストラクチャのセットアップ${NC}"

    # 必要なAPIの有効化
    echo -e "${YELLOW}📡 必要なAPIの有効化中...${NC}"
    REQUIRED_APIS=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
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

    # IAM権限の設定
    echo -e "${YELLOW}🔑 Cloud Build権限を設定中...${NC}"
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$CLOUD_BUILD_SA" \
        --role="roles/run.admin" \
        --quiet >/dev/null 2>&1 || echo -e "   ⚠️ Cloud Run Admin権限は既に設定済みです"

    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$CLOUD_BUILD_SA" \
        --role="roles/iam.serviceAccountUser" \
        --quiet >/dev/null 2>&1 || echo -e "   ⚠️ Service Account User権限は既に設定済みです"

    echo -e "   ✓ Cloud Build権限設定完了"

    # Cloud Tasksキューの確認・作成
    echo -e "${YELLOW}📝 Cloud Tasksキューの確認・作成中...${NC}"
    
    # Cloud Tasks共通関数の読み込み
    source "./cloud-tasks/tasks-functions.sh"

    # Cloud Tasksキューの作成（詳細設定付き）
    if create_cloud_tasks_queue "$PROJECT_ID" "$CLOUD_TASKS_LOCATION" "$CLOUD_TASKS_QUEUE" "100" "3600s" "3" "10s" "300s"; then
        echo -e "   ✓ Cloud Tasksキューのセットアップが完了しました"
    else
        echo -e "   ❌ Cloud Tasksキューのセットアップに失敗しました"
        return 1
    fi
}

# アプリケーションデプロイ関数
deploy_application() {
    echo -e "${BLUE}🐳 Cloud Run Jobのビルド・デプロイ${NC}"

    # Cloud Run Jobs専用デプロイスクリプトを実行
    echo -e "${YELLOW}☁️ Cloud Run Jobsをデプロイ中...${NC}"

    # 環境変数を設定してからデプロイスクリプトを実行
    export ENVIRONMENT="$ENVIRONMENT"
    export LOG_LEVEL="$LOG_LEVEL"
    export JOB_NAME="$JOB_NAME"
    export REGION="$REGION"
    export CLOUD_TASKS_LOCATION="$CLOUD_TASKS_LOCATION"
    export CLOUD_TASKS_QUEUE="$CLOUD_TASKS_QUEUE"

    if ./cloud-run-jobs/deploy-job.sh build; then
        echo -e "   ✓ Cloud Run Jobsをデプロイしました"
    else
        echo -e "   ❌ Cloud Run Jobsのデプロイに失敗しました"
        return 1
    fi

    # 権限設定
    echo -e "${BLUE}🔐 権限設定${NC}"
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

    # Cloud Schedulerの設定
    echo -e "${BLUE}⏰ Cloud Schedulerの設定${NC}"

    # 共通関数の読み込み
    source "./cloud-scheduler/scheduler-functions.sh"

    echo -e "${YELLOW}📅 Cloud Schedulerを作成中...${NC}"
    if create_cloud_scheduler "$PROJECT_ID" "$REGION" "$SCHEDULER_NAME" "$SCHEDULE" "$TIMEZONE" "$JOB_NAME" "$SERVICE_ACCOUNT"; then
        echo -e "   ✓ Cloud Schedulerを作成しました (毎分実行で即時対応)"
    else
        echo -e "   ⚠️ Cloud Schedulerは既に存在するか、作成をスキップしました"
    fi

}

# 動作確認関数
run_verification_tests() {
    echo -e "${BLUE}🧪 動作確認${NC}"

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
    source "./cloud-tasks/tasks-functions.sh"
    if check_tasks_queue_status "$CLOUD_TASKS_QUEUE" "$CLOUD_TASKS_LOCATION"; then
        TASK_COUNT=$(gcloud tasks list --queue=$CLOUD_TASKS_QUEUE --location=$CLOUD_TASKS_LOCATION --format="value(name)" 2>/dev/null | wc -l)
        echo -e "   ✓ Cloud Tasksキュー内のタスク数: $TASK_COUNT"
    else
        echo -e "   ⚠️ Cloud Tasksキューの状態確認に失敗しました"
    fi
}

# デプロイメントサマリー表示
show_deployment_summary() {
    echo ""
    echo -e "${GREEN}🎉 デプロイメント完了！${NC}"
    echo ""

    # サマリー情報の表示
    echo -e "${BLUE}📊 デプロイメントサマリー:${NC}"
    echo -e "   ✅ Cloud Run Job: ${GREEN}$JOB_NAME${NC} (デプロイ済み)"
    echo -e "   ✅ Cloud Scheduler: ${GREEN}$SCHEDULER_NAME${NC} ($SCHEDULE)"
    echo -e "   ✅ Cloud Tasks Queue: ${GREEN}$CLOUD_TASKS_QUEUE${NC}"
    echo -e "   ✅ 環境: ${GREEN}$ENVIRONMENT${NC}"
    echo -e "   ✅ リージョン: ${GREEN}$REGION${NC}"
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
}

# ==============================================================================
# メイン処理
# ==============================================================================

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║             anpi-call-scheduler 統合デプロイ                 ║${NC}"
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

# 実行処理の分岐
if [ "$INFRASTRUCTURE_ONLY" = true ]; then
    setup_infrastructure
    echo -e "${GREEN}✅ インフラストラクチャのセットアップが完了しました${NC}"
elif [ "$DEPLOY_ONLY" = true ]; then
    deploy_application
    if [ "$SKIP_TEST" = false ]; then
        run_verification_tests
    fi
    show_deployment_summary
else
    # 完全デプロイメント
    setup_infrastructure
    deploy_application
    if [ "$SKIP_TEST" = false ]; then
        run_verification_tests
    fi
    show_deployment_summary
fi

