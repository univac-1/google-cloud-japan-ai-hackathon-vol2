#!/bin/bash

# Cloud SQL for MySQL 8.4 セットアップスクリプト
# 高齢者向け安否確認＋イベント案内アプリ用データベース

set -e  # エラー時に停止

# config.envファイルの読み込み（基本設定）
if [[ -f "config.env" ]]; then
    export $(cat config.env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "エラー: config.envファイルが見つかりません"
    echo "基本設定ファイルが必要です"
    exit 1
fi

# .envファイルの読み込み（パスワード情報）
if [[ -f ".env" ]]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
else
    echo "エラー: .envファイルが見つかりません"
    echo "パスワード情報ファイルが必要です"
    exit 1
fi

# === 固定設定（config.envから読み込み） ===
# 基本設定、インスタンス設定、ストレージ設定、セキュリティ設定は config.env で管理

# === DDL/DMLファイルリスト ===
DDL_FILES=(
    "01_users.sql"
    "02_events.sql"
)

DML_FILES=(
    "01_users.sql"
    "02_events.sql"
)

# === カラーコード ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# === 設定値チェック関数 ===
check_config() {
    echo -e "${BLUE}=== 設定値確認 ===${NC}"
    echo -e "${YELLOW}プロジェクトID: ${PROJECT_ID}${NC}"
    echo -e "${YELLOW}インスタンス名: ${DB_INSTANCE_NAME}${NC}"
    echo -e "${YELLOW}データベース名: ${DB_NAME}${NC}"
    echo -e "${YELLOW}ユーザー名: ${DEFAULT_USER}${NC}"
    echo -e "${YELLOW}リージョン: ${REGION}${NC}"
    echo -e "${YELLOW}インスタンスタイプ: ${TIER}${NC}"
    echo -e "${YELLOW}MySQL バージョン: ${DATABASE_VERSION}${NC}"
    echo ""
}

# パスワード生成（設定ファイルとは別にここで生成）
DEFAULT_PASSWORD="$(openssl rand -base64 32)"
ROOT_PASSWORD="$(openssl rand -base64 32)"

echo -e "${GREEN}=== Cloud SQL for MySQL 8.4 セットアップ開始 ===${NC}"

# 設定値の確認
check_config

# プロジェクトの設定
echo -e "${YELLOW}プロジェクトを設定中...${NC}"
gcloud config set project $PROJECT_ID

# 必要なAPIの有効化
echo -e "${YELLOW}必要なAPIを有効化中...${NC}"
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com

# Cloud SQLインスタンスの作成
echo -e "${YELLOW}Cloud SQLインスタンスを作成中...${NC}"
gcloud sql instances create $DB_INSTANCE_NAME \
    --database-version=$DATABASE_VERSION \
    --tier=$TIER \
    --edition=$EDITION \
    --region=$REGION \
    --storage-size=$STORAGE_SIZE \
    --storage-type=$STORAGE_TYPE \
    --storage-auto-increase \
    --no-backup \
    --authorized-networks=$AUTHORIZED_NETWORKS \
    $([ "$DELETION_PROTECTION" = true ] && echo "--deletion-protection" || echo "--no-deletion-protection")

echo -e "${GREEN}Cloud SQLインスタンス '$DB_INSTANCE_NAME' が作成されました${NC}"

# rootユーザーのパスワード設定（Cloud SQL Studio用）
echo -e "${YELLOW}rootユーザーのパスワードを設定中...${NC}"
gcloud sql users set-password root \
    --host=% \
    --instance=$DB_INSTANCE_NAME \
    --password=$ROOT_PASSWORD

echo -e "${GREEN}rootユーザーのパスワードが設定されました${NC}"

# データベースの作成
echo -e "${YELLOW}データベース '$DB_NAME' を作成中...${NC}"
gcloud sql databases create $DB_NAME \
    --instance=$DB_INSTANCE_NAME \
    --charset=utf8mb4 \
    --collation=utf8mb4_unicode_ci

echo -e "${GREEN}データベース '$DB_NAME' が作成されました${NC}"

# データベースユーザーの作成（Cloud SQL Studio対応）
echo -e "${YELLOW}データベースユーザー '$DEFAULT_USER' を作成中...${NC}"
gcloud sql users create $DEFAULT_USER \
    --instance=$DB_INSTANCE_NAME \
    --password=$DEFAULT_PASSWORD \
    --host=%

echo -e "${GREEN}データベースユーザー '$DEFAULT_USER' が作成されました${NC}"

# アプリケーションユーザーに権限を付与
echo -e "${YELLOW}ユーザー '$DEFAULT_USER' に権限を付与中...${NC}"
echo -e "${YELLOW}注意: Cloud SQL Studioから手動で権限を設定してください${NC}"
echo -e "${YELLOW}  1. Cloud SQL Studio > $DB_INSTANCE_NAME に接続${NC}"
echo -e "${YELLOW}  2. rootユーザーで接続後、以下のSQLを実行:${NC}"
echo -e "${YELLOW}     GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DEFAULT_USER'@'%';${NC}"
echo -e "${YELLOW}     FLUSH PRIVILEGES;${NC}"

echo -e "${GREEN}ユーザー '$DEFAULT_USER' が作成されました（権限は手動設定してください）${NC}"

# パスワードの保存（.env形式）
echo -e "${YELLOW}データベース接続情報を.envファイルに保存中...${NC}"
cat > .env << EOF
# Cloud SQL パスワード情報（機密情報）
# ※このファイルはバージョン管理対象外（.gitignoreで除外）

# === 認証情報 ===
# Cloud SQL Studio用
ROOT_USER=root
ROOT_PASSWORD=$ROOT_PASSWORD

# アプリケーション用
DEFAULT_USER=default
DEFAULT_PASSWORD=$DEFAULT_PASSWORD

# === パスワード再設定履歴 ===
# 再設定日時: $(date)
EOF

echo -e "${GREEN}接続情報が '.env' ファイルに保存されました${NC}"

# セキュリティ設定の確認
echo -e "${YELLOW}接続設定を確認中...${NC}"
echo "現在の承認済みネットワーク:"
gcloud sql instances describe $DB_INSTANCE_NAME --format="value(settings.ipConfiguration.authorizedNetworks[].value)"

# 完了メッセージ
echo -e "${GREEN}=== Cloud SQL セットアップ完了 ===${NC}"
echo -e "${YELLOW}次のステップ:${NC}"
echo "1. '.env' ファイルを安全な場所に保管してください"
echo "2. DDLスクリプトを実行してテーブルを作成してください"
echo "   ./run-ddl.sh"
echo "3. DMLスクリプトを実行してサンプルデータを投入してください"
echo "   ./run-dml.sh"

# インスタンス情報の表示
echo -e "${YELLOW}作成されたインスタンス情報:${NC}"
gcloud sql instances describe $DB_INSTANCE_NAME --format="table(name,databaseVersion,region,settings.tier,state)"
