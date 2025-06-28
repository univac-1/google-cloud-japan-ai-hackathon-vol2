import os
import logging
from typing import Optional
import pymysql
from google.cloud.sql.connector import Connector

logger = logging.getLogger(__name__)

def get_db_connection_with_connector():
    """Cloud SQL Python Connectorを使用したDB接続"""
    try:
        # Cloud Run環境判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        if is_cloud_run:
            # Cloud SQL Python Connectorを使用
            logger.info("Cloud SQL Python Connectorを使用した接続")
            
            connector = Connector()
            
            def getconn():
                conn = connector.connect(
                    "univac-aiagent:asia-northeast1:cloudsql-01",
                    "pymysql",
                    user=os.environ.get('DB_USER', 'default'),
                    password=os.environ.get('DB_PASSWORD'),
                    db=os.environ.get('DB_NAME', 'default'),
                    charset='utf8mb4',
                    autocommit=True
                )
                return conn
            
            return getconn()
        else:
            # 通常のPyMySQL接続（開発環境）
            logger.info("PyMySQL直接接続を使用")
            connection = pymysql.connect(
                host=os.environ.get('DB_HOST', '127.0.0.1'),
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                autocommit=True
            )
            return connection
            
    except Exception as e:
        logger.error(f"DB接続エラー (Cloud SQL Connector): {type(e).__name__}: {str(e)}")
        raise

def test_connection_with_connector():
    """Cloud SQL Python Connectorを使用したDB接続テスト"""
    conn = None
    cursor = None
    try:
        logger.info("DB接続テスト開始 (Cloud SQL Connector)")
        conn = get_db_connection_with_connector()
        logger.info("DB接続成功、カーソル作成中")
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        logger.info("SELECT 1クエリ実行中")
        cursor.execute("SELECT 1 as test, NOW() as current_time")
        result = cursor.fetchone()
        logger.info(f"DB接続テスト成功: {result}")
        return True
    except Exception as e:
        logger.error(f"DB接続エラー: {type(e).__name__}: {str(e)}")
        return False
    finally:
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception as close_error:
            logger.error(f"接続クローズエラー: {type(close_error).__name__}: {str(close_error)}")
