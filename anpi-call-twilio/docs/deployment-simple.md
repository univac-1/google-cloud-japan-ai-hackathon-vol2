# デプロイガイド

## 前提条件

1. Google Cloud SDK インストール済み
2. プロジェクト権限: Owner または Editor + Cloud Run Admin
3. OpenAI API キー

## 初回セットアップ

### 1. 必要なAPIの有効化
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 2. Artifact Registry作成
```bash
gcloud artifacts repositories create speech-assistant \
  --repository-format=docker \
  --location=asia-northeast1
```

### 3. 権限設定（管理者が実行）
```bash
# Cloud Buildサービスアカウントに権限付与
PROJECT_NUMBER=$(gcloud projects describe univac-aiagent --format="value(projectNumber)")

gcloud projects add-iam-policy-binding univac-aiagent \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding univac-aiagent \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

## デプロイ方法

### deploy.shスクリプト使用（推奨）

```bash
# OpenAI API キーを設定
export OPENAI_API_KEY="your_openai_api_key"

# デプロイ実行
./deploy.sh
```

### 手動デプロイ

```bash
# OpenAI API キーを設定
export OPENAI_API_KEY="your_openai_api_key"

# Cloud Buildでデプロイ
gcloud builds submit --config cloudbuild.yaml \
  --substitutions _OPENAI_API_KEY="$OPENAI_API_KEY" .
```

## deploy.shの機能

1. **API有効化確認**: 必要なGoogle Cloud APIが有効か確認
2. **権限チェック**: 必要な権限があるか確認
3. **自動デプロイ**: Cloud Buildを使用してビルド・デプロイ
4. **結果表示**: デプロイ後のサービスURL表示

## パブリックアクセス設定

```bash
# 外部からのアクセスを許可
gcloud run services add-iam-policy-binding speech-assistant-openai \
  --region=asia-northeast1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

## Twilio設定

Webhook URLを以下に設定:
```
https://speech-assistant-openai-hkzk5xnm7q-an.a.run.app/incoming-call
```

## トラブルシューティング

### 403エラー
```bash
# パブリックアクセス権限を再設定
gcloud run services add-iam-policy-binding speech-assistant-openai \
  --region=asia-northeast1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### ログ確認
```bash
gcloud run services logs read speech-assistant-openai --region=asia-northeast1
```

### サービス状態確認
```bash
gcloud run services describe speech-assistant-openai --region=asia-northeast1
```
