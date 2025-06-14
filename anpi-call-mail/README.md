# 🚨 安否確認システム - 自治体通報機能

安否確認電話の結果、直接訪問が必要と判断された場合に自治体へ緊急通報メールを送信するGCP Cloud Functionsシステムです。

**Gmail APIを使用**してメール送信を行います。

## 🚀 クイックスタート

### 1. Gmail API設定
1. Google Cloud ConsoleでGmail APIを有効化
2. サービスアカウントを作成しJSONキーファイルをダウンロード
3. 詳細は `gmail_setup_guide.md` を参照

### 2. 環境変数設定
```bash
./setup_env.sh
```

### 3. デプロイ実行
```bash
./setup_and_deploy.sh
```

### 4. 安否確認通報テスト
```bash
# デフォルト値でテスト
./test.sh

# カスタム値でテスト
./test.sh safety@city.tokyo.jp 田中 太郎 090-1234-5678
```

## 📁 ファイル構成

```
├── main.py                    # Cloud Function メインコード（Gmail API使用）
├── requirements.txt           # Python依存関係
├── setup_env.sh              # 環境変数設定スクリプト
├── setup_and_deploy.sh       # 自動デプロイスクリプト
├── setup_secret_manager.sh   # Secret Manager設定スクリプト
├── test.sh                   # テストスクリプト
├── gmail_setup_guide.md      # Gmail API設定ガイド
└── README.md                 # このファイル
```

## 📧 API仕様

### エンドポイント
```
POST https://asia-northeast1-univac-aiagent.cloudfunctions.net/send-mail
```

### リクエスト
```json
{
    "to": "safety@city.tokyo.jp",
    "last_name": "田中",
    "first_name": "太郎", 
    "phone_number": "090-1234-5678",
    "timestamp": "2025-06-14 13:45:30"
}
```

### レスポンス
**成功時（200）:**
```json
{
    "status": "success",
    "message": "Safety check notification sent to local government",
    "target_person": "田中 太郎",
    "phone_number": "090-1234-5678",
    "sent_to": "safety@city.tokyo.jp",
    "gmail_message_id": "187abc123..."
}
```

## 🔧 使用例

### 安否確認システムからの自動通報
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "to": "safety@city.tokyo.jp",
    "last_name": "田中",
    "first_name": "太郎",
    "phone_number": "090-1234-5678",
    "timestamp": "2025-06-14 13:45:30"
  }' \
  $(cat function_url.txt)
```

### メール内容の特徴
- 📧 緊急性を伝える件名と本文
- 👤 対象者の基本情報（氏名・電話番号）
- ⏰ 通報時刻の記録
- 📋 自治体向けの対応手順
- 🚨 HTMLフォーマットによる視認性向上

## ⚠️ 注意事項

1. **Gmail API認証**: Google Cloud ConsoleでGmail APIの有効化とサービスアカウントの設定が必要です
2. **送信制限**: Gmail APIには1日あたりの送信数制限があります（個人Gmail: 500通/日、Google Workspace: 10,000通/日）
3. **緊急性**: このシステムは緊急時の自治体通報用です。テスト時は実際の自治体アドレスを使用しないでください
4. **個人情報**: 安否確認対象者の個人情報を適切に管理してください
5. **ドメイン全体の委任**: Google Workspaceアカウントから送信する場合は、ドメイン全体の委任設定が必要です

## 📚 詳細ドキュメント

- [Gmail API設定ガイド](gmail_setup_guide.md) - Gmail APIの詳細設定方法
