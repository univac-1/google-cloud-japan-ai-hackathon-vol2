import os

from flask import Flask
from illustration.generator import generate_illustration

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
    except Exception as e:
        print("❌ エラーが発生しました:", str(e))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
