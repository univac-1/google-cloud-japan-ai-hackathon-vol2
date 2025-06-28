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
from html_generator.generator import generate_html_page, test_html_generation
from flask import Flask, request, jsonify
from functools import wraps
from typing import Dict, Tuple, Any, Optional
from get_info.user_service import get_user_info
from get_info.db_connection import test_connection
from get_history.conversation_service import get_conversation_history
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

@app.route("/")
def hello_world():
    """Example endpoint."""
    name = os.environ.get("NAME", "World")
    app.logger.info("test")
    return f"Hello, {name}!"

@app.route("/test-gen")
def test_generate_illustration():
    # テスト用パラメータ
    diary_text = "今日は孫と凧揚げをしました。空高く飛んで、とても楽しかったです。"
    user_id = "test-user-1234"
    call_id = "call-5678"
    gender = "female"

    # 関数を呼び出し
    try:
        image_url = generate_illustration(diary_text, user_id, gender, call_id)
        print("✅ 画像生成成功！")
        print("画像URL:", image_url)

        return f"画像生成処理終了： {image_url}"
    except Exception as e:
        print("❌ エラーが発生しました:", str(e))

        return "Error"


@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック"""
    return create_success_response({"service": "ai-diary-get-info"}, "healthy")

@app.route("/test-db", methods=["GET"])
def test_db():
    """DB接続テスト"""
    if test_connection():
        return create_success_response(None, "DB接続成功")
    else:
        error_response, status_code = create_error_response("DB_CONNECTION_ERROR", "DB接続失敗")
        return jsonify(error_response), status_code

@app.route("/test-gemini", methods=["GET"])
@handle_exceptions
def test_gemini():
    """Gemini API接続テスト"""
    try:
        generator = DiaryGenerator()
        if generator.test_generation():
            return create_success_response(None, "Gemini API接続成功")
        else:
            error_response, status_code = create_error_response(
                "GEMINI_CONNECTION_ERROR", 
                "Gemini API接続失敗"
            )
            return jsonify(error_response), status_code
    except ValueError as e:
        error_response, status_code = create_error_response(
            "GEMINI_API_KEY_ERROR", 
            f"Gemini APIキー設定エラー: {str(e)}"
        )
        return jsonify(error_response), status_code
    except Exception as e:
        error_response, status_code = create_error_response(
            "GEMINI_CONNECTION_ERROR", 
            f"Gemini API接続エラー: {str(e)}"
        )
        return jsonify(error_response), status_code

@app.route("/test-html", methods=["GET"])
@handle_exceptions
def test_html():
    """HTML生成API接続テスト"""
    try:
        if test_html_generation():
            return create_success_response(None, "HTML生成API接続成功")
        else:
            error_response, status_code = create_error_response(
                "HTML_CONNECTION_ERROR", 
                "HTML生成API接続失敗"
            )
            return jsonify(error_response), status_code
    except Exception as e:
        error_response, status_code = create_error_response(
            "HTML_CONNECTION_ERROR", 
            f"HTML生成API接続エラー: {str(e)}"
        )
        return jsonify(error_response), status_code

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
            
            # 成功レスポンス
            response_data = {
                "userID": user_id,
                "callID": call_id,
                "userInfo": user_info,
                "conversationHistory": conversation_data,
                "diary": diary_text,
                "illustrationUrl": illustration_url,
                "htmlContent": html_content
            }
            
            return jsonify(create_success_response(
                response_data, 
                "ユーザー情報、会話履歴、日記、挿絵、HTMLページを正常に生成しました"
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

@app.route("/get-user-and-conversation", methods=["POST"])
@handle_exceptions
def get_user_and_conversation():
    """
    メインAPI: ユーザー情報取得→会話履歴取得の統合エンドポイント
    userIDからユーザー情報を取得し、その後userIDとcallIDで会話履歴を取得する
    
    注意: 日記生成も含む完全な処理には /generate-diary エンドポイントを使用してください
    """
    data = request.get_json()
    
    # リクエストデータの検証
    is_valid, error_response = validate_request_data(data, ["userID", "callID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    call_id = data["callID"]
    
    # Step 1: ユーザー情報取得
    user_info = get_user_info(user_id)
    if not user_info:
        error_response, status_code = create_error_response(
            "USER_NOT_FOUND", 
            "ユーザーが見つかりませんでした"
        )
        return jsonify(error_response), status_code
    
    # Step 2: 会話履歴取得 (サブコレクション構造を使用)
    service = SubcollectionConversationHistoryService()
    success, conversation_data, error_code = service.get_conversation_history(user_id, call_id)
    
    if not success:
        status_code = get_http_status_from_error_code(error_code)
        error_response, _ = create_error_response(error_code, "会話履歴の取得に失敗しました")
        return jsonify(error_response), status_code
    
    # 成功レスポンス
    response_data = {
        "userID": user_id,
        "callID": call_id,
        "userInfo": user_info,
        "conversationHistory": conversation_data
    }
    
    return jsonify(create_success_response(response_data, "ユーザー情報と会話履歴を正常に取得しました"))

# ===============================
# 互換性のための個別エンドポイント (レガシー)
# ===============================

@app.route("/get-user-info", methods=["POST"])
@handle_exceptions
def get_user_info_endpoint():
    """ユーザー情報取得エンドポイント (レガシー互換性のため残存)"""
    data = request.get_json()
    
    is_valid, error_response = validate_request_data(data, ["userID", "callID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    call_id = data["callID"]
    
    user_info = get_user_info(user_id)
    if user_info:
        response_data = {
            "userID": user_id,
            "callID": call_id,
            "userInfo": user_info
        }
        return jsonify(create_success_response(response_data))
    else:
        error_response, status_code = create_error_response(
            "USER_NOT_FOUND", 
            "ユーザーが見つかりませんでした"
        )
        return jsonify(error_response), status_code

@app.route("/get-conversation-history-v2", methods=["POST"])
@handle_exceptions
def get_conversation_history_v2_endpoint():
    """会話履歴取得エンドポイント (レガシー互換性のため残存)"""
    data = request.get_json()
    
    is_valid, error_response = validate_request_data(data, ["userID", "callID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    call_id = data["callID"]
    
    service = SubcollectionConversationHistoryService()
    success, response_data, error_code = service.get_conversation_history(user_id, call_id)
    
    if success:
        return jsonify(create_success_response(response_data))
    else:
        status_code = get_http_status_from_error_code(error_code)
        error_response, _ = create_error_response(error_code, "会話履歴の取得に失敗しました")
        return jsonify(error_response), status_code

@app.route("/get-user-calls", methods=["POST"])
@handle_exceptions
def get_user_calls_endpoint():
    """指定ユーザーのすべての会話履歴取得エンドポイント"""
    data = request.get_json()
    
    is_valid, error_response = validate_request_data(data, ["userID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    
    service = SubcollectionConversationHistoryService()
    success, response_data, error_code = service.get_user_all_calls(user_id)
    
    if success:
        return jsonify(create_success_response(response_data))
    else:
        status_code = get_http_status_from_error_code(error_code)
        error_response, _ = create_error_response(error_code, "会話履歴の取得に失敗しました")
        return jsonify(error_response), status_code

# ===============================
# 非推奨エンドポイント (互換性のためのみ)
# ===============================

@app.route("/get-conversation-history", methods=["POST"])
@handle_exceptions
def get_conversation_history_endpoint():
    """会話履歴取得エンドポイント (非推奨 - v2を使用してください)"""
    data = request.get_json()
    
    is_valid, error_response = validate_request_data(data, ["userID", "callID"])
    if not is_valid:
        return jsonify(error_response[0]), error_response[1]
    
    user_id = data["userID"]
    call_id = data["callID"]
    
    result = get_conversation_history(user_id, call_id)
    
    if result["status"] == "success":
        return jsonify(result), 200
    else:
        error_code = result.get("error_code", "UNKNOWN_ERROR")
        status_code = get_http_status_from_error_code(error_code)
        return jsonify(result), status_code

if __name__ == "__main__":
    print("AI Diary Service starting...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
