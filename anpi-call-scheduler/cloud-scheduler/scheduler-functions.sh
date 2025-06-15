#!/bin/bash
# Cloud Scheduler作成処理の共通関数
# anpi-call-scheduler/cloud-scheduler/scheduler-functions.sh

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cloud Scheduler作成関数
create_cloud_scheduler() {
    local PROJECT_ID=$1
    local REGION=$2
    local SCHEDULER_NAME=$3
    local JOB_NAME=$4
    local SCHEDULE=$5
    local TIMEZONE=$6
    local SERVICE_ACCOUNT=$7
    local DESCRIPTION="${8:-安否確認コールスケジューラー - 毎時0分にCloud Run Jobを実行してタスクを作成}"

    echo -e "${YELLOW}📅 Cloud Schedulerジョブを設定中...${NC}"

    # パラメータ検証
    if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ] || [ -z "$SCHEDULER_NAME" ] || [ -z "$JOB_NAME" ] || [ -z "$SCHEDULE" ] || [ -z "$TIMEZONE" ] || [ -z "$SERVICE_ACCOUNT" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: create_cloud_scheduler PROJECT_ID REGION SCHEDULER_NAME JOB_NAME SCHEDULE TIMEZONE SERVICE_ACCOUNT [DESCRIPTION]"
        return 1
    fi

    # Cloud Scheduler APIの有効化確認
    echo -e "${YELLOW}   Cloud Scheduler APIの確認中...${NC}"
    if ! gcloud services list --enabled --filter="name:cloudscheduler.googleapis.com" --format="value(name)" | grep -q "cloudscheduler.googleapis.com"; then
        echo -e "${YELLOW}   Cloud Scheduler APIを有効化中...${NC}"
        gcloud services enable cloudscheduler.googleapis.com
        echo -e "${GREEN}   ✓ Cloud Scheduler APIを有効化しました${NC}"
    else
        echo -e "${GREEN}   ✓ Cloud Scheduler APIは有効化済み${NC}"
    fi

    # Cloud Run Jobの存在確認
    echo -e "${YELLOW}   Cloud Run Jobの存在確認中...${NC}"
    if ! gcloud run jobs describe $JOB_NAME --region=$REGION >/dev/null 2>&1; then
        echo -e "${RED}   ❌ Cloud Run Job '$JOB_NAME' が見つかりません${NC}"
        echo -e "${YELLOW}   先にCloud Run Jobをデプロイしてください${NC}"
        return 1
    fi
    echo -e "${GREEN}   ✓ Cloud Run Job が存在します${NC}"

    # サービスアカウント権限の確認・設定
    echo -e "${YELLOW}   サービスアカウント権限の確認・設定中...${NC}"
    if gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/run.invoker" \
        --no-user-output-enabled >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Run Invoker権限が設定されました${NC}"
    else
        echo -e "${YELLOW}   ⚠ Cloud Run Invoker権限の設定に失敗または既に設定済み${NC}"
    fi

    # 既存のスケジューラージョブの確認と削除
    echo -e "${YELLOW}   既存のスケジューラージョブの確認中...${NC}"
    if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
        echo -e "${YELLOW}   既存のスケジューラージョブを削除中...${NC}"
        gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION --quiet
        echo -e "${GREEN}   ✓ 既存のスケジューラージョブを削除しました${NC}"
    else
        echo -e "${GREEN}   ✓ 新規作成します${NC}"
    fi

    # Cloud Run JobのURLを構築
    local JOB_URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

    # Cloud Schedulerジョブの作成（OIDC認証方式）
    echo -e "${YELLOW}   Cloud Schedulerジョブを作成中...${NC}"
    if gcloud scheduler jobs create http $SCHEDULER_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --time-zone="$TIMEZONE" \
        --uri="$JOB_URL" \
        --http-method=POST \
        --oidc-service-account-email="$SERVICE_ACCOUNT" \
        --description="$DESCRIPTION" \
        --max-retry-attempts=3 \
        --max-retry-duration=300s \
        --max-doublings=5 \
        --min-backoff-duration=10s \
        --max-backoff-duration=300s >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Schedulerジョブが作成されました${NC}"
    else
        echo -e "${RED}   ❌ Cloud Schedulerジョブの作成に失敗しました${NC}"
        return 1
    fi

    return 0
}

# OAuth認証版のCloud Scheduler作成関数（互換性のため）
create_cloud_scheduler_oauth() {
    local PROJECT_ID=$1
    local REGION=$2
    local SCHEDULER_NAME=$3
    local JOB_NAME=$4
    local SCHEDULE=$5
    local TIMEZONE=$6
    local SERVICE_ACCOUNT=$7
    local DESCRIPTION="${8:-安否確認コールスケジューラー - 毎時0分にCloud Run Jobを実行してタスクを作成}"

    echo -e "${YELLOW}📅 Cloud Schedulerジョブを設定中（OAuth認証）...${NC}"

    # パラメータ検証
    if [ -z "$PROJECT_ID" ] || [ -z "$REGION" ] || [ -z "$SCHEDULER_NAME" ] || [ -z "$JOB_NAME" ] || [ -z "$SCHEDULE" ] || [ -z "$TIMEZONE" ] || [ -z "$SERVICE_ACCOUNT" ]; then
        echo -e "${RED}❌ 必要なパラメータが不足しています${NC}"
        echo "使用方法: create_cloud_scheduler_oauth PROJECT_ID REGION SCHEDULER_NAME JOB_NAME SCHEDULE TIMEZONE SERVICE_ACCOUNT [DESCRIPTION]"
        return 1
    fi

    # 既存のスケジューラージョブの確認と削除
    echo -e "${YELLOW}   既存のスケジューラージョブの確認中...${NC}"
    if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
        echo -e "${YELLOW}   既存のスケジューラージョブを削除中...${NC}"
        gcloud scheduler jobs delete $SCHEDULER_NAME --location=$REGION --quiet
        echo -e "${GREEN}   ✓ 既存のスケジューラージョブを削除しました${NC}"
    fi

    # プロジェクト番号の取得
    local PROJECT_NUMBER
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")

    # Cloud Run JobのURLを構築
    local JOB_URL="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/${JOB_NAME}:run"

    # Cloud Schedulerジョブの作成（OAuth認証方式）
    echo -e "${YELLOW}   Cloud Schedulerジョブを作成中（OAuth認証）...${NC}"
    if gcloud scheduler jobs create http $SCHEDULER_NAME \
        --location=$REGION \
        --schedule="$SCHEDULE" \
        --time-zone="$TIMEZONE" \
        --uri="$JOB_URL" \
        --http-method=POST \
        --oauth-service-account-email="$SERVICE_ACCOUNT" \
        --oauth-token-scope="https://www.googleapis.com/auth/cloud-platform" \
        --max-retry-attempts=1 \
        --min-backoff=10s \
        --max-backoff=60s >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ Cloud Schedulerジョブが作成されました${NC}"
    else
        echo -e "${RED}   ❌ Cloud Schedulerジョブの作成に失敗しました${NC}"
        return 1
    fi

    return 0
}

# スケジューラー状態確認関数
check_scheduler_status() {
    local SCHEDULER_NAME=$1
    local REGION=$2

    if [ -z "$SCHEDULER_NAME" ] || [ -z "$REGION" ]; then
        echo -e "${RED}❌ スケジューラー名とリージョンが必要です${NC}"
        return 1
    fi

    echo -e "${YELLOW}📊 スケジューラーの状態を確認中...${NC}"
    
    if gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ スケジューラー '$SCHEDULER_NAME' が存在します${NC}"
        
        # 詳細情報を表示
        gcloud scheduler jobs describe $SCHEDULER_NAME --location=$REGION \
            --format="table(name,schedule,timeZone,state,httpTarget.uri)"
        
        return 0
    else
        echo -e "${RED}   ❌ スケジューラー '$SCHEDULER_NAME' が見つかりません${NC}"
        return 1
    fi
}

# スケジューラーテスト実行関数  
test_scheduler() {
    local SCHEDULER_NAME=$1
    local REGION=$2

    if [ -z "$SCHEDULER_NAME" ] || [ -z "$REGION" ]; then
        echo -e "${RED}❌ スケジューラー名とリージョンが必要です${NC}"
        return 1
    fi

    echo -e "${YELLOW}🧪 スケジューラーのテスト実行中...${NC}"
    
    if gcloud scheduler jobs run $SCHEDULER_NAME --location=$REGION >/dev/null 2>&1; then
        echo -e "${GREEN}   ✓ テスト実行が完了しました${NC}"
        return 0
    else
        echo -e "${RED}   ❌ テスト実行に失敗しました${NC}"
        return 1
    fi
}

# スクリプトが直接実行された場合の処理
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo -e "${BLUE}Cloud Scheduler作成処理の共通関数${NC}"
    echo -e "${YELLOW}このファイルは他のスクリプトから読み込んで使用してください${NC}"
    echo ""
    echo -e "${YELLOW}使用可能な関数:${NC}"
    echo "  - create_cloud_scheduler: OIDC認証でCloud Schedulerを作成"
    echo "  - create_cloud_scheduler_oauth: OAuth認証でCloud Schedulerを作成"
    echo "  - check_scheduler_status: スケジューラーの状態確認"
    echo "  - test_scheduler: スケジューラーのテスト実行"
fi
