# 高齢者安否確認アプリ - データベース

高齢者向け安否確認＋イベント案内アプリのためのCloud SQL for MySQL 8.4データベース環境構築スクリプト集です。

## ファイル構成

```
anpi-call-db/
├── config.env                 # 基本設定（バージョン管理対象）
├── .env                       # パスワード情報（機密・管理対象外）
├── setup-cloudsql.sh          # Cloud SQLインスタンス作成
├── run-ddl.sh                 # テーブル作成
├── run-dml.sh                 # サンプルデータ投入
├── reset-password.sh          # パスワード再設定
├── ddl/                       # テーブル定義SQLファイル
│   ├── 01_users.sql
│   └── 02_events.sql
├── dml/                       # サンプルデータSQLファイル
│   ├── 01_users.sql
│   └── 02_events.sql
└── docs/
    └── db.md                  # データベース仕様書（外部システム連携用）
```

## 設定ファイル管理

### config.env（バージョン管理対象）
- プロジェクトID、リージョン、インスタンス名など基本設定
- チーム共有可能な非機密情報
- Gitでバージョン管理される

### .env（機密情報・管理対象外）
- データベースパスワード、rootパスワードなど認証情報
- `.gitignore`で除外され、各環境で個別管理
- 初回セットアップ時に自動生成される

## セットアップ手順

### 1. リポジトリクローン後の初期設定

新しい環境でセットアップする場合：

```bash
# リポジトリには config.env が含まれている
# .env は各環境で作成が必要（パスワード情報）

# 最初にCloud SQLを作成する場合は、.envファイルを手動作成：
cat > .env << 'EOF'
# パスワード情報は setup-cloudsql.sh で自動生成されます
ROOT_USER=root
ROOT_PASSWORD=
DB_PASSWORD=
EOF
```

### 2. Cloud SQL作成

```bash
./setup-cloudsql.sh
```

※ パスワードは自動生成され、`.env`ファイルに保存されます

### 3. 実行権限付与

```bash
chmod +x *.sh
```

### 4. テーブル作成

```bash
./run-ddl.sh
```

### 5. サンプルデータ投入

```bash
./run-dml.sh
```

## 接続確認

### 環境変数の読み込み

```bash
# 基本設定の読み込み
source config.env
# パスワード情報の読み込み
source .env
```

### データベース一覧の確認

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE -e "SHOW DATABASES;"
```

### テーブル一覧の確認

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME -e "SHOW TABLES;"
```

### インタラクティブ接続

```bash
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME
```

### rootユーザーでの接続

```bash
mysql -h $DB_HOST -P $DB_PORT -u $ROOT_USER -p"$ROOT_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME
```

## リソース削除

テスト完了後にリソースを削除する場合：

```bash
# Cloud SQLインスタンス削除（注意：データも削除されます）
gcloud sql instances delete cloudsql-01 --project=univac-aiagent
```

詳細な接続情報や外部システム連携については、[docs/db.md](docs/db.md)を参照してください。
