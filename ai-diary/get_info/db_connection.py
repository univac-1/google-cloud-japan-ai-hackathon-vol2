import mysql.connector
from mysql.connector import Error
import os
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """DB接続を取得する"""
    try:
        # Cloud Run環境の判定 - Cloud Run JobsやCloud Run Servicesで動作中か判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or  # Cloud Run Service
            os.environ.get('CLOUD_RUN_JOB') is not None or  # Cloud Run Job
            os.environ.get('K_CONFIGURATION') is not None  # Cloud Run (一般)
        )
        
        if is_cloud_run:
            # Cloud SQL Proxyソケット接続（Cloud Run環境）
            unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            print(f"Cloud SQL接続を使用: {unix_socket}")
            connection = mysql.connector.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                auth_plugin='caching_sha2_password',
                autocommit=True,
                sql_mode='TRADITIONAL'
            )
        else:
            # 通常のTCP接続（開発環境など）
            db_host = os.environ.get('DB_HOST', '127.0.0.1')
            print(f"TCP接続を使用: {db_host}")
            connection = mysql.connector.connect(
                host=db_host,
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                autocommit=True,
                ssl_disabled=False,
                ssl_verify_cert=False,
                ssl_verify_identity=False,
                auth_plugin='caching_sha2_password'
            )
        return connection
    except Error as e:
        print(f"データベース接続エラー: {e}")
        raise

def test_connection():
    """DB接続テスト"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        print(f"DB接続テスト成功: {result}")
        return True
    except Exception as e:
        print(f"DB接続エラー: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close() 