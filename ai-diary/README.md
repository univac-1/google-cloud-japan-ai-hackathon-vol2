# AI Diary Service

ユーザー情報取得 + 会話履歴取得 + AI日記生成の統合APIサービス

## 概要

- userIDとcallIDを受け取り、以下の一連の処理を実行：
  1. userIDをもとにRDBからユーザー情報を取得
  2. userIDとcallIDをもとにFirestoreから会話履歴を取得  
  3. **NEW**: 取得した情報を使ってGemini APIで家族向けの日記風文章を生成
- anpi-call-dbで作成されたCloud SQL for MySQLに接続
- Flask RESTful APIとして実装

## メインAPI

### `/generate-diary` - 完全な日記生成API
ユーザー情報取得→会話履歴取得→日記生成の一連の処理を実行

```bash
POST /generate-diary
{
    "userID": "user123",
    "callID": "call456"
}
```

詳細な使用方法は [API_USAGE.md](API_USAGE.md) を参照してください。

## プロジェクト構成

```
ai-diary/
├── main.py                  # メインAPIサーバー（Flask）
├── get_info/               # ユーザー情報取得処理パッケージ
│   ├── __init__.py         # パッケージ初期化
│   ├── db_connection.py    # DB接続処理
│   ├── user_service.py     # ユーザー情報取得処理
│   ├── test_service.py     # テストスクリプト
│   └── README.md           # パッケージ説明
├── get_history/            # 会話履歴取得処理パッケージ
│   ├── __init__.py         # パッケージ初期化
│   ├── firestore_info.py   # Firestore接続・情報確認
│   ├── conversation_service.py    # 会話履歴取得サービス
│   ├── subcollection_conversation_service.py # サブコレクション会話履歴サービス
│   ├── test_api.py         # API総合テスト
│   └── README.md           # パッケージ説明
├── create_diary_entry/     # 日記生成処理パッケージ (NEW)
│   ├── __init__.py         # パッケージ初期化
│   ├── gemini_service.py   # Gemini API日記生成サービス
│   ├── gemini_test.py      # Gemini API動作確認テスト
│   └── README.md           # パッケージ説明
├── .env                    # 環境設定（ローカル開発用）
├── config.env              # 基本設定（非推奨）
├── requirements.txt        # Python依存関係
├── start_service.sh        # サービス起動スクリプト（DB接続チェック付き）
├── start_cloud_sql_proxy.sh # Cloud SQL Proxy起動ヘルパー（NEW）
├── check_db_connection.sh  # データベース接続状況チェック（NEW）
├── test_service.sh         # テストスクリプト
├── test_gemini_api.sh      # Gemini APIテストスクリプト
├── test_specified_params.sh # 指定パラメータテストスクリプト（NEW）
├── venv/                  # Python仮想環境
└── README.md              # このファイル
```

## 前提条件

⚠️ **重要: データベース接続のための必須手順**

### 1. Cloud SQL Proxyの起動（必須）

**データベースを使用するAPIテストの前に、必ずCloud SQL Proxyを起動してください：**

```bash
# 新しいターミナルを開いて以下を実行（バックグラウンドで常時動作）
cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
```

**確認方法：**
```bash
# Cloud SQL Proxyが起動しているか確認
ps aux | grep cloud_sql_proxy | grep -v grep

# 期待する出力例:
# yasami    12345  0.1  0.2 1234567 89012 ?  S  17:13  0:00 cloud_sql_proxy --instances=...
```

**注意事項：**
- Cloud SQL Proxyを起動せずにAPIテストを実行すると「MySQL server connection error」が発生します
- 一度起動すると、ターミナルを閉じるまで動作し続けます
- 複数のテストを実行する場合は、同一セッションで実行してください

### 2. Gemini API キーの設定（必須）
### 2. Gemini API キーの設定（必須）

