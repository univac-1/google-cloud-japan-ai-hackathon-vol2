# AI Diary Get Info Package

ユーザー情報取得処理パッケージ

## 概要

- userIDをもとにRDBからユーザー情報を取得する処理を提供
- anpi-call-dbで作成されたDBに接続してユーザー情報を取得
- **処理ロジックのみを含むパッケージ**（APIエンドポイントは`ai-diary/main.py`に配置）

## パッケージ構成

```
get-info/
├── __init__.py          # パッケージ初期化
├── db_connection.py     # DB接続処理
├── user_service.py      # ユーザー情報取得処理
├── test_service.py      # テストスクリプト
└── README.md           # このファイル
```

## 使用方法

### APIサービスとしての実行

APIエンドポイントは`ai-diary/main.py`に実装されています。

```bash
cd ai-diary
./start_service.sh
```

詳細な使用方法は`ai-diary/README.md`を参照してください。

### 処理のテスト

このパッケージ内の処理をテストする場合：

```bash
cd ai-diary
./test_service.sh
```

または手動で：

```bash
cd ai-diary
source venv/bin/activate
source config.env
export DB_PASSWORD="TH8V+cqXJOPqRl3Ez4RAg+mQvnlkQmqh/r14epk2BT0="
export GOOGLE_CLOUD_PROJECT=univac-aiagent
cd get-info
python test_service.py
```

## モジュール説明

### db_connection.py

- `get_connection()`: DB接続オブジェクトを取得
- `test_connection()`: DB接続テスト

### user_service.py

- `get_user_info(user_id)`: ユーザー情報を取得
- `test_get_user()`: ユーザー情報取得のテスト

### パッケージからのインポート

他のモジュールからこのパッケージを使用する場合：

```python
from get_info.user_service import get_user_info
from get_info.db_connection import test_connection

# または
from get_info import get_user_info, test_connection
```

## 前提条件

1. **Cloud SQL Proxyの起動**が必要です：
   ```bash
   cloud_sql_proxy -instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
   ```

2. **環境変数の設定**が必要です（ai-diary/config.envと実際のパスワード）

3. **依存関係のインストール**（初回のみ）：
   ```bash
   cd ai-diary
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## APIエンドポイント

APIエンドポイントは`ai-diary/main.py`に実装されています：

- `GET /health` - ヘルスチェック
- `GET /test-db` - DB接続テスト  
- `POST /get-user-info` - ユーザー情報取得（userIDとcallIDが必要）

詳細は`ai-diary/main.py`を参照してください。 