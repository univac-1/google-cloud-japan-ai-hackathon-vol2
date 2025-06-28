# AI Diary - 会話履歴取得機能

## 概要

ai-diary プロジェクトの新機能として、Firestore から会話履歴情報を取得する処理を実装しました。ユーザー情報取得後、パラメータの callID を使って会話履歴を取得する API エンドポイントを提供します。

## 🚀 実装された機能

### 1. Firestore 接続・リソース情報確認
- **ファイル**: `firestore_info.py`
- **機能**: Firestore への接続テスト、リソース情報の確認・記録
- **結果**: ✅ 接続成功、既存コレクション `users` を確認

### 2. テストデータ作成
- **ファイル**: `create_test_data.py`
- **機能**: ユーザー情報と会話履歴のテストデータ作成
- **作成データ**:
  - ユーザー: 2名（田中太郎、佐藤花子）
  - 会話履歴: 3件（朝・夜の会話、体調に関する会話）

### 3. 会話履歴取得サービス
- **ファイル**: `conversation_service.py`
- **クラス**: `ConversationHistoryService`
- **主要メソッド**:
  - `get_user_info()`: ユーザー情報取得
  - `get_conversation_by_call_id()`: callID による会話履歴取得
  - `get_conversation_history()`: メイン処理（ユーザー認証 + 会話履歴取得）

### 4. API エンドポイント
- **エンドポイント**: `POST /get-conversation-history`
- **リクエスト形式**:
  ```json
  {
    "userID": "user001",
    "callID": "call_001_20241201_morning"
  }
  ```
- **レスポンス形式**:
  ```json
  {
    "status": "success",
    "user_id": "user001",
    "call_id": "call_001_20241201_morning",
    "user_info": {
      "name": "田中太郎",
      "age": 75,
      "phone": "090-1234-5678"
    },
    "conversation": {
      "conversation": [
        {
          "speaker": "system",
          "message": "おはようございます、田中さん。今日の体調はいかがですか？",
          "timestamp": "..."
        }
      ],
      "analysis": {
        "mood": "positive",
        "health_indicators": ["good_sleep", "active_plan"]
      }
    },
    "retrieved_at": "2025-06-28T14:46:37.283895"
  }
  ```

## 📊 データ構造

### Users コレクション
```json
{
  "user_id": "user001",
  "name": "田中太郎",
  "age": 75,
  "phone": "090-1234-5678",
  "emergency_contact": "090-8765-4321",
  "created_at": "SERVER_TIMESTAMP"
}
```

### Conversations コレクション
```json
{
  "call_id": "call_001_20241201_morning",
  "user_id": "user001",
  "timestamp": "datetime",
  "duration_seconds": 180,
  "status": "completed",
  "conversation": [
    {
      "speaker": "system|user",
      "message": "会話内容",
      "timestamp": "datetime"
    }
  ],
  "analysis": {
    "mood": "positive|neutral|negative",
    "health_indicators": ["indicator1", "indicator2"],
    "concerns": ["concern1", "concern2"]
  }
}
```

## 🛡️ エラーハンドリング

| エラーコード | HTTPステータス | 説明 |
|-------------|----------------|------|
| `USER_NOT_FOUND` | 404 | 指定されたユーザーIDが見つからない |
| `CONVERSATION_NOT_FOUND` | 404 | 指定されたcallIDの会話履歴が見つからない |
| `USER_MISMATCH` | 403 | callIDがユーザーの会話ではない |
| `INTERNAL_ERROR` | 500 | 内部サーバーエラー |

## 🧪 テスト結果

### 総合テスト結果
- **実行したテスト数**: 6件
- **成功**: 6件
- **失敗**: 0件  
- **成功率**: 100.0% ✅

### テストケース
1. ✅ 正常ケース - user001 朝の会話
2. ✅ 正常ケース - user001 夜の会話  
3. ✅ 正常ケース - user002 朝の会話
4. ✅ エラーケース - 存在しないユーザー
5. ✅ エラーケース - 存在しないcallID
6. ✅ エラーケース - ユーザーIDミスマッチ

## 🔧 使用方法

### 1. 環境準備
```bash
# 仮想環境アクティベート
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt

# 環境変数読み込み
source .env
```

### 2. サービス起動
```bash
python main.py
```

### 3. API呼び出し例
```bash
curl -X POST http://localhost:8080/get-conversation-history \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "user001",
    "callID": "call_001_20241201_morning"
  }'
```

### 4. テスト実行
```bash
# 会話履歴取得サービステスト
python get_history/conversation_service.py

# API総合テスト
python get_history/test_api.py
```

## 📁 ファイル構成

```
ai-diary/get_history/
├── __init__.py                    # モジュール初期化
├── firestore_info.py             # Firestore接続・情報確認
├── examine_data.py               # データ構造調査
├── create_test_data.py           # テストデータ作成
├── conversation_service.py       # 会話履歴取得サービス
├── test_api.py                   # API総合テスト
└── README.md                     # このファイル
```

## 🔄 追加された依存関係

```txt
google-cloud-firestore==2.11.1
requests==2.28.2
```

## 🌟 特徴

- **セキュリティ**: ユーザーIDとcallIDの照合により、不正アクセスを防止
- **エラーハンドリング**: 詳細なエラーコードとメッセージを提供
- **スケーラビリティ**: Firestore を使用した高可用性設計
- **テスタビリティ**: 包括的なテストスイートを提供
- **ログ機能**: 詳細なログ出力による運用サポート

## 📚 今後の拡張予定

- 会話履歴の期間指定検索
- 複数callIDの一括取得
- リアルタイム更新通知
- アナリティクス機能の強化

---

**作成者**: AI Diary Team  
**作成日**: 2025年6月28日  
**バージョン**: 1.0.0 