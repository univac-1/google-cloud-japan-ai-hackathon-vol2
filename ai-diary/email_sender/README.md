# Email Sender Module

このモジュールは、AI日記完成後のメール送信処理を担当します。

## 機能

- 日記完成通知メールの送信
- HTMLコンテンツの配信
- エラーハンドリングとログ出力

## 使用方法

```python
from email_sender.service import process_diary_email_sending

# メール送信処理
email_sent, email_message = process_diary_email_sending(
    user_info=user_info,
    html_content=html_content,
    user_id=user_id
)
```

## API

### `process_diary_email_sending(user_info, html_content, user_id)`

日記完成メール送信の統合処理

**引数:**
- `user_info` (dict): ユーザー情報
- `html_content` (str): 送信するHTMLコンテンツ
- `user_id` (str): ユーザーID

**戻り値:**
- `Tuple[bool, str]`: (送信成功フラグ, メッセージ)

### `send_diary_email(to_email, subject, content)`

メール送信の低レベル処理

**引数:**
- `to_email` (str): 送信先メールアドレス
- `subject` (str): 件名
- `content` (str): HTMLコンテンツ

**戻り値:**
- `Tuple[bool, str]`: (成功フラグ, メッセージまたはエラー)
