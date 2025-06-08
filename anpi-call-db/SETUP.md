# Cloud SQL環境構築 - 設定管理ガイド

## 設定ファイル構成

### config.env（バージョン管理対象）
```bash
# 基本設定（チーム共有可能）
PROJECT_ID=univac-aiagent
REGION=asia-northeast1
DB_INSTANCE_NAME=cloudsql-01
DB_NAME=default
DB_USER=default
# ... その他の基本設定
```

### .env（機密情報・管理対象外）
```bash
# パスワード情報（各環境で個別管理）
ROOT_USER=root
ROOT_PASSWORD=xxxxxxxxxx
DB_PASSWORD=xxxxxxxxxx
```

## 新規環境セットアップ手順

### 1. リポジトリクローン
```bash
git clone <repository>
cd anpi-call-db
```

### 2. パスワードファイル作成
```bash
# 初期の.envファイル作成（パスワードは後で自動生成）
cat > .env << 'EOF'
ROOT_USER=root
ROOT_PASSWORD=
DB_PASSWORD=
EOF
```

### 3. Cloud SQL作成とパスワード生成
```bash
chmod +x *.sh
./setup-cloudsql.sh  # パスワード自動生成・.env更新
```

### 4. データベース初期化
```bash
./run-ddl.sh  # テーブル作成
./run-dml.sh  # サンプルデータ投入
```

## 既存環境での設定確認

### 設定値の確認
```bash
# 基本設定
source config.env && echo "PROJECT: $PROJECT_ID, INSTANCE: $DB_INSTANCE_NAME"

# パスワード設定確認（値は表示しない）
source .env && echo "ROOT_USER: $ROOT_USER, PASSWORD: [設定済み]"
```

### データベース接続テスト
```bash
source config.env && source .env
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME -e "SHOW TABLES;"
```

## ファイル管理ルール

- ✅ `config.env`: Gitで管理、チーム共有
- ❌ `.env`: Gitで除外（.gitignore）、個別管理
- ✅ 各種スクリプト: Gitで管理
- ✅ DDL/DMLファイル: Gitで管理
- ✅ ドキュメント: Gitで管理

## トラブルシューティング

### パスワード紛失時
```bash
./reset-password.sh  # 新しいパスワード生成・更新
```

### 設定ファイル不整合
```bash
# config.envの値確認
cat config.env

# .envの存在確認（内容は表示しない）
ls -la .env && echo ".envファイルが存在します"
```
