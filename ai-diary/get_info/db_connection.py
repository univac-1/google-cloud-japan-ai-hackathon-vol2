import mysql.connector
from mysql.connector import Error
import os
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """データベース接続を取得する"""
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
            logger.info(f"Cloud SQL接続を使用: {unix_socket}")
            connection = mysql.connector.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                auth_plugin='mysql_native_password',
                autocommit=True,
                sql_mode='TRADITIONAL'
            )
        else:
            # 通常のTCP接続（開発環境など）
            db_host = os.environ.get('DB_HOST', '127.0.0.1')
            logger.info(f"TCP接続を使用: {db_host}")
            connection = mysql.connector.connect(
                host=db_host,
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                auth_plugin='mysql_native_password',
                autocommit=True
            )
        return connection
    except Exception as e:
        logger.error(f"データベース接続エラー: {type(e).__name__}: {str(e)}")
        raise

def test_connection():
    """DB接続テスト"""
    conn = None
    cursor = None
    try:
        logger.info("DB接続テスト開始")
        conn = get_db_connection()
        logger.info("DB接続成功、カーソル作成中")
        cursor = conn.cursor(dictionary=True)
        logger.info("SELECT 1クエリ実行中")
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        logger.info(f"DB接続テスト成功: {result}")
        return True
    except Exception as e:
        # エラーログ出力を単純化
        try:
            logger.error(f"DB接続エラー: {type(e).__name__}")
            logger.error(f"エラー詳細: {str(e)}")
        except:
            logger.error("DB接続エラー（詳細不明）")
        return False
    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
        except Exception as close_error:
            try:
                logger.error(f"接続クローズエラー: {type(close_error).__name__}")
            except:
                logger.error("接続クローズエラー（詳細不明）") 