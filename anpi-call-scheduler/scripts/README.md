# Scripts

開発・テスト・デバッグ用のユーティリティスクリプト集

## データベース関連

### test_db_connection.py
データベース接続テスト用スクリプト。Cloud SQL ProxyまたはTCP接続でデータベースへの接続を確認し、テーブル構造やデータを表示します。

```bash
python scripts/test_db_connection.py
```

### check_db_schema.py
データベーススキーマの確認と現在時刻に近いテストデータの追加を行います。

```bash
python scripts/check_db_schema.py
```

### add_test_data.sql
データベースに直接テストデータを追加するためのSQLスクリプト。現在時刻に近い土曜日設定のテストユーザーを追加します。

```bash
# Cloud SQL Proxyを使用してSQLファイルを実行
mysql -h 127.0.0.1 -P 3306 -u default -p default < scripts/add_test_data.sql
```

## テストデータ関連

### add_test_data.py
基本的なテストユーザーデータを追加します。

```bash
python scripts/add_test_data.py
```

### add_current_time_test_data.py
現在時刻に近い通話設定を持つテストユーザーを追加します。即時実行テストに最適です。

```bash
python scripts/add_current_time_test_data.py
```

### add_bulk_test_data.py
5分間隔で大量のテストデータを追加します。負荷テストやスケジューラーテストに使用します。

```bash
python scripts/add_bulk_test_data.py
```

## デバッグ関連

### debug_immediate_execution.py
即時実行機能の詳細なデバッグを行います。時刻判定ロジックや関数の動作を確認できます。

```bash
python scripts/debug_immediate_execution.py
```

## ツール

### cloud-sql-proxy
Cloud SQL Proxyバイナリ。ローカル開発環境でCloud SQLに接続する際に使用します。

```bash
# Cloud SQL Proxyの起動例
./scripts/cloud-sql-proxy --port 3306 univac-aiagent:asia-northeast1:cloudsql-01
```

## 使用方法

1. **データベース接続の確認**
   ```bash
   python scripts/test_db_connection.py
   ```

2. **テストデータの追加**
   ```bash
   python scripts/add_current_time_test_data.py
   ```

3. **即時実行のデバッグ**
   ```bash
   python scripts/debug_immediate_execution.py
   ```

4. **システムテスト用の大量データ追加**
   ```bash
   python scripts/add_bulk_test_data.py
   ```

## 注意事項

- これらのスクリプトは開発・テスト専用です
- 本番環境での使用は推奨されません
- データベース接続情報はハードコーディングされているため、適切な環境で実行してください
- テストデータは定期的にクリーンアップしてください
