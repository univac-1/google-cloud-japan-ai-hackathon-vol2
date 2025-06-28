import pymysql
import os
import logging

logger = logging.getLogger(__name__)

def get_db_connection_pymysql():
    """PyMySQLを使用してDB接続を取得する"""
    try:
        # Cloud Run環境の判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        if is_cloud_run:
            # Cloud SQL Proxyソケット接続（Cloud Run環境）
            instance_connection_name = os.environ.get('INSTANCE_CONNECTION_NAME')
            if instance_connection_name:
                unix_socket = f"/cloudsql/{instance_connection_name}"
            else:
                unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            
            print(f"PyMySQL Cloud SQL接続を使用: {unix_socket}")
            
            password = os.environ.get('DB_PASS') or os.environ.get('DB_PASSWORD')
            print(f"PyMySQL DB設定: user={os.environ.get('DB_USER', 'default')}, database={os.environ.get('DB_NAME', 'default')}, password_set={password is not None}")
            
            connection = pymysql.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER', 'default'),
                password=password,
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=10
            )
        else:
            # 通常のTCP接続（開発環境など）
            db_host = os.environ.get('DB_HOST', '127.0.0.1')
            password = os.environ.get('DB_PASS') or os.environ.get('DB_PASSWORD')
            print(f"PyMySQL TCP接続を使用: {db_host}")
            print(f"PyMySQL DB設定: user={os.environ.get('DB_USER', 'default')}, database={os.environ.get('DB_NAME', 'default')}, password_set={password is not None}")
            
            connection = pymysql.connect(
                host=db_host,
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER', 'default'),
                password=password,
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                autocommit=True,
                connect_timeout=10
            )
        return connection
    except Exception as e:
        print(f"PyMySQL データベース接続エラー: {e}")
        print(f"PyMySQL エラータイプ: {type(e)}")
        import traceback
        print(f"PyMySQL トレースバック:\n{traceback.format_exc()}")
        raise

def test_connection_pymysql():
    """PyMySQLでDB接続テスト"""
    try:
        conn = get_db_connection_pymysql()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"PyMySQL DB接続テスト成功: {result}")
        return True
    except Exception as e:
        print(f"PyMySQL DB接続エラー: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()
