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

if __name__ == "__main__":
    print("AI Diary Service starting...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
