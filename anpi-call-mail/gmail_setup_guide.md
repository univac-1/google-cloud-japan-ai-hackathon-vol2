# Gmail API セットアップガイド

## 1. Google Cloud Console での設定

### ステップ1: Gmail APIの有効化
1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. プロジェクトを選択（univac-aiagent）
3. **APIとサービス** → **ライブラリ** をクリック
4. 「Gmail API」を検索して選択
5. **有効にする** をクリック

### ステップ2: サービスアカウントの作成と設定
1. **IAMと管理** → **サービスアカウント** をクリック
2. **サービスアカウントを作成** をクリック
3. サービスアカウント名を入力（例: gmail-sender-sa）
4. **作成して続行** をクリック
5. 必要に応じてロールを設定（Gmail送信には特定のロールは不要）
6. **完了** をクリック

### ステップ3: サービスアカウントキーの作成
1. 作成したサービスアカウントをクリック
2. **キー** タブを選択
3. **鍵を追加** → **新しい鍵を作成** をクリック
4. **JSON** を選択して **作成** をクリック
5. ダウンロードされたJSONファイルを安全な場所に保存

### ステップ4: ドメイン全体の委任設定（G Suite/Google Workspaceの場合）
組織のGoogleアカウントから送信する場合：
1. サービスアカウントの詳細ページで **詳細を表示** をクリック
2. **ドメイン全体の委任** セクションで **G Suite ドメイン全体の委任を有効にする** をチェック
3. **保存** をクリック
4. クライアントIDをコピー

5. [Google Admin Console](https://admin.google.com) にアクセス
6. **セキュリティ** → **アクセスとデータ管理** → **APIアクセス** をクリック
7. **ドメイン全体の委任** → **新しく追加** をクリック
8. クライアントIDを入力
9. OAuth スコープに `https://www.googleapis.com/auth/gmail.send` を入力
10. **承認** をクリック

## 2. 現在のシステムでの設定方法

### 方法A: 環境変数で直接設定
```bash
# サービスアカウントキーJSONファイルの内容を環境変数に設定
export GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"..."}'
export FROM_EMAIL="あなたのGmailアドレス@gmail.com"
./setup_and_deploy.sh
```

### 方法B: .envファイルで設定
```bash
# .envファイルを編集
echo 'export GOOGLE_SERVICE_ACCOUNT_KEY='"'"'{"type":"service_account",...}'"'"'' > .env
echo 'export FROM_EMAIL="あなたのGmailアドレス@gmail.com"' >> .env
source .env
./setup_and_deploy.sh
```

### 方法C: Secret Manager を使用（推奨）
```bash
# Secret Managerにサービスアカウントキーを保存
./setup_secret_manager.sh
```

## 3. Gmail送信の制限事項

### 個人Gmailアカウントの場合
- 1日あたり最大500通の送信制限
- APIを使用した送信でも同じ制限が適用
- 大量送信が必要な場合はGoogle Workspaceの利用を検討

### Google Workspaceアカウントの場合
- 1日あたり最大10,000通まで送信可能
- ドメイン全体の委任により、組織内の任意のユーザーとして送信可能

## 4. テスト実行
```bash
# 自分宛にテストメールを送信
./test.sh "recipient@example.com" "山田" "花子" "090-1234-5678"
```

## 5. トラブルシューティング

### エラー: "insufficient authentication scopes"
- サービスアカウントに正しいスコープが設定されているか確認
- ドメイン全体の委任が正しく設定されているか確認

### エラー: "Delegation denied"
- Google Admin Consoleでドメイン全体の委任が承認されているか確認
- クライアントIDとスコープが正しく設定されているか確認

### エラー: "invalid_grant"
- サービスアカウントキーのJSONが正しいか確認
- プロジェクトIDが一致しているか確認

### その他のエラー
```bash
# Cloud Functionのログを確認
gcloud functions logs read send-mail --region=asia-northeast1
```

## 6. セキュリティベストプラクティス

1. **サービスアカウントキーを安全に管理**
   - 本番環境ではSecret Managerを使用
   - キーファイルをバージョン管理システムにコミットしない

2. **最小権限の原則**
   - 必要最小限のスコープのみを付与
   - 不要になったサービスアカウントは削除

3. **監査とログ**
   - Cloud Audit LogsでAPI使用状況を監視
   - 不審なアクティビティを定期的にチェック
