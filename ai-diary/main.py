import os

# .envファイルから環境変数を読み込み
def load_env_file():
    """
    .envファイルから環境変数を読み込む
    """
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 環境変数読み込み実行
load_env_file()

from illustration.generator import generate_illustration
from html_generator.generator import generate_html_page
from email_sender.service import process_diary_email_sending
from flask import Flask, request, jsonify
from functools import wraps
from typing import Dict, Tuple, Any, Optional
from get_info.user_service import get_user_info
from get_history.subcollection_conversation_service import SubcollectionConversationHistoryService
from create_diary_entry import DiaryGenerator

app = Flask(__name__)

# ===============================
# ヘルパー関数
# ===============================

def validate_request_data(data: Optional[Dict], required_fields: list) -> Tuple[bool, Optional[Dict]]:
    """
    リクエストデータのバリデーション
    
    Args:
        data: リクエストデータ
        required_fields: 必須フィールドのリスト
        
    Returns:
        Tuple[bool, Optional[Dict]]: (検証成功フラグ, エラーレスポンス)
    """
    if not data:
        return False, create_error_response("BAD_REQUEST", "JSONデータが必要です", 400)
    
    for field in required_fields:
        if not data.get(field):
            return False, create_error_response("BAD_REQUEST", f"{field}が必要です", 400)
    
    return True, None

def create_success_response(data: Any, message: str = None) -> Dict:
    """
    成功レスポンスの作成
    
    Args:
        data: レスポンスデータ
        message: オプションメッセージ
        
    Returns:
        Dict: 成功レスポンス
    """
    response = {
        "status": "success",
        "data": data
    }
    if message:
        response["message"] = message
    return response

def create_error_response(error_code: str, message: str, status_code: int = 500) -> Tuple[Dict, int]:
    """
    エラーレスポンスの作成
    
    Args:
        error_code: エラーコード
        message: エラーメッセージ
        status_code: HTTPステータスコード
        
    Returns:
        Tuple[Dict, int]: (エラーレスポンス, HTTPステータスコード)
    """
    return {
        "status": "error",
        "error_code": error_code,
        "message": message
    }, status_code

def get_http_status_from_error_code(error_code: str) -> int:
    """
    エラーコードに応じたHTTPステータスコードを取得
    
    Args:
        error_code: エラーコード
        
    Returns:
        int: HTTPステータスコード
    """
    status_mapping = {
        "USER_NOT_FOUND": 404,
        "CONVERSATION_NOT_FOUND": 404,
        "USER_MISMATCH": 403,
        "BAD_REQUEST": 400,
        "INTERNAL_ERROR": 500,
        "DIARY_GENERATION_ERROR": 500
    }
    return status_mapping.get(error_code, 500)

def handle_exceptions(f):
    """
    例外処理用デコレータ
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            app.logger.error(f"Unexpected error in {f.__name__}: {str(e)}")
            error_response, status_code = create_error_response(
                "INTERNAL_ERROR", 
                f"処理中にエラーが発生しました: {str(e)}"
            )
            return jsonify(error_response), status_code
    return decorated_function

# ===============================
# エンドポイント
# ===============================

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック"""
    return create_success_response({"service": "ai-diary-service"}, "healthy")

@app.route("/test-db", methods=["GET"])
def test_db_connection():
    """データベース接続テスト"""
    try:
        from get_info.db_connection import test_connection
        
        # データベース接続テスト
        result = test_connection()
        if result:
            return jsonify(create_success_response({"db_status": "connected"}, "Database connection successful"))
        else:
            return jsonify(create_error_response("DB_CONNECTION_ERROR", "Database connection failed", 500)[0]), 500
            
    except Exception as e:
        app.logger.error(f"Database test error: {str(e)}")
        return jsonify(create_error_response("DB_TEST_ERROR", f"Database test error: {str(e)}", 500)[0]), 500

@app.route("/test-db-simple", methods=["GET"])
def test_db_simple():
    """軽量なデータベース接続テスト（タイムアウト回避）"""
    try:
        import mysql.connector
        from mysql.connector import Error
        
        # Cloud Run環境判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        print(f"Environment: Cloud Run = {is_cloud_run}")
        
        if is_cloud_run:
            # Cloud SQL接続設定の確認
            instance_connection_name = os.environ.get('INSTANCE_CONNECTION_NAME')
            if instance_connection_name:
                unix_socket = f"/cloudsql/{instance_connection_name}"
            else:
                unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            
            print(f"Unix socket: {unix_socket}")
            
            # 環境変数確認
            env_check = {
                "DB_USER": os.environ.get('DB_USER', 'NOT_SET'),
                "DB_NAME": os.environ.get('DB_NAME', 'NOT_SET'),
                "DB_PASSWORD_SET": 'DB_PASSWORD' in os.environ,
                "UNIX_SOCKET": unix_socket
            }
            print(f"Environment variables: {env_check}")
            
            # 接続テスト
            try:
                # 接続パラメータを詳細ログ出力
                connection_params = {
                    'unix_socket': unix_socket,
                    'user': os.environ.get('DB_USER', 'default'),
                    'password': os.environ.get('DB_PASSWORD'),
                    'database': os.environ.get('DB_NAME', 'default'),
                    'charset': 'utf8mb4',
                    'auth_plugin': 'mysql_native_password',
                    'autocommit': True,
                    'connection_timeout': 10,
                    'sql_mode': 'TRADITIONAL'
                }
                print(f"Connection parameters: {connection_params}")
                
                # Unixソケットファイルの存在確認
                import os.path as ospath
                socket_exists = ospath.exists(unix_socket)
                print(f"Unix socket exists: {socket_exists}")
                
                # /cloudsqlディレクトリの確認
                cloudsql_dir = "/cloudsql"
                cloudsql_exists = ospath.exists(cloudsql_dir)
                if cloudsql_exists:
                    cloudsql_contents = os.listdir(cloudsql_dir)
                    print(f"CloudSQL directory contents: {cloudsql_contents}")
                else:
                    print("CloudSQL directory does not exist")
                
                connection = mysql.connector.connect(**connection_params)
                
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                
                return jsonify({
                    "status": "success",
                    "message": "Cloud Run DB connection successful",
                    "environment": env_check,
                    "result": result[0] if result else None
                })
                
            except Error as e:
                error_msg = f"MySQL Error: {e}"
                print(error_msg)
                print(f"Error type: {type(e)}")
                print(f"Error dir: {dir(e)}")
                return jsonify({
                    "status": "error",
                    "message": error_msg,
                    "error_type": str(type(e)),
                    "error_attrs": [attr for attr in dir(e) if not attr.startswith('_')],
                    "environment": env_check
                }), 500
                
        else:
            return jsonify({
                "status": "info", 
                "message": "Not in Cloud Run environment"
            })
            
    except Exception as e:
        import traceback
        error_msg = f"General error: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"{error_msg}\n{traceback_str}")
        return jsonify({
            "status": "error",
            "message": error_msg,
            "traceback": traceback_str
        }), 500

@app.route("/test-db-pymysql", methods=["GET"])
def test_db_pymysql():
    """PyMySQLでのデータベース接続テスト"""
    try:
        import pymysql
        
        # Cloud Run環境判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        print(f"PyMySQL Environment: Cloud Run = {is_cloud_run}")
        
        if is_cloud_run:
            # Cloud SQL接続設定の確認
            instance_connection_name = os.environ.get('INSTANCE_CONNECTION_NAME')
            if instance_connection_name:
                unix_socket = f"/cloudsql/{instance_connection_name}"
            else:
                unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            
            print(f"PyMySQL Unix socket: {unix_socket}")
            
            env_check = {
                "DB_USER": os.environ.get('DB_USER', 'NOT_SET'),
                "DB_NAME": os.environ.get('DB_NAME', 'NOT_SET'),
                "DB_PASSWORD_SET": 'DB_PASSWORD' in os.environ,
                "UNIX_SOCKET": unix_socket
            }
            print(f"PyMySQL Environment variables: {env_check}")
            
            try:
                connection = pymysql.connect(
                    unix_socket=unix_socket,
                    user=os.environ.get('DB_USER', 'default'),
                    password=os.environ.get('DB_PASSWORD'),
                    database=os.environ.get('DB_NAME', 'default'),
                    charset='utf8mb4',
                    autocommit=True,
                    connect_timeout=10
                )
                
                cursor = connection.cursor(pymysql.cursors.DictCursor)
                cursor.execute("SELECT 1 as test")
                result = cursor.fetchone()
                cursor.close()
                connection.close()
                
                return jsonify({
                    "status": "success",
                    "message": "PyMySQL Cloud Run DB connection successful",
                    "environment": env_check,
                    "result": result
                })
                
            except Exception as e:
                error_msg = f"PyMySQL Error: {e}"
                print(error_msg)
                import traceback
                traceback_str = traceback.format_exc()
                print(f"PyMySQL Traceback: {traceback_str}")
                return jsonify({
                    "status": "error",
                    "message": error_msg,
                    "traceback": traceback_str,
                    "environment": env_check
                }), 500
                
        else:
            return jsonify({
                "status": "info", 
                "message": "Not in Cloud Run environment"
            })
            
    except ImportError as e:
        return jsonify({
            "status": "error",
            "message": f"PyMySQL not available: {e}"
        }), 500
    except Exception as e:
        import traceback
        error_msg = f"General PyMySQL error: {str(e)}"
        traceback_str = traceback.format_exc()
        print(f"{error_msg}\n{traceback_str}")
        return jsonify({
            "status": "error",
            "message": error_msg,
            "traceback": traceback_str
        }), 500

@app.route("/generate-diary", methods=["POST"])
@handle_exceptions
def generate_diary_endpoint():
    """
    完全な日記生成API
    ユーザー情報取得→会話履歴取得→日記生成→挿絵作成→HTML生成の一連の処理を実行
    
    Request Body:
    {
        "userID": "string",
        "callID": "string"
    }
    
    Response:
    {
        "status": "success",
        "data": {
            "userID": "string",
            "callID": "string", 
            "userInfo": {...},
            "conversationHistory": {...},
            "diary": "string",
            "illustrationUrl": "string" or null,
            "htmlContent": "string" or null
        },
        "message": "string"
    }
    """
    data = request.get_json()
    
    # リクエストデータの検証
    is_valid, error_response = validate_request_data(data, ["userID", "callID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    call_id = data["callID"]
    
    try:
        # Step 1: ユーザー情報取得
        user_info = get_user_info(user_id)
        if not user_info:
            error_response, status_code = create_error_response(
                "USER_NOT_FOUND", 
                "ユーザーが見つかりませんでした"
            )
            return jsonify(error_response), status_code
        
        # Step 2: 会話履歴取得
        service = SubcollectionConversationHistoryService()
        success, conversation_data, error_code = service.get_conversation_history(user_id, call_id)
        
        if not success:
            status_code = get_http_status_from_error_code(error_code)
            error_response, _ = create_error_response(error_code, "会話履歴の取得に失敗しました")
            return jsonify(error_response), status_code
        
        # Step 3: 日記生成
        try:
            generator = DiaryGenerator()
            diary_success, diary_text, diary_error = generator.generate_diary_entry(
                user_info, conversation_data
            )
            
            if not diary_success:
                error_response, status_code = create_error_response(
                    "DIARY_GENERATION_ERROR", 
                    f"日記生成に失敗しました: {diary_error}"
                )
                return jsonify(error_response), status_code
            
            # Step 4: 挿絵作成
            illustration_url = None
            try:
                # ユーザー情報から性別を取得（デフォルトは'unknown'）
                gender = user_info.get('gender', 'unknown')
                illustration_url = generate_illustration(diary_text, user_id, gender, call_id)
                app.logger.info(f"Illustration generated successfully: {illustration_url}")
            except Exception as illustration_error:
                # 挿絵生成エラーは警告ログに記録するが、処理は継続
                app.logger.warning(f"Illustration generation failed: {str(illustration_error)}")
                illustration_url = None
            
            # Step 5: HTML生成
            html_content = None
            try:
                html_content = generate_html_page(diary_text, user_id, call_id)
                if html_content:
                    app.logger.info("HTML page generated successfully")
                else:
                    app.logger.warning("HTML generation returned empty content")
            except Exception as html_error:
                # HTML生成エラーは警告ログに記録するが、処理は継続
                app.logger.warning(f"HTML generation failed: {str(html_error)}")
                html_content = None
            
            # Step 6: メール送信
            email_sent, email_message = process_diary_email_sending(
                user_info=user_info,
                html_content=html_content,
                user_id=user_id
            )
            
            # 成功レスポンス
            response_data = {
                "userID": user_id,
                "callID": call_id,
                "userInfo": user_info,
                "conversationHistory": conversation_data,
                "diary": diary_text,
                "illustrationUrl": illustration_url,
                "htmlContent": html_content,
                "emailSent": email_sent,
                "emailMessage": email_message
            }
            
            return jsonify(create_success_response(
                response_data, 
                "ユーザー情報取得→会話履歴取得→日記生成→挿絵作成→HTML生成→メール送信の処理が完了しました"
            ))
            
        except ValueError as e:
            error_response, status_code = create_error_response(
                "GEMINI_API_KEY_ERROR", 
                f"Gemini APIキーが設定されていません: {str(e)}"
            )
            return jsonify(error_response), status_code
            
    except Exception as e:
        app.logger.error(f"Diary generation error: {str(e)}")
        error_response, status_code = create_error_response(
            "INTERNAL_ERROR", 
            f"日記生成処理中にエラーが発生しました: {str(e)}"
        )
        return jsonify(error_response), status_code

@app.route("/debug-env", methods=["GET"])
def debug_env():
    """環境変数確認エンドポイント"""
    env_info = {
        "K_SERVICE": os.environ.get('K_SERVICE'),
        "GOOGLE_CLOUD_PROJECT": os.environ.get('GOOGLE_CLOUD_PROJECT'),
        "INSTANCE_CONNECTION_NAME": os.environ.get('INSTANCE_CONNECTION_NAME'),
        "DB_USER": os.environ.get('DB_USER'),
        "DB_NAME": os.environ.get('DB_NAME'),
        "has_DEFAULT_PASSWORD": 'DEFAULT_PASSWORD' in os.environ,
        "has_DB_PASSWORD": 'DB_PASSWORD' in os.environ,
        "has_DB_PASS": 'DB_PASS' in os.environ,
    }
    return jsonify({"status": "success", "env": env_info})

@app.route("/test-db-debug", methods=["GET"])
def test_db_debug():
    """詳細なデータベース接続デバッグ"""
    try:
        import mysql.connector
        from mysql.connector import Error
        import os
        
        # 環境変数の確認
        debug_info = {
            "environment_variables": {
                "K_SERVICE": os.environ.get('K_SERVICE'),
                "CLOUD_RUN_JOB": os.environ.get('CLOUD_RUN_JOB'),
                "K_CONFIGURATION": os.environ.get('K_CONFIGURATION'),
                "GOOGLE_CLOUD_PROJECT": os.environ.get('GOOGLE_CLOUD_PROJECT'),
                "DB_HOST": os.environ.get('DB_HOST'),
                "DB_PORT": os.environ.get('DB_PORT'),
                "DB_USER": os.environ.get('DB_USER'),
                "DB_NAME": os.environ.get('DB_NAME'),
                "TZ": os.environ.get('TZ')
            }
        }
        
        # Cloud Run環境判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or
            os.environ.get('CLOUD_RUN_JOB') is not None or
            os.environ.get('K_CONFIGURATION') is not None
        )
        
        debug_info["is_cloud_run"] = is_cloud_run
        
        if is_cloud_run:
            # Cloud SQL Proxyソケット接続（Cloud Run環境）
            unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            debug_info["connection_method"] = "unix_socket"
            debug_info["unix_socket"] = unix_socket
            
            try:
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
                debug_info["connection_status"] = "success"
                
                # 簡単なクエリ実行
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT 1 as test, NOW() as current_time")
                result = cursor.fetchone()
                debug_info["query_result"] = result
                
                cursor.close()
                connection.close()
                
            except Exception as e:
                debug_info["connection_status"] = "failed"
                debug_info["error_type"] = type(e).__name__
                debug_info["error_message"] = str(e)
                
                # MySQLエラーの詳細情報を安全に取得
                error_details = {}
                for attr in ['errno', 'sqlstate', 'msg']:
                    try:
                        error_details[attr] = getattr(e, attr, None)
                    except:
                        error_details[attr] = f"Cannot access {attr}"
                        
                debug_info["error_details"] = error_details
                
                # mysql.connector.Errorの場合の追加詳細
                if hasattr(e, 'args'):
                    debug_info["error_args"] = str(e.args)
        else:
            debug_info["connection_method"] = "tcp"
            debug_info["message"] = "Not in Cloud Run environment"
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            "error": f"Debug test failed: {type(e).__name__}: {str(e)}"
        }), 500

@app.route("/test-db-connector", methods=["GET"])
def test_db_connector():
    """Cloud SQL Python Connectorを使用したDB接続テスト"""
    try:
        from get_info.db_connection_connector import test_connection_with_connector
        
        # データベース接続テスト
        result = test_connection_with_connector()
        if result:
            return jsonify(create_success_response({"db_status": "connected", "method": "cloud-sql-connector"}, "Database connection successful with Cloud SQL Python Connector"))
        else:
            return jsonify(create_error_response("DB_CONNECTION_ERROR", "Database connection failed with Cloud SQL Python Connector", 500)[0]), 500
            
    except Exception as e:
        app.logger.error(f"Cloud SQL Connector test error: {str(e)}")
        return jsonify(create_error_response("DB_CONNECTOR_TEST_ERROR", f"Cloud SQL Connector test error: {str(e)}", 500)[0]), 500

if __name__ == "__main__":
    print("AI Diary Service starting...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
