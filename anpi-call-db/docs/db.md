# データベース仕様書 - 外部システム連携用

## 概要

高齢者向け安否確認＋イベント案内アプリのCloud SQL for MySQL 8.4データベースの仕様書です。

このドキュメントは外部システムやアプリケーションからの接続に必要な情報を記載しています。

## データベース接続情報

### リソース名の確認方法

以下のコマンドで現在のリソース名を確認できます：

```bash
# プロジェクトID確認
gcloud config get-value project

# Cloud SQLインスタンス一覧
gcloud sql instances list

# データベース一覧
gcloud sql databases list --instance=cloudsql-01

# ユーザー一覧
gcloud sql users list --instance=cloudsql-01
```

### 標準リソース名

| リソース | 名前 | 説明 |
|---------|------|------|
| Cloud SQLインスタンス | `cloudsql-01` | メインのデータベースインスタンス |
| データベース | `default` | アプリケーション用データベース |
| アプリケーションユーザー | `default` | 読み書き権限を持つユーザー |
| 管理ユーザー | `root` | 管理権限を持つユーザー |

### 接続文字列の取得方法

```bash
# パブリックIPアドレス取得
gcloud sql instances describe cloudsql-01 --format="get(ipAddresses[0].ipAddress)"

# 接続名取得（Cloud SQL Proxy用）
gcloud sql instances describe cloudsql-01 --format="get(connectionName)"
```

## データベーススキーマ

### テーブル一覧

| テーブル名 | 用途 | 主キー |
|-----------|------|--------|
| `users` | 高齢者利用者マスタ | `user_id` (CHAR(36)) |
| `events` | イベント情報マスタ | `event_id` (CHAR(36)) |

### users テーブル

高齢者利用者の基本情報を管理するテーブルです。

#### カラム定義

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|------------|------|
| user_id | CHAR(36) | NO | UUID() | 利用者ID（主キー） |
| last_name | VARCHAR(64) | NO | | 姓（漢字） |
| first_name | VARCHAR(64) | NO | | 名（漢字） |
| last_name_kana | VARCHAR(64) | YES | | セイ（全角カナ） |
| first_name_kana | VARCHAR(64) | YES | | メイ（全角カナ） |
| postal_code | CHAR(8) | YES | | 郵便番号 |
| prefecture | VARCHAR(40) | YES | | 都道府県 |
| address_block | VARCHAR(100) | YES | | 市区町村・町名・番地 |
| address_building | VARCHAR(100) | YES | | 建物名・部屋番号 |
| phone_number | VARCHAR(14) | NO | | 電話番号 |
| email | VARCHAR(255) | YES | | メールアドレス |
| gender | ENUM('male','female') | YES | NULL | 性別 |
| birth_date | DATE | YES | | 生年月日 |
| call_time | TIME | YES | | 電話希望時刻 |
| call_weekday | ENUM('sun','mon','tue','wed','thu','fri','sat') | YES | 'mon' | 電話希望曜日 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新日時 |

#### インデックス

```sql
-- 主キー
PRIMARY KEY (user_id)

-- 電話番号での検索用（推奨）
CREATE INDEX idx_users_phone ON users(phone_number);

-- 電話スケジュール検索用（推奨）
CREATE INDEX idx_users_call_schedule ON users(call_weekday, call_time);
```

### events テーブル

イベント情報を管理するテーブルです。

#### カラム定義

| カラム名 | データ型 | NULL | デフォルト | 説明 |
|---------|---------|------|------------|------|
| event_id | CHAR(36) | NO | UUID() | イベントID（主キー） |
| title | VARCHAR(150) | NO | | イベントタイトル |
| description | TEXT | YES | | イベント詳細 |
| start_datetime | DATETIME | NO | | 開始日時 |
| end_datetime | DATETIME | NO | | 終了日時 |
| postal_code | CHAR(8) | YES | | 会場郵便番号 |
| prefecture | VARCHAR(40) | YES | | 会場都道府県 |
| address_block | VARCHAR(100) | YES | | 会場市区町村・町名・番地 |
| address_building | VARCHAR(100) | YES | | 会場建物名・部屋番号 |
| contact_name | VARCHAR(120) | YES | | 問い合わせ窓口名 |
| contact_phone | VARCHAR(14) | YES | | 問い合わせ電話番号 |
| event_url | VARCHAR(2083) | YES | | イベント公式URL |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 作成日時 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 更新日時 |

