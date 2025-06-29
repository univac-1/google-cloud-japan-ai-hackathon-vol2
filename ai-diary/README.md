# AI Diary Service

AI日記生成統合APIサービス

## 機能

ユーザー情報と会話履歴から家族向けの日記を自動生成し、メールで送信します。

1. **ユーザー情報取得** - Cloud SQL（MySQL）からユーザー情報を取得
2. **会話履歴取得** - Firestoreから会話履歴を取得
3. **日記生成** - Gemini APIで家族向けの日記風文章を生成
4. **挿絵作成** - Vertex AI Imagenでイラストを生成
5. **HTML生成** - 日記をHTMLページに変換
6. **メール送信** - 生成されたコンテンツをメールで送信

## API エンドポイント

### `/health` - ヘルスチェック
```bash
GET /health
```

### `/test-db` - データベース接続テスト
```bash
GET /test-db
```

### `/generate-diary` - 日記生成（メイン機能）
```bash
POST /generate-diary
{
    "userID": "user123",
    "callID": "call456"
}
```

## プロジェクト構成

- `main.py` - Flask APIサーバー
- `get_info/` - ユーザー情報取得（Cloud SQL）
- `get_history/` - 会話履歴取得（Firestore）
- `create_diary_entry/` - 日記生成（Gemini API）
- `illustration/` - 挿絵生成（Vertex AI Imagen）
- `html_generator/` - HTML生成
- `email_sender/` - メール送信
- `test/` - テストファイル（最小限）

## デプロイ

```bash
gcloud builds submit --config cloudbuild.yaml
```

詳細な使用方法は [API_USAGE.md](API_USAGE.md) を参照してください。