- [Google AI Studio](https://ai.google.dev/) でAPIキーを取得
- 環境変数に設定: `export GEMINI_API_KEY=your_api_key_here`
- または `.env` ファイルに記載済み

### 3. 依存関係のインストール（初回のみ）
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## クイックスタート

### ⚠️ 必読: 初回実行前の準備

**📚 詳細な手順書: [LOCAL_EXECUTION_GUIDE.md](LOCAL_EXECUTION_GUIDE.md)**

**1. データベース接続の準備（必須）**
```bash
# ターミナル1: Cloud SQL Proxy起動（常時実行）
./start_cloud_sql_proxy.sh

# または手動で:
# cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
```

**2. 接続状況の確認**
```bash
# ターミナル2: 接続状況チェック
./check_db_connection.sh
```

### 1. テスト実行

```bash
# 基本機能テスト（データベース接続必須）
./test_service.sh

# Gemini API動作テスト（データベース接続不要）
./test_gemini_api.sh

# 指定パラメータでの完全テスト（データベース接続必須）
./test_specified_params.sh
```

### 2. サービス起動

```bash
# 自動チェック付きサービス起動
./start_service.sh
```

サービスは http://localhost:8080 で起動します。

## 手動実行方法

環境変数を手動で設定して実行する場合：

```bash
source venv/bin/activate
source .env
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

### Gemini API接続テスト (NEW)

```
GET /test-gemini
```

### 日記生成 (NEW) - 推奨エンドポイント

```
POST /generate-diary
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
  "data": {
    "userID": "test-user-001",
    "callID": "call-12345",
    "userInfo": {
      "user_id": "test-user-001",
      "last_name": "山田",
      "first_name": "太郎",
      "phone_number": "090-1234-5678",
      "address": "東京都渋谷区..."
    },
    "conversationHistory": {
      "conversation": [
        {"role": "assistant", "text": "おはようございます、山田さん。"},
        {"role": "user", "text": "おはよう。今日は孫が来るんだ。"}
      ]
    },
    "diary": "2024年12月01日 山田太郎さんの一日\n\n今日の山田太郎さんはとても嬉しそうでした。孫が遊びに来ることを楽しみにしていて..."
  },
  "message": "ユーザー情報、会話履歴、日記を正常に生成しました"
}
```

### ユーザー情報と会話履歴取得

```
POST /get-user-and-conversation
Content-Type: application/json

{
  "userID": "ユーザーID",
  "callID": "コールID"
}
```

### ユーザー情報取得 (レガシー)

```
POST /get-user-info
Content-Type: application/json

{
  "userID": "ユーザーID",
  "callID": "コールID"
}
```

### 会話履歴取得 (レガシー)

```
POST /get-conversation-history-v2
Content-Type: application/json

{
  "userID": "ユーザーID",
  "callID": "コールID"
}
```

### ユーザーのすべての会話履歴取得

```
POST /get-user-calls
Content-Type: application/json

{
  "userID": "ユーザーID"
}
```

## API使用例

### curlコマンドでのテスト

```bash
# ヘルスチェック
curl http://localhost:8080/health

# DB接続テスト
curl http://localhost:8080/test-db

# Gemini API接続テスト (NEW)
curl http://localhost:8080/test-gemini

# 日記生成 (NEW)
curl -X POST http://localhost:8080/generate-diary \
  -H "Content-Type: application/json" \
  -d '{"userID": "test-user-001", "callID": "call-12345"}'

# ユーザー情報と会話履歴取得
curl -X POST http://localhost:8080/get-user-and-conversation \
  -H "Content-Type: application/json" \
  -d '{"userID": "test-user-001", "callID": "call-12345"}'
```

## 新機能: 日記生成 (NEW)

### 概要

Gemini APIを使用して、ユーザー情報と会話履歴から家族向けの温かい日記風の文章を自動生成します。

### 特徴

- **家族向け**: 家族が読んで安心できる内容に調整
- **温かみのある表現**: 敬語を使わず親しみやすい文体
- **プライバシー配慮**: センシティブな情報を適切に処理
- **自動要約**: 会話の要点を自然な文章にまとめ

### 使用方法

1. **APIキー設定**: Gemini API キーを環境変数に設定
2. **エンドポイント呼び出し**: `/generate-diary` にPOSTリクエスト
3. **日記取得**: レスポンスの `diary` フィールドに生成された日記

### 出力例

```
2024年12月01日 山田太郎さんの一日