#### インデックス

```sql
-- 主キー
PRIMARY KEY (event_id)

-- 日時での検索用（推奨）
CREATE INDEX idx_events_datetime ON events(start_datetime, end_datetime);

-- 地域での検索用（推奨）
CREATE INDEX idx_events_location ON events(prefecture, postal_code);
```

## 接続方法

### 環境変数の読み込み

設定ファイルから環境変数を読み込みます：

```bash
# 基本設定の読み込み
source config.env

# パスワード情報の読み込み（機密情報）
source .env
```

**ファイル構成**
- `config.env`: プロジェクトID、リージョンなど基本設定（バージョン管理対象）
- `.env`: パスワード情報（機密情報・各環境で個別管理）

### 1. Cloud SQL Proxy経由（推奨）

Cloud SQL Proxyを起動してローカル接続：

```bash
# プロキシ起動
cloud_sql_proxy -instances=$CLOUD_SQL_CONNECTION_STRING=tcp:3306

# アプリケーションから接続
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME
```

### 2. 直接接続

```bash
# パブリックIPでの接続（要IP許可設定）
mysql -h [INSTANCE_PUBLIC_IP] -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME
```

### 3. gcloudコマンド経由

```bash
# パスワード自動入力での接続
export MYSQL_PWD="$DB_PASSWORD"
gcloud sql connect $DB_INSTANCE_NAME --user=$DB_USER
```

### 4. 接続確認コマンド例

```bash
# データベース一覧
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE -e "SHOW DATABASES;"

# テーブル一覧
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME -e "SHOW TABLES;"

# ユーザー情報確認
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" --ssl-mode=$SSL_MODE $DB_NAME -e "SELECT COUNT(*) FROM users;"
```

### 5. アプリケーション設定例

#### Node.js (mysql2)

```javascript
const mysql = require('mysql2/promise');
require('dotenv').config({ path: 'config.env' }); // 基本設定
require('dotenv').config({ path: '.env' });       // パスワード情報

const config = {
  host: process.env.DB_HOST,     // 127.0.0.1（Cloud SQL Proxy使用時）
  port: process.env.DB_PORT,     // 3306
  user: process.env.DEFAULT_USER,     // default
  password: process.env.DEFAULT_PASSWORD,
  database: process.env.DB_NAME, // default
  ssl: process.env.SSL_MODE === 'REQUIRED' ? { rejectUnauthorized: false } : false
};

const connection = await mysql.createConnection(config);
```

#### Python (mysql-connector-python)

```python
import mysql.connector
import os
from dotenv import load_dotenv

# 基本設定とパスワード情報を読み込み
load_dotenv('config.env')  # 基本設定
load_dotenv('.env')        # パスワード情報

config = {
    'host': os.getenv('DB_HOST'),        # 127.0.0.1（Cloud SQL Proxy使用時）
    'port': os.getenv('DB_PORT'),        # 3306
    'user': os.getenv('DEFAULT_USER'),   # default
    'password': os.getenv('DEFAULT_PASSWORD'),
    'database': os.getenv('DB_NAME'),    # default
    'ssl_disabled': os.getenv('SSL_MODE') == 'DISABLED'
}
  password: process.env.DB_PASSWORD,  // 環境変数またはdb-credentials.txtから取得
  database: 'default',
  charset: 'utf8mb4'
};

const connection = await mysql.createConnection(config);
```

#### Python (PyMySQL)

```python
import pymysql

connection = pymysql.connect(
    host='127.0.0.1',        # Cloud SQL Proxy使用時
    port=3306,
    user='default',
    password=os.environ['DB_PASSWORD'],  # 環境変数またはdb-credentials.txtから取得
    database='default',
    charset='utf8mb4'
)
```

## セキュリティ設定

### 接続制限

現在の設定では開発用として全IPからの接続を許可しています。
本番環境では以下の設定を推奨します：

```bash
# 特定IPのみ許可（例：オフィスIP）
gcloud sql instances patch cloudsql-01 \
  --authorized-networks=YOUR_OFFICE_IP/32

# SSL強制
gcloud sql instances patch cloudsql-01 \
  --require-ssl
```

### 認証情報の確認

```bash
# 接続情報の確認（セットアップ後に生成されるファイル）
cat db-credentials.txt
```

## データアクセスパターン

### よく使用されるクエリ例

#### 利用者検索

```sql
-- 電話番号での利用者検索
SELECT * FROM users WHERE phone_number = ?;

-- 今日電話すべき利用者検索
SELECT * FROM users 
WHERE call_weekday = DAYNAME(CURDATE()) 
  AND call_time BETWEEN ? AND ?;
```

#### イベント検索

```sql
-- 今後のイベント一覧
SELECT * FROM events 
WHERE start_datetime >= NOW() 
ORDER BY start_datetime;

-- 地域別イベント検索
SELECT * FROM events 
WHERE prefecture = ? 
  AND start_datetime >= NOW() 
ORDER BY start_datetime;
```

## 監視・メンテナンス

### パフォーマンス監視

```bash
# インスタンス状態確認
gcloud sql instances describe cloudsql-01

# 接続数確認
gcloud sql operations list --instance=cloudsql-01 --limit=10
```

### バックアップ設定

現在の設定では自動バックアップが有効です：

- バックアップ時刻：3:00 AM（JST）
- 保持期間：7日間
- バイナリログ：有効

## トラブルシューティング

### 接続エラー

1. **接続できない場合**
   ```bash
   # インスタンス状態確認
   gcloud sql instances describe cloudsql-01 --format="get(state)"
   
   # 認証ネットワーク確認
   gcloud sql instances describe cloudsql-01 --format="get(settings.ipConfiguration.authorizedNetworks)"
   ```

2. **権限エラー**
   ```sql
   -- ユーザー権限確認
   SHOW GRANTS FOR 'default'@'%';
   ```

### パスワードリセット

```bash
# アプリケーションユーザーのパスワードリセット
gcloud sql users set-password default \
  --instance=cloudsql-01 \
  --password=NEW_PASSWORD
```

### ログ確認

```bash
# エラーログ確認
gcloud logging read "resource.type=gce_instance AND logName=projects/PROJECT_ID/logs/mysql.err" --limit=50
```
- MySQL 8.4のUUID()関数でサーバサイド生成
- 日時範囲による効率的な検索が可能

## 設計方針

### 1. プライマリキー
- すべてのテーブルでUUID（CHAR(36)）を使用
- MySQL 8.4のUUID()関数でサーバサイド生成

### 2. 文字セット・照合順序
- utf8mb4文字セット使用（絵文字対応）
- utf8mb4_unicode_ci照合順序使用

### 3. タイムスタンプ
- created_at: 作成時の自動設定
- updated_at: 更新時の自動更新

### 4. シンプルな構成
- 基本的な利用者管理（users）とイベント管理（events）に特化
- 必要最小限のテーブル構成で運用効率を重視

### 5. インデックス戦略
- 現在は基本的なプライマリキー（UUID）のみ設定
- 必要に応じて検索頻度の高いカラムにインデックスを追加予定
- パフォーマンス要件に応じた段階的なインデックス追加

## パフォーマンス考慮事項

### 1. 検索最適化（将来の検討事項）
- 氏名検索用複合インデックス（users）
- 日時範囲検索用インデックス（events）
- 地域検索用インデックス（users, events）

### 2. ストレージ最適化
- 適切なデータ型選択
- 不要なNULL値制約の排除

### 3. 運用最適化
- 定期的なインデックス統計更新
- スロークエリログの監視

## 将来の拡張予定

現在はシンプルな構成ですが、以下の機能追加を検討可能です：

### 安否確認機能
- safety_checksテーブル（安否確認記録）
- 確認方法、結果、備考等の管理

### イベント参加管理機能  
- event_participantsテーブル（イベント参加者管理）
- 参加登録、出欠状況の管理

これらの機能は必要に応じて段階的に追加できる設計になっています。
