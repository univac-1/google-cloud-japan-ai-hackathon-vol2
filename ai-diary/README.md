# AI Diary Service

ユーザー情報取得APIサービス

## 概要

- userIDとcallIDを受け取り、userIDをもとにRDBからユーザー情報を取得するAPIサービス
- anpi-call-dbで作成されたCloud SQL for MySQLに接続してユーザー情報を取得
- Flask RESTful APIとして実装

## プロジェクト構成

```
ai-diary/
├── main.py              # メインAPIサーバー（Flask）
├── get-info/            # ユーザー情報取得処理パッケージ
│   ├── __init__.py      # パッケージ初期化
│   ├── db_connection.py # DB接続処理
│   ├── user_service.py  # ユーザー情報取得処理
│   ├── test_service.py  # テストスクリプト
│   └── README.md        # パッケージ説明
├── config.env           # 基本設定
├── requirements.txt     # Python依存関係
├── start_service.sh     # サービス起動スクリプト
├── test_service.sh      # テストスクリプト
├── venv/               # Python仮想環境
└── README.md           # このファイル
```

## 前提条件

1. **Cloud SQL Proxyの起動**が必要です：
   ```bash
   cloud_sql_proxy -instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
   ```

2. **依存関係のインストール**（初回のみ）：
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## クイックスタート

### 1. テスト実行

```bash
./test_service.sh
```

### 2. サービス起動

```bash
./start_service.sh
```

サービスは http://localhost:8081 で起動します。

## 手動実行方法

環境変数を手動で設定して実行する場合：

```bash
source venv/bin/activate
source config.env
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="
export GOOGLE_CLOUD_PROJECT=univac-aiagent
python main.py
```

## APIエンドポイント

### ヘルスチェック

```
GET /health
```

### DB接続テスト

```
GET /test-db
```

### ユーザー情報取得

```
POST /get-user-info
Content-Type: application/json

{
  "userID": "ユーザーID",
  "callID": "コールID"
}
```

#### レスポンス例（成功）

```json
{
  "status": "success",
  "userID": "test-user-001",
  "callID": "call-12345",
  "userInfo": {
    "user_id": "test-user-001",
    "last_name": "山田",
    "first_name": "太郎",
    "phone_number": "090-1234-5678",
    "address": "東京都渋谷区..."
  }
}
```

#### レスポンス例（エラー）

```json
{
  "status": "error",
  "userID": "test-user-001",
  "callID": "call-12345",
  "message": "ユーザーが見つかりませんでした"
}
```

## API使用例

### curlコマンドでのテスト

```bash
# ヘルスチェック
curl http://localhost:8081/health

# DB接続テスト
curl http://localhost:8081/test-db

# ユーザー情報取得
curl -X POST http://localhost:8081/get-user-info \
  -H "Content-Type: application/json" \
  -d '{"userID": "test-user-001", "callID": "call-12345"}'
```

## 技術仕様

- **フレームワーク**: Flask
- **データベース**: Cloud SQL for MySQL
- **認証**: mysql-connector-python with caching_sha2_password
- **ポート**: 8081
- **環境**: 開発環境（TCP接続）/ Cloud Run環境（Unix socket）対応

## トラブルシューティング

### 接続エラーが発生する場合

1. Cloud SQL Proxyが起動しているか確認
2. 環境変数が正しく設定されているか確認
3. ネットワーク接続を確認

### パッケージ開発

処理ロジックの開発やテストについては `get-info/README.md` を参照してください。 