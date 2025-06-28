import os

from illustration.generator import generate_illustration
from flask import Flask, request, jsonify
from get_info.user_service import get_user_info
from get_info.db_connection import test_connection

app = Flask(__name__)

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
    return {"status": "healthy", "service": "ai-diary-get-info"}

@app.route("/test-db", methods=["GET"])
def test_db():
    """DB接続テスト"""
    if test_connection():
        return {"status": "success", "message": "DB接続成功"}
    else:
        return {"status": "error", "message": "DB接続失敗"}, 500

@app.route("/get-user-info", methods=["POST"])
def get_user_info_endpoint():
    """ユーザー情報取得エンドポイント"""
    try:
        # リクエストからuserIDとcallIDを取得
        data = request.get_json()
        if not data:
            return {"error": "JSONデータが必要です"}, 400
        
        user_id = data.get("userID")
        call_id = data.get("callID")
        
        if not user_id:
            return {"error": "userIDが必要です"}, 400
        
        if not call_id:
            return {"error": "callIDが必要です"}, 400
        
        # ユーザー情報を取得
        user_info = get_user_info(user_id)
        
        if user_info:
            response = {
                "status": "success",
                "userID": user_id,
                "callID": call_id,
                "userInfo": user_info
            }
            return jsonify(response)
        else:
            return {
                "status": "error",
                "userID": user_id,
                "callID": call_id,
                "message": "ユーザーが見つかりませんでした"
            }, 404
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"処理中にエラーが発生しました: {str(e)}"
        }, 500

if __name__ == "__main__":
    print("AI Diary Get Info Service starting...")
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
