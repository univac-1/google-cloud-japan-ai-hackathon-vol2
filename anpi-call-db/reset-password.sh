#!/bin/bash

# Cloud SQL ユーザーパスワード再設定スクリプト
# db-credentials.txtが削除された場合の復旧用

set -e  # エラー時に停止

# config.envファイルの読み込み（基本設定）
if [[ -f "config.env" ]]; then
    export $(cat config.env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo -e "${RED}config.envファイルが見つかりません${NC}"
    echo -e "${YELLOW}基本設定ファイルが必要です${NC}"
    exit 1
fi

# .envファイルの読み込み（パスワード情報）
if [[ -f ".env" ]]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo -e "${RED}.envファイルが見つかりません${NC}"
    echo -e "${YELLOW}パスワード情報ファイルが必要です${NC}"
    exit 1
fi

# 色設定
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 新しいパスワード生成
NEW_DEFAULT_PASSWORD="$(openssl rand -base64 32)"
NEW_ROOT_PASSWORD="$(openssl rand -base64 32)"

echo -e "${GREEN}=== Cloud SQL ユーザーパスワード再設定 ===${NC}"
echo -e "${YELLOW}プロジェクト: $PROJECT_ID${NC}"
echo -e "${YELLOW}インスタンス: $DB_INSTANCE_NAME${NC}"
echo -e "${YELLOW}ユーザー: $DEFAULT_USER${NC}"

# プロジェクトの設定
echo -e "${YELLOW}プロジェクトを設定中...${NC}"
gcloud config set project $PROJECT_ID

# 既存ユーザーのパスワードを再設定
echo -e "${YELLOW}ユーザー '$DEFAULT_USER' のパスワードを再設定中...${NC}"
gcloud sql users set-password $DEFAULT_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$NEW_DEFAULT_PASSWORD \
    --host=%

echo -e "${GREEN}ユーザー '$DEFAULT_USER' のパスワードが再設定されました${NC}"

# rootユーザーのパスワードも再設定
echo -e "${YELLOW}rootユーザーのパスワードを再設定中...${NC}"
gcloud sql users set-password root \
    --instance=$DB_INSTANCE_NAME \
    --password=$NEW_ROOT_PASSWORD \
    --host=%

echo -e "${GREEN}rootユーザーのパスワードも再設定されました${NC}"

# 新しい接続情報を保存（.env形式）
echo -e "${YELLOW}新しい接続情報を.envファイルに保存中...${NC}"
cat > .env << EOF
# Cloud SQL パスワード情報（機密情報）
# ※このファイルはバージョン管理対象外（.gitignoreで除外）

# === 認証情報 ===
# Cloud SQL Studio用
ROOT_USER=root
ROOT_PASSWORD=$NEW_ROOT_PASSWORD

# アプリケーション用
DEFAULT_USER=default
DEFAULT_PASSWORD=$NEW_DEFAULT_PASSWORD

# === パスワード再設定履歴 ===
# 再設定日時: $(date)
EOF

echo -e "${GREEN}新しい接続情報が '.env' ファイルに保存されました${NC}"
echo -e "${YELLOW}新しいパスワード: $NEW_DEFAULT_PASSWORD${NC}"
echo -e "${RED}このパスワードを安全な場所に保管してください${NC}"

# インスタンス状態の確認
echo -e "${YELLOW}インスタンス状態を確認中...${NC}"
gcloud sql instances describe $DB_INSTANCE_NAME --format="table(name,state,settings.tier)"

echo -e "${GREEN}=== パスワード再設定完了 ===${NC}"
echo -e "${YELLOW}アプリケーション側の設定も新しいパスワードに更新してください${NC}"
