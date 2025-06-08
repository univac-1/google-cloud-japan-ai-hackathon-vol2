#!/bin/bash

# デプロイ用のスクリプト
# このスクリプトを実行する前に以下の設定が必要です：
# 1. Google Cloud SDKのインストールと認証
# 2. プロジェクトIDの設定
# 3. 必要なAPIの有効化

set -e

# カラー出力用の設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Speech Assistant OpenAI Cloud Run Deployment ===${NC}"

# プロジェクトIDの確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: Google Cloud project ID not set. Please run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"

# 必要なAPIが有効化されているかチェック
echo -e "${YELLOW}Checking required APIs...${NC}"
REQUIRED_APIS=("cloudbuild.googleapis.com" "run.googleapis.com" "artifactregistry.googleapis.com" "secretmanager.googleapis.com")

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo -e "${GREEN}✓ $api is enabled${NC}"
    else
        echo -e "${YELLOW}Enabling $api...${NC}"
        gcloud services enable "$api"
    fi
done

# OpenAI API キーをSecret Managerに保存
echo -e "${YELLOW}Setting up OpenAI API key in Secret Manager...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable not set.${NC}"
    echo -e "${YELLOW}Please set it by running: export OPENAI_API_KEY=your_api_key${NC}"
    exit 1
fi

# Secretが既に存在するかチェック
echo -e "${YELLOW}Checking if secret exists...${NC}"
if gcloud secrets describe openai-api-key --project=$PROJECT_ID >/dev/null 2>&1; then
    echo -e "${YELLOW}Updating existing secret...${NC}"
    echo -n "$OPENAI_API_KEY" | gcloud secrets versions add openai-api-key --data-file=- --project=$PROJECT_ID
else
    echo -e "${YELLOW}Creating new secret...${NC}"
    echo -n "$OPENAI_API_KEY" | gcloud secrets create openai-api-key --data-file=- --project=$PROJECT_ID
fi

# Cloud BuildサービスアカウントにCloud Runの権限を付与
echo -e "${YELLOW}Setting up Cloud Build permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
CLOUD_RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Cloud BuildサービスアカウントにCloud Run権限を付与
echo -e "${YELLOW}Adding Cloud Run permissions to Cloud Build service account...${NC}"
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" 2>/dev/null; then
    echo -e "${GREEN}✓ Cloud Run admin permissions added to Cloud Build SA${NC}"
else
    echo -e "${YELLOW}Warning: Could not add Cloud Run permissions to Cloud Build SA.${NC}"
fi

if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" 2>/dev/null; then
    echo -e "${GREEN}✓ Service Account User permissions added to Cloud Build SA${NC}"
else
    echo -e "${YELLOW}Warning: Could not add Service Account User permissions to Cloud Build SA.${NC}"
fi

if gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null; then
    echo -e "${GREEN}✓ Secret Manager permissions set successfully${NC}"
else
    echo -e "${YELLOW}Warning: Could not set Secret Manager permissions automatically.${NC}"
    echo -e "${YELLOW}Please run the following command manually with sufficient permissions:${NC}"
    echo -e "${YELLOW}gcloud secrets add-iam-policy-binding openai-api-key --member=\"serviceAccount:${CLOUD_RUN_SA}\" --role=\"roles/secretmanager.secretAccessor\"${NC}"
fi

# Cloud Buildを使用してデプロイ
echo -e "${YELLOW}Starting Cloud Build deployment...${NC}"
gcloud builds submit --config cloudbuild.yaml --substitutions _OPENAI_API_KEY="$OPENAI_API_KEY" .

echo -e "${GREEN}=== Deployment completed! ===${NC}"

# デプロイされたサービスのURLを取得
SERVICE_URL=$(gcloud run services describe speech-assistant-openai --region=asia-northeast1 --format="value(status.url)")
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"

echo -e "${YELLOW}Important: Update your Twilio webhook URL to: $SERVICE_URL/incoming-call${NC}"
