# データベース仕様書 - 外部システム連携用

## 接続先
### 接続ルール
接続先の環境はCloudSQLであり、接続にはCloud SQL Python Connectorをつかうこと
接続に必要な情報は、.envから読み取ること



### 標準リソース名

| リソース | 名前 | 説明 |
|---------|------|------|
| Cloud SQLインスタンス | `cloudsql-01` | メインのデータベースインスタンス |
| データベース | `default` | アプリケーション用データベース |
| アプリケーションユーザー | `default` | 読み書き権限を持つユーザー |
| 管理ユーザー | `root` | 管理権限を持つユーザー |


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
