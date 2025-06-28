# サブコレクション構造対応 会話履歴取得システム

## 概要

Firestoreのサブコレクション構造 `users/{userID}/calls/{callID}` に対応した会話履歴取得システムです。

## Firestore データ構造

```
/users/{userID}                    # ユーザー情報ドキュメント
├── calls/{callID}                 # 会話履歴サブコレクション
│   ├── conversation              # 会話内容配列
│   ├── ai_analysis              # AI分析結果
│   ├── metadata                 # メタデータ
│   └── ...                      # その他の会話関連情報
```

### 例: 指定されたID
- **UserID**: `4CC0CA6A-657C-4253-99FF-C19219D30AE2`
- **CallID**: `CA995a950a2b9f6623a5adc987d0b31131`
- **Firestoreパス**: `users/4CC0CA6A-657C-4253-99FF-C19219D30AE2/calls/CA995a950a2b9f6623a5adc987d0b31131`

## 実装ファイル

### 1. サービスクラス
- **ファイル**: `subcollection_conversation_service.py`
- **クラス**: `SubcollectionConversationHistoryService`
- **機能**:
  - ユーザー情報取得
  - 会話履歴取得（単一）
  - 全会話履歴取得
  - データ整合性チェック

### 2. APIエンドポイント

#### `/get-conversation-history-v2` (POST)
**説明**: 指定されたuserIDとcallIDで単一の会話履歴を取得

**リクエスト**:
```json
{
  "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
  "callID": "CA995a950a2b9f6623a5adc987d0b31131"
}
```

**レスポンス例**:
```json
{
  "status": "success",
  "data": {
    "user_info": {
      "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
      "name": "山田一郎",
      "age": 78,
      "gender": "男性",
      "address": {
        "prefecture": "東京都",
        "city": "新宿区"
      }
    },
    "conversation_history": {
      "callID": "CA995a950a2b9f6623a5adc987d0b31131",
      "status": "completed",
      "call_type": "scheduled",
      "duration_seconds": 342,
      "conversation": [
        {
          "speaker": "AI",
          "message": "おはようございます、山田さん。今日の体調はいかがですか？",
          "timestamp": "...",
          "emotion": "neutral"
        }
      ],
      "ai_analysis": {
        "health_status": "良好",
        "concerns": ["肩こり"],
        "recommendations": ["軽いストレッチ", "温湿布の使用"],
        "urgency_level": "low"
      }
    },
    "firestore_path": "users/4CC0CA6A-657C-4253-99FF-C19219D30AE2/calls/CA995a950a2b9f6623a5adc987d0b31131"
  }
}
```

#### `/get-user-calls` (POST)
**説明**: 指定ユーザーのすべての会話履歴を取得

**リクエスト**:
```json
{
  "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2"
}
```

**レスポンス例**:
```json
{
  "status": "success",
  "data": {
    "user_info": {
      "userID": "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
      "name": "山田一郎"
    },
    "calls_count": 2,
    "calls": [
      {
        "callID": "CA995a950a2b9f6623a5adc987d0b31131",
        "status": "completed",
        "call_type": "scheduled",
        "timestamp": "..."
      },
      {
        "callID": "CALL002",
        "status": "completed",
        "call_type": "urgent",
        "timestamp": "..."
      }
    ]
  }
}
```

## エラーハンドリング

| エラーコード | HTTPステータス | 説明 |
|-------------|---------------|------|
| USER_NOT_FOUND | 404 | 指定されたユーザーが存在しない |
| CONVERSATION_NOT_FOUND | 404 | 指定された会話履歴が存在しない |
| USER_MISMATCH | 403 | ユーザーIDと会話履歴の不整合 |
| INTERNAL_ERROR | 500 | サーバー内部エラー |

## テスト

### 1. サービスレベルテスト
```bash
python get_history/subcollection_conversation_service.py
```

### 2. APIテスト
```bash
python get_history/test_subcollection_api.py
```

### 3. curlテスト
```bash
# 単一会話履歴取得
curl -X POST http://localhost:8080/get-conversation-history-v2 \
  -H "Content-Type: application/json" \
  -d '{"userID":"4CC0CA6A-657C-4253-99FF-C19219D30AE2","callID":"CA995a950a2b9f6623a5adc987d0b31131"}'

# 全会話履歴取得
curl -X POST http://localhost:8080/get-user-calls \
  -H "Content-Type: application/json" \
  -d '{"userID":"4CC0CA6A-657C-4253-99FF-C19219D30AE2"}'
```

## 検証結果

### テスト結果サマリー
- **成功率**: 100% (6/6 テストケース)
- **カバレッジ**: 正常ケース3件、エラーケース3件
- **データ整合性**: ✅ 確認済み
- **エラーハンドリング**: ✅ 適切

### 実際のデータ確認
- **UserID**: `4CC0CA6A-657C-4253-99FF-C19219D30AE2` ✅ 存在確認
- **CallID**: `CA995a950a2b9f6623a5adc987d0b31131` ✅ 存在確認  
- **会話数**: 6件 ✅ 取得成功
- **AI分析**: ✅ 正常に構造化されたデータ
- **ユーザー情報**: ✅ 山田一郎 (78歳) の詳細情報

## 使用方法

### Python サービス経由
```python
from get_history.subcollection_conversation_service import SubcollectionConversationHistoryService

service = SubcollectionConversationHistoryService()
success, data, error = service.get_conversation_history(
    "4CC0CA6A-657C-4253-99FF-C19219D30AE2",
    "CA995a950a2b9f6623a5adc987d0b31131"
)

if success:
    print(f"ユーザー: {data['user_info']['name']}")
    print(f"会話数: {len(data['conversation_history']['conversation'])}")
```

### REST API経由
```javascript
const response = await fetch('http://localhost:8080/get-conversation-history-v2', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    userID: '4CC0CA6A-657C-4253-99FF-C19219D30AE2',
    callID: 'CA995a950a2b9f6623a5adc987d0b31131'
  })
});

const data = await response.json();
if (data.status === 'success') {
  console.log('会話履歴:', data.data.conversation_history);
}
```

## セキュリティ

- ユーザーIDと会話IDの整合性チェック実装済み
- データ取得前の認証確認
- エラー情報の適切なマスキング

## パフォーマンス

- Firestore サブコレクション活用による効率的なクエリ
- 必要最小限のデータ取得
- 適切なインデックス活用推奨

## 今後の拡張予定

- 日付範囲指定による会話履歴フィルタリング
- ページネーション対応
- 会話内容の検索機能
- リアルタイム更新通知 