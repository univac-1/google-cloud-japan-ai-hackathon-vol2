import os
from flask import Flask, request, jsonify
from get_info.user_service import get_user_info
from get_history.subcollection_conversation_service import SubcollectionConversationHistoryService
from create_diary_entry import DiaryGenerator
from illustration.generator import generate_illustration
from html_generator.generator import generate_html_page
from email_sender.service import process_diary_email_sending

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health_check():
    """ヘルスチェック"""
    return {"status": "success", "data": {"service": "ai-diary-service"}, "message": "healthy"}

@app.route("/test-db", methods=["GET"])
def test_db_connection():
    """データベース接続テスト"""
    try:
        from get_info.db_connection import test_connection
        result = test_connection()
        if result:
            return {"status": "success", "data": {"db_status": "connected"}, "message": "Database connection successful"}
        else:
            return {"status": "error", "message": "Database connection failed"}, 500
    except Exception as e:
        return {"status": "error", "message": f"Database test failed: {type(e).__name__}"}, 500

@app.route("/generate-diary", methods=["POST"])
def generate_diary_endpoint():
    """日記生成API"""
    try:
        data = request.get_json()
        if not data or not data.get("userID") or not data.get("callID"):
            return {"status": "error", "message": "userID and callID are required"}, 400
        
        user_id = data["userID"]
        call_id = data["callID"]
        
        app.logger.info(f"user_id:{user_id}")
        app.logger.info(f"call_id:{call_id}")
        
        # ユーザー情報取得
        user_info = get_user_info(user_id)
        if not user_info:
            return {"status": "error", "message": "User not found"}, 404
        
        # 会話履歴取得
        service = SubcollectionConversationHistoryService()
        success, conversation_data, error_code = service.get_conversation_history(user_id, call_id)
        if not success:
            return {"status": "error", "message": f"Conversation not found: {error_code}"}, 404
        
        # 日記生成
        generator = DiaryGenerator()
        diary_success, diary_text, diary_error = generator.generate_diary_entry(user_info, conversation_data)
        if not diary_success:
            return {"status": "error", "message": f"Diary generation failed: {diary_error}"}, 500
        
        # 挿絵作成（エラーでも継続）
        illustration_url = None
        try:
            gender = user_info.get('gender', 'unknown')
            illustration_url = generate_illustration(diary_text, user_id, gender, call_id)
        except Exception as e:
            app.logger.warning(f"Illustration generation failed: {type(e).__name__}")
        
        # HTML生成（エラーでも継続）
        html_content = None
        try:
            html_content = generate_html_page(diary_text, user_id, call_id)
        except Exception as e:
            app.logger.warning(f"HTML generation failed: {type(e).__name__}")
        
        # メール送信（エラーでも継続）
        email_sent, email_message = False, "Not attempted"
        try:
            email_sent, email_message = process_diary_email_sending(user_info, html_content, user_id)
        except Exception as e:
            app.logger.warning(f"Email sending failed: {type(e).__name__}")
        
        return {
            "status": "success",
            "data": {
                "userID": user_id,
                "callID": call_id,
                "userInfo": user_info,
                "conversationHistory": conversation_data,
                "diary": diary_text,
                "illustrationUrl": illustration_url,
                "htmlContent": html_content,
                "emailSent": email_sent,
                "emailMessage": email_message
            },
            "message": "Diary generation completed"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Internal error: {type(e).__name__}"}, 500

if __name__ == "__main__":
    print("AI Diary Service starting...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