今日の山田太郎さんはとても嬉しそうでした。孫が遊びに来ることを楽しみにしていて、一緒に近所の公園へお散歩に行く予定を立てています。お天気も良く、きっと素敵な時間を過ごせそうです。久しぶりに孫と会えることを心から楽しみにしている様子が伝わってきました。
```

## 技術仕様

- **フレームワーク**: Flask
- **データベース**: Cloud SQL for MySQL
- **NoSQL**: Cloud Firestore
- **AI**: Gemini 2.5 Flash API (NEW)
- **認証**: mysql-connector-python with caching_sha2_password
- **ポート**: 8080
- **環境**: 開発環境（TCP接続）/ Cloud Run環境（Unix socket）対応

## 環境変数

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `DB_PASSWORD` | データベースパスワード | ✅ |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud プロジェクトID | ✅ |
| `GEMINI_API_KEY` | Gemini API キー | ✅ (日記生成機能使用時) |

## トラブルシューティング

### 接続エラーが発生する場合

1. Cloud SQL Proxyが起動しているか確認
2. 環境変数が正しく設定されているか確認
3. ネットワーク接続を確認

### Gemini API関連エラー (NEW)

1. `GEMINI_API_KEY` 環境変数が設定されているか確認
2. APIキーが有効かGoogle AI Studioで確認
3. APIの利用制限に達していないか確認

## 動作確認

### テスト用パラメータ

動作確認には以下の固定パラメータを使用します：

- **userID**: `4CC0CA6A-657C-4253-99FF-C19219D30AE2`
- **callID**: `CA995a950a2b9f6623a5adc987d0b31131`

### 1. Gemini API単体テスト（DB接続不要）

```bash
# 仮想環境をアクティベート
source ai_diary_env/bin/activate

# Gemini APIキーを設定
export GEMINI_API_KEY="your_gemini_api_key_here"

# サンプルデータでの日記生成テスト
python test_sample_data.py

# 基本的なGemini API接続テスト
python test_gemini_simple.py

# より詳細なGemini APIテスト
python test_gemini_local.py
```

### 2. DB接続を含む統合テスト

```bash
# Cloud SQL Proxyが起動していることを確認
# cloud_sql_proxy -instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306

# 統合テスト実行（DB接続、ユーザー情報取得、会話履歴取得、日記生成）
python test_integration.py
```

### 3. Flaskサーバー起動・API動作確認

```bash
# サーバー起動
python main.py

# 別ターミナルでAPIテスト
curl -X POST http://localhost:8080/generate-diary \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "callID": "CA995a950a2b9f6623a5adc987d0b31131"
  }'
```

### 4. テストスクリプト一覧

| スクリプト名 | 説明 | DB接続要 | Gemini API要 |
|-------------|------|----------|--------------|
| `test_sample_data.py` | サンプルデータでの日記生成テスト | ❌ | ✅ |
| `test_gemini_simple.py` | 基本的なGemini API接続テスト | ❌ | ✅ |
| `test_gemini_local.py` | 詳細なGemini APIテスト | ❌ | ✅ |
| `test_integration.py` | DB接続を含む統合テスト | ✅ | ✅ |
| `comprehensive_test.py` | API経由での総合テスト | ✅ | ✅ |

### 5. 動作確認の結果例

#### 成功時の日記生成例
```
タイトル: 2025年06月28日 田中さんの一日

今日は朝から調子がいいんだ！久しぶりに体が軽くて、なんだか嬉しい一日になりそう。
朝ごはんもいつもよりたくさん食べられたしね。午前中はゆっくりとラジオ体操をして、
庭の草花に水をあげたよ。

午後には、娘と孫娘が遊びに来てくれる予定なんだ！7歳になる元気いっぱいの女の子でね、
一緒に絵を描く約束をしているんだ。孫娘が来るってだけで、家の中が明るくなった気がする。
久しぶりに賑やかな時間になるのが、本当に楽しみ！
```