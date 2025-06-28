# DB接続テスト - Cloud Run Jobs 検証結果

## 概要
`anpi-call-db`で構築したCloud SQL(MySQL)に対して、Cloud Run JobsからPythonスクリプトで接続できるかの検証を実施しました。

## プロジェクト構成

### ファイル構成
```
db-connect-test/
├── main.py              # Flask API版 (参考用)
├── job_main.py           # Cloud Run Jobs用メインスクリプト
├── requirements.txt     # Python依存関係
├── Dockerfile           # Cloud Run Jobs用Dockerコンテナ定義
├── job.yaml             # Cloud Run Job設定
└── README.md            # この検証結果ドキュメント
```

### 技術スタック
- **言語**: Python 3.12
- **データベース**: Cloud SQL (MySQL 8.0)
- **接続ライブラリ**: mysql-connector-python 9.3.0
- **実行環境**: Cloud Run Jobs (Container)
- **認証**: Google Cloud IAM（サービスアカウント）

## 実装内容

### DB接続ロジック
- `anpi-call-scheduler`と同一の方式を採用
- Cloud Run環境ではUnix Socket接続（`/cloudsql/...`）
- ローカル環境ではTCP接続をサポート

### エラーハンドリング
- `mysql.connector.Error`基底クラスでのキャッチ
- 詳細なログ出力による問題の特定と解決

### 環境設定
```yaml
環境変数:
  GOOGLE_CLOUD_PROJECT: univac-aiagent
  DB_HOST: localhost
  DB_PORT: 3306
  DB_USER: default
  DB_PASSWORD: [暗号化済み]
  DB_NAME: default
  USE_CLOUD_SQL: true
  LOG_LEVEL: debug

Cloud SQL設定:
  Instance: univac-aiagent:asia-northeast1:cloudsql-01
  Database: default
  Connection: Unix Socket (/cloudsql/...)
```

## 検証結果

### ✅ 成功実績
- **実行日時**: 2025-06-28 14:12:24 UTC, 14:14:06 UTC
- **実行ID**: db-connect-test-job-gddc6, db-connect-test-job-47r8f
- **ステータス**: ✔ 成功 (2回連続)
- **実行時間**: 約18秒/回

### 実行内容
1. Cloud Run環境の自動検出
2. Cloud SQL Proxyソケット経由での接続
3. MySQL バージョン確認
4. 現在時刻取得
5. `users`テーブルの存在確認
6. レコード数の取得

### テスト項目
- [x] Cloud Run Jobs環境でのコンテナ起動
- [x] Cloud SQLインスタンスへの接続
- [x] Unix Socket経由でのMySQL接続
- [x] 基本的なSQLクエリの実行
- [x] 適切なログ出力
- [x] 正常終了（exit(0)）

## トラブルシューティング履歴

### 問題1: MySQLInterfaceError
**症状**: AttributeError: 'MySQLInterfaceError' object has no attribute 'msg'  
**原因**: 過度に詳細なエラーハンドリングでの属性アクセスエラー  
**解決**: `mysql.connector.Error`基底クラスでのシンプルな例外処理に変更

### 問題2: エラーハンドリングの複雑化
**症状**: エラー属性アクセス時の二次的エラー  
**原因**: `MySQLInterfaceError`オブジェクトの属性構造の誤解  
**解決**: anpi-call-schedulerの実装パターンに合わせて簡素化

## デプロイ手順

### 1. イメージビルド
```bash
cd db-connect-test
gcloud builds submit . --tag gcr.io/univac-aiagent/db-connect-test:latest
```

### 2. Cloud Run Job作成・更新
```bash
gcloud run jobs replace job.yaml --region=asia-northeast1
```

### 3. 実行
```bash
gcloud run jobs execute db-connect-test-job --region=asia-northeast1 --wait
```

### 4. ログ確認
```bash
gcloud run jobs executions list --job=db-connect-test-job --region=asia-northeast1
```

## 学習・改善ポイント

### 成功要因
1. **実績のあるパターンの踏襲**: anpi-call-schedulerと同一の接続方式を採用
2. **段階的なデバッグ**: エラーハンドリングを段階的に簡素化
3. **環境設定の一致**: 成功している他サービスと同じ設定値を使用

### 改善項目
1. **ログの可視性**: Cloud Loggingでのアプリケーションログ確認方法の改善
2. **エラーハンドリング**: 最初からシンプルな例外処理パターンの適用
3. **テストデータ**: 実際のusersテーブルでのCRUD操作テストの追加

## 次のステップ

1. **本格運用**: 実際の業務ロジックでの接続テスト
2. **性能測定**: 大量データ処理時のパフォーマンス測定
3. **監視設定**: Cloud Monitoringでの接続エラー監視設定
4. **自動化**: CI/CDパイプラインでの自動テスト組み込み

## 結論

✅ **Cloud Run JobsからCloud SQL(MySQL)への接続が正常に動作することを確認**

anpi-call-schedulerで実績のある接続方式を採用することで、安定したDB接続を実現できました。今後の類似プロジェクトでは、このパターンを標準として採用することを推奨します。
