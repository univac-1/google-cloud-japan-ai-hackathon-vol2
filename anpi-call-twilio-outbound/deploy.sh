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

echo -e "${GREEN}=== Speech Assistant Outbound Cloud Run Deployment ===${NC}"

# プロジェクトIDの確認
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: No project ID set. Please run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${YELLOW}Project ID: $PROJECT_ID${NC}"

# 必要なAPIが有効化されているかチェック
echo -e "${YELLOW}Checking required APIs...${NC}"
REQUIRED_APIS=("cloudbuild.googleapis.com" "run.googleapis.com" "artifactregistry.googleapis.com")

for api in "${REQUIRED_APIS[@]}"; do
    if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
        echo -e "${GREEN}✓ $api is enabled${NC}"
    else
        echo -e "${YELLOW}⚠ Enabling $api...${NC}"
        gcloud services enable "$api"
        echo -e "${GREEN}✓ $api enabled${NC}"
    fi
done

# 環境変数のチェック
echo -e "${YELLOW}Checking environment variables...${NC}"
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ Error: OPENAI_API_KEY is not set${NC}"
    exit 1
fi

if [ -z "$TWILIO_ACCOUNT_SID" ]; then
    echo -e "${RED}❌ Error: TWILIO_ACCOUNT_SID is not set${NC}"
    exit 1
fi

if [ -z "$TWILIO_AUTH_TOKEN" ]; then
    echo -e "${RED}❌ Error: TWILIO_AUTH_TOKEN is not set${NC}"
    exit 1
fi

if [ -z "$PHONE_NUMBER_FROM" ]; then
    echo -e "${RED}❌ Error: PHONE_NUMBER_FROM is not set${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All environment variables are set${NC}"

# Artifact Registryリポジトリの存在確認・作成
echo -e "${YELLOW}Checking Artifact Registry repository...${NC}"
if gcloud artifacts repositories describe speech-assistant --location=asia-northeast1 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Artifact Registry repository exists${NC}"
else
    echo -e "${YELLOW}Creating Artifact Registry repository...${NC}"
    gcloud artifacts repositories create speech-assistant \
        --repository-format=docker \
        --location=asia-northeast1 \
        --description="Speech Assistant containers"
    echo -e "${GREEN}✓ Artifact Registry repository created${NC}"
fi

# Cloud Buildサービスアカウントに権限付与
echo -e "${YELLOW}Setting up Cloud Build permissions...${NC}"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Cloud BuildサービスアカウントにCloud Run権限を付与
echo -e "${YELLOW}Adding Cloud Run permissions to Cloud Build service account...${NC}"
if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Cloud Run admin permissions added to Cloud Build SA${NC}"
else
    echo -e "${YELLOW}Warning: Could not add Cloud Run permissions to Cloud Build SA.${NC}"
fi

if gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Service Account User permissions added to Cloud Build SA${NC}"
else
    echo -e "${YELLOW}Warning: Could not add Service Account User permissions to Cloud Build SA.${NC}"
fi

# Cloud Buildを使用してデプロイ
echo -e "${YELLOW}Starting Cloud Build deployment...${NC}"
gcloud builds submit --config cloudbuild.yaml \
    --substitutions _OPENAI_API_KEY="$OPENAI_API_KEY",_TWILIO_ACCOUNT_SID="$TWILIO_ACCOUNT_SID",_TWILIO_AUTH_TOKEN="$TWILIO_AUTH_TOKEN",_PHONE_NUMBER_FROM="$PHONE_NUMBER_FROM" .

# デプロイ完了後のサービスURL取得
echo -e "${YELLOW}Getting service URL...${NC}"
SERVICE_URL=$(gcloud run services describe speech-assistant-outbound \
    --region=asia-northeast1 \
    --format="value(status.url)")

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}Outbound call endpoint: $SERVICE_URL/outbound-call${NC}"

# パブリックアクセス権限の設定確認
echo -e "${YELLOW}Checking public access permissions...${NC}"
if gcloud run services get-iam-policy speech-assistant-outbound --region=asia-northeast1 \
    --format="value(bindings[].members[])" | grep -q "allUsers"; then
    echo -e "${GREEN}✓ Public access is already enabled${NC}"
else
    echo -e "${YELLOW}Setting up public access...${NC}"
    gcloud run services add-iam-policy-binding speech-assistant-outbound \
        --region=asia-northeast1 \
        --member="allUsers" \
        --role="roles/run.invoker"
    echo -e "${GREEN}✓ Public access enabled${NC}"
fi

echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo -e "${GREEN}Service Name: speech-assistant-outbound${NC}"
echo -e "${GREEN}Region: asia-northeast1${NC}"
echo -e "${GREEN}URL: $SERVICE_URL${NC}"
echo -e "${GREEN}Test the outbound call: curl -X POST $SERVICE_URL/outbound-call -H \"Content-Type: application/json\" -d '{\"to_number\":\"+81XXXXXXXXX\"}'${NC}"
