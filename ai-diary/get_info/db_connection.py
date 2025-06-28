import mysql.connector
from mysql.connector import Error
import os
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    データベース接続を取得する（最小限・安定性重視）
    
    【設計方針】
    - Cloud Run環境: Unix socket接続（最小限のパラメータのみ）
    - ローカル開発環境: TCP接続（標準パラメータ）
    - db-connect-test Cloud Run Jobで実証済みの安定パターンを採用
    
    【接続パラメータ】
    - Cloud Run: unix_socket, user, password, database, autocommit=True のみ
    - 複雑な設定（charset, auth_plugin, sql_mode等）は除外してエラー回避
    - MySQLInterfaceError の msg 属性エラー対策済み
    """
    try:
        # Cloud Run環境の判定 - Cloud Run JobsやCloud Run Servicesで動作中か判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or  # Cloud Run Service
            os.environ.get('CLOUD_RUN_JOB') is not None or  # Cloud Run Job
            os.environ.get('K_CONFIGURATION') is not None  # Cloud Run (一般)
        )
        
        if is_cloud_run:
            # Cloud SQL Proxyソケット接続（最小限パラメータで安定性重視）
            unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            logger.info(f"Cloud SQL接続を使用: {unix_socket}")
            connection = mysql.connector.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME'),
                autocommit=True
            )
        else:
            # 通常のTCP接続（開発環境など）
            db_host = os.environ.get('DB_HOST', '127.0.0.1')
            logger.info(f"TCP接続を使用: {db_host}")
            connection = mysql.connector.connect(
                host=db_host,
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME'),
                autocommit=True
            )
        return connection
    except mysql.connector.Error as e:
        logger.error(f"データベース接続エラー: エラーコード={getattr(e, 'errno', 'N/A')}")
        raise
    except Exception as e:
        logger.error(f"予期しないエラー: タイプ={type(e).__name__}")
        raise

def test_connection():
    """
    データベース接続テスト（最小限・安定性重視）
    
    【設計原則】
    - db-connect-test Cloud Run Jobで実証済みの最小限パターンを採用
    - 複雑な設定パラメータを排除し、Cloud Run環境での安定性を最優先
    - エラーハンドリングは安全な方式のみを使用
    
    【接続パラメータの選択理由】
    - unix_socket: Cloud Run環境での標準的な接続方式
    - user, password, database: 基本認証情報のみ
    - autocommit=True: 明示的なコミット処理を避けて簡潔性を確保
    - その他のパラメータ（charset, auth_plugin等）は除外: 
      Cloud Run環境で予期しないエラーの原因となるため
    
    【エラーハンドリング方針】
    - mysql.connector.Error: MySQL特有のエラーのみキャッチ
    - Exception: 予期しないエラーもキャッチするが、安全な情報取得のみ
    - 例外の直接文字列変換（str(e), f"{e}"）は使用しない: 
      MySQLInterfaceErrorで'msg'属性エラーが発生するため
    - getattr(e, 'errno', 'N/A'): 安全なエラーコード取得
    - type(e).__name__: エラータイプの安全な取得
    """
    connection = None
    try:
        logger.info("=== Cloud SQL接続テスト開始（最小限）===")
        
        # Cloud Run環境の判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        if is_cloud_run:
            # Cloud SQL Proxyソケット接続（最小限のパラメータ）
            unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            logger.info(f"Unix socket: {unix_socket}")
            
            connection = mysql.connector.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME'),
                autocommit=True
            )
        else:
            logger.info("Not in Cloud Run environment")
            return False
            
        logger.info("✅ データベース接続成功!")
        
        # 簡単なクエリ実行
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        
        logger.info(f"クエリ結果: {result}")
        logger.info("=== Cloud SQL接続テスト正常終了 ===")
        return True
        
    except mysql.connector.Error as e:
        logger.error(f"データベースエラー: エラーコード={getattr(e, 'errno', 'N/A')}")
        return False
    except Exception as e:
        logger.error(f"予期しないエラー: タイプ={type(e).__name__}")
        return False
    finally:
        if connection:
            try:
                connection.close()
                logger.info("データベース接続を閉じました")
            except:
                pass 