#!/bin/bash

# DDL実行スクリプト - テーブル作成
# Cloud SQL for MySQL 8.4
# 高齢者向け安否確認＋イベント案内アプリ

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

# === DDL/DMLファイルリスト ===
DDL_FILES=(
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

# パスワードは.envから自動読み込み済み
if [[ -z "$DEFAULT_PASSWORD" ]]; then
    echo -e "${RED}.envファイルからパスワードを取得できませんでした${NC}"
    echo -e "${YELLOW}setup-cloudsql.sh を実行して.envファイルを作成してください${NC}"
    exit 1
fi

echo -e "${GREEN}=== DDL実行開始（テーブル作成） ===${NC}"

# 設定値の確認
check_config

# プロジェクトの設定
echo -e "${YELLOW}プロジェクトを設定中...${NC}"
gcloud config set project $PROJECT_ID

# DDLファイルを順番に実行（設定ファイルから読み込み）
for ddl_file in "${DDL_FILES[@]}"; do
    file_path="ddl/${ddl_file}"
    
    if [[ -f "$file_path" ]]; then
        echo -e "${YELLOW}実行中: ${ddl_file}${NC}"
        
        # MySQLクライアントでSQLファイルを実行（SSL接続）
        mysql -h $DB_HOST -P $DB_PORT -u $DEFAULT_USER -p"$DEFAULT_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME < "$file_path"
            
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✓ ${ddl_file} の実行が完了しました${NC}"
        else
            echo -e "${RED}✗ ${ddl_file} の実行でエラーが発生しました${NC}"
            exit 1
        fi
    else
        echo -e "${RED}ファイルが見つかりません: ${file_path}${NC}"
        exit 1
    fi
done

echo -e "${GREEN}=== DDL実行完了 ===${NC}"
echo -e "${YELLOW}次のステップ: DMLスクリプトを実行してサンプルデータを投入${NC}"
echo "  ./run-dml.sh"
