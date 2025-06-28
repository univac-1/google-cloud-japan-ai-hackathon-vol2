#!/usr/bin/env python3
"""
Cloud SQL接続テスト専用サービス
anpi-call-dbで構築したCloud SQLとの接続確認を行う
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """データベース接続を取得する（anpi-call-schedulerと同一の方式）"""
    try:
        # Cloud Run環境の判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
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
    except Error as e:
        logger.error(f"データベース接続エラー: {e}")
        raise

def test_db_connection():
    """データベース接続テスト"""
    conn = None
    cursor = None
    try:
        logger.info("DB接続テスト開始")
        conn = get_db_connection()
        logger.info("DB接続成功、カーソル作成中")
        cursor = conn.cursor(dictionary=True)
        
        # 基本的なクエリテスト
        logger.info("SELECT 1クエリ実行中")
        cursor.execute("SELECT 1 as test, NOW() as current_time, VERSION() as version")
        result = cursor.fetchone()
        logger.info(f"基本クエリ成功: {result}")
        
        # usersテーブルの存在確認
        logger.info("usersテーブル存在確認中")
        cursor.execute("SHOW TABLES LIKE 'users'")
        table_exists = cursor.fetchone()
        logger.info(f"usersテーブル存在: {table_exists is not None}")
        
        # usersテーブルの件数確認（存在する場合）
        user_count = 0
        if table_exists:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            count_result = cursor.fetchone()
            user_count = count_result['count']
            logger.info(f"usersテーブル件数: {user_count}")
        
        return {
            'status': 'success',
            'basic_query': result,
            'users_table_exists': table_exists is not None,
            'users_count': user_count,
            'test_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"DB接続テストエラー: {type(e).__name__}: {str(e)}")
        return {
            'status': 'error',
            'error_type': type(e).__name__,
            'error_message': str(e),
            'test_time': datetime.now().isoformat()
        }
    finally:
        try:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()
                logger.info("DB接続クローズ完了")
        except Exception as close_error:
            logger.error(f"接続クローズエラー: {close_error}")

@app.route("/", methods=["GET"])
def home():
    """ホームエンドポイント"""
    return jsonify({
        "service": "db-connect-test",
        "description": "Cloud SQL接続テスト専用サービス",
        "endpoints": {
            "/health": "ヘルスチェック",
            "/test-db": "データベース接続テスト",
            "/test-db-details": "詳細なデータベース接続テスト",
            "/env-info": "環境変数情報"
        }
    })

@app.route("/health", methods=["GET"])
def health():
    """ヘルスチェック"""
    return jsonify({
        "status": "healthy",
        "service": "db-connect-test",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test-db", methods=["GET"])
def test_db():
    """シンプルなデータベース接続テスト"""
    result = test_db_connection()
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

@app.route("/test-db-details", methods=["GET"])
def test_db_details():
    """詳細なデータベース接続テスト"""
    try:
        # 環境情報の収集
        env_info = {
            "GOOGLE_CLOUD_PROJECT": os.environ.get('GOOGLE_CLOUD_PROJECT'),
            "DB_HOST": os.environ.get('DB_HOST'),
            "DB_PORT": os.environ.get('DB_PORT'),
            "DB_USER": os.environ.get('DB_USER'),
            "DB_NAME": os.environ.get('DB_NAME'),
            "K_SERVICE": os.environ.get('K_SERVICE'),
            "K_CONFIGURATION": os.environ.get('K_CONFIGURATION'),
            "CLOUD_RUN_JOB": os.environ.get('CLOUD_RUN_JOB'),
            "TZ": os.environ.get('TZ')
        }
        
        # Cloud Run環境判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        # DB接続テスト実行
        db_test_result = test_db_connection()
        
        return jsonify({
            "environment_info": env_info,
            "is_cloud_run": is_cloud_run,
            "unix_socket_path": f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01" if is_cloud_run else None,
            "connection_method": "unix_socket" if is_cloud_run else "tcp",
            "db_test_result": db_test_result,
            "test_timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"詳細テストエラー: {e}")
        return jsonify({
            "error": f"詳細テストエラー: {type(e).__name__}: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/env-info", methods=["GET"])
def env_info():
    """環境変数情報の表示"""
    return jsonify({
        "environment_variables": {
            "GOOGLE_CLOUD_PROJECT": os.environ.get('GOOGLE_CLOUD_PROJECT'),
            "DB_HOST": os.environ.get('DB_HOST'),
            "DB_PORT": os.environ.get('DB_PORT'),
            "DB_USER": os.environ.get('DB_USER'),
            "DB_NAME": os.environ.get('DB_NAME'),
            "K_SERVICE": os.environ.get('K_SERVICE'),
            "K_CONFIGURATION": os.environ.get('K_CONFIGURATION'),
            "CLOUD_RUN_JOB": os.environ.get('CLOUD_RUN_JOB'),
            "TZ": os.environ.get('TZ')
        },
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
