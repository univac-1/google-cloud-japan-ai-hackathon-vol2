# AI Diary サービス ローカル実行手順書

## 🚨 重要: データベース接続が必要な作業の前に必読

このドキュメントは、AI Diary サービスをローカルでテスト・実行する際の **必須手順** をまとめています。

## 📋 前提条件チェックリスト

- [ ] Google Cloud認証済み (`gcloud auth list` で確認)
- [ ] Cloud SQL Proxyインストール済み (`which cloud_sql_proxy` で確認)
- [ ] Python仮想環境作成済み (`venv/` フォルダが存在)
- [ ] 依存関係インストール済み (`pip install -r requirements.txt`)

## 🔄 毎回実行が必要な手順

### 1. Cloud SQL Proxy の起動（データベース接続必須）

**ターミナル1（常時実行）:**
```bash
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary

# 方法A: ヘルパースクリプト使用（推奨）
./start_cloud_sql_proxy.sh

# 方法B: 手動実行
cloud_sql_proxy --instances=univac-aiagent:asia-northeast1:cloudsql-01=tcp:3306
```

**✅ 成功の確認:**
- `Ready for new connections` メッセージが表示
- ターミナルがブロックされた状態（正常）

### 2. 接続状況の確認

**ターミナル2:**
```bash
cd /home/yasami/google-cloud-japan-ai-hackathon-vol2/ai-diary

# 接続状況の総合チェック
./check_db_connection.sh
```

**✅ 成功の確認:**
- すべての項目で ✅ が表示される

### 3. APIテストまたはサービス起動

**ターミナル2（続き）:**
```bash
# 指定パラメータでの完全テスト
./test_specified_params.sh

# または、サービス起動
./start_service.sh
```

## 🔧 トラブルシューティング

### エラー: "MySQL server connection error"
```
❌ 原因: Cloud SQL Proxyが起動していない
✅ 解決: 手順1を実行してCloud SQL Proxyを起動
```

### エラー: "Cloud SQL Proxyが起動していません"
```
❌ 原因: Cloud SQL Proxyプロセスが検出されない
✅ 解決: 
   1. ターミナル1でCloud SQL Proxyが動作中か確認
   2. エラーメッセージがないか確認
   3. 必要に応じて再起動
```

### エラー: "GEMINI_API_KEY environment variable is required"
```
❌ 原因: Gemini APIキーが設定されていない
✅ 解決: .envファイルにAPIキーが正しく設定されているか確認
```

## 📚 スクリプト一覧と用途

| スクリプト名 | 用途 | DB接続要 | 備考 |
|-------------|------|---------|------|
| `start_cloud_sql_proxy.sh` | Cloud SQL Proxy起動 | - | 常時実行、他の作業の前提 |
| `check_db_connection.sh` | 接続状況確認 | ✅ | トラブルシューティング用 |
| `test_specified_params.sh` | 指定パラメータでのテスト | ✅ | 完全な機能テスト |
| `start_service.sh` | APIサーバー起動 | ✅ | 本番相当の動作確認 |
| `test_gemini_api.sh` | Gemini API単体テスト | ❌ | DB接続不要 |

## 🎯 推奨ワークフロー

```bash
# 1. Cloud SQL Proxy起動（ターミナル1）
./start_cloud_sql_proxy.sh

# 2. 接続確認（ターミナル2）
./check_db_connection.sh

# 3. 完全テスト（ターミナル2）
./test_specified_params.sh

# 4. 開発継続時
#    - ターミナル1は起動したまま
#    - ターミナル2で各種テスト/サービス起動
```

## ⚠️ 注意事項

1. **Cloud SQL Proxy は前台実行**: ターミナルを閉じると停止します
2. **複数ターミナル必要**: Proxy用とテスト/開発用で最低2つ
3. **セッション継続**: 複数のテストを行う場合、Proxyは起動したまま
4. **認証期限**: 長時間使用時は `gcloud auth list` で認証状況確認

## 🔄 次回以降の実行時

このドキュメントまたはREADMEの「前提条件」セクションを確認してから作業を開始してください。
