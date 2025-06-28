# AI Diary API 使用方法

## 日記生成API

### エンドポイント: `/generate-diary`

ユーザー情報取得→会話履歴取得→日記生成の一連の処理を行う完全なAPIです。

#### リクエスト

```bash
POST /generate-diary
Content-Type: application/json

{
    "userID": "user123",
    "callID": "call456"
}
```

#### レスポンス（成功時）

```json
{
    "status": "success",
    "data": {
        "userID": "user123",
        "callID": "call456",
        "userInfo": {
            "id": "user123",
            "name": "田中太郎",
            "age": 30,
            "location": "東京都",
            "preferences": {...}
        },
        "conversationHistory": {
            "callID": "call456",
            "timestamp": "2025-06-28T10:00:00Z",
            "messages": [
                {
                    "speaker": "user",
                    "message": "今日は良い天気ですね",
                    "timestamp": "2025-06-28T10:00:15Z"
                },
                {
                    "speaker": "system",
                    "message": "そうですね。お散歩日和ですね",
                    "timestamp": "2025-06-28T10:00:30Z"
                }
            ]
        },
        "diary": "今日は素晴らしい一日でした。お天気も良く、心地よい会話を楽しむことができました..."
    },
    "message": "ユーザー情報、会話履歴、日記を正常に生成しました"
}
```

#### エラーレスポンス

```json
{
    "status": "error",
    "error_code": "USER_NOT_FOUND",
    "message": "ユーザーが見つかりませんでした"
}
```

#### 可能なエラーコード

- `USER_NOT_FOUND` (404): ユーザーが見つからない
- `CONVERSATION_NOT_FOUND` (404): 会話履歴が見つからない
- `DIARY_GENERATION_ERROR` (500): 日記生成に失敗
- `GEMINI_API_KEY_ERROR` (500): Gemini APIキーが未設定
- `BAD_REQUEST` (400): リクエストデータが不正
- `INTERNAL_ERROR` (500): 内部サーバーエラー

## 使用例

### curl での実行例

```bash
curl -X POST http://localhost:8080/generate-diary \
  -H "Content-Type: application/json" \
  -d '{
    "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "callID": "CA995a950a2b9f6623a5adc987d0b31131"
  }'
```

### Python での実行例

```python
import requests
import json

url = "http://localhost:8080/generate-diary"
data = {
    "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "callID": "CA995a950a2b9f6623a5adc987d0b31131"
}

response = requests.post(url, json=data)
result = response.json()

if result["status"] == "success":
    print("日記生成成功:")
    print(result["data"]["diary"])
else:
    print(f"エラー: {result['message']}")
```

## 処理フロー

1. **ユーザー情報取得**: `userID` を使ってデータベースからユーザー情報を取得
2. **会話履歴取得**: `userID` と `callID` を使ってFirestoreから会話履歴を取得
3. **日記生成**: ユーザー情報と会話履歴を元にGemini APIを使用して日記を生成

## 部分的なAPI

### `/get-user-and-conversation`
ユーザー情報と会話履歴のみを取得（日記生成なし）

### `/test-gemini`
Gemini API の接続テスト

### `/health`
サービスのヘルスチェック

## 設定要件

- `GEMINI_API_KEY`: Gemini API キー
- データベース接続設定
- Firestore 接続設定
