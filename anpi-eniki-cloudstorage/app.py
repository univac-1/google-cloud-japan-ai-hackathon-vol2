import datetime
import logging
import os
import uuid

from flask import Flask, jsonify, request
from google.cloud import storage

from .src.utils import check_image_exists_in_gcs, generate_html_content

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 環境変数からGCSバケット名を取得
# デプロイ時に環境変数として設定します (例: OUTPUT_BUCKET_NAME=my-html-output-bucket)
OUTPUT_BUCKET_NAME = os.environ.get("OUTPUT_BUCKET_NAME")
IMAGE_BUCKET_NAME = os.environ.get("IMAGE_BUCKET_NAME", OUTPUT_BUCKET_NAME)


if not OUTPUT_BUCKET_NAME:
    raise ValueError("OUTPUT_BUCKET_NAME environment variable not set.")

storage_client = storage.Client()
output_bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
image_bucket = storage_client.bucket(IMAGE_BUCKET_NAME)


@app.route("/process-text", methods=["POST"])
def process_text():
    # --- テキストコンテンツの取得 ---
    text_content = ""
    if "text_content" in request.form:
        text_content = request.form["text_content"]
    else:
        return (
            jsonify(
                {"error": "Invalid request. 'text_content' form field is required."}
            ),
            400,
        )

    # 'user_id' フィールドは必須
    if "user_id" in request.form:
        user_id = request.form["user_id"]
    else:
        return (
            jsonify({"error": "Invalid request. 'user_id' form field is required."}),
            400,
        )

    # 'call_id' フィールドは必須
    if "call_id" in request.form:
        call_id = request.form["call_id"]
    else:
        return (
            jsonify({"error": "Invalid request. 'call_id' form field is required."}),
            400,
        )

    # --- 画像ファイルの取得 ---
    image_url = f"https://storage.googleapis.com/eniki-completed/illustrations/{user_id}/{call_id}.png"
    if not check_image_exists_in_gcs(image_bucket, user_id, call_id):
        image_url = None  # 画像が存在しない場合はNoneに設定

    # --- HTMLコンテンツの生成 (新しい関数に委譲) ---
    # generate_html_content 関数を呼び出し
    html_content = generate_html_content(text_content, image_url)

    # --- HTMLファイルのGCSへの書き込み ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    output_file_name = f"eniki/{timestamp}-{unique_id}.html"

    output_blob = output_bucket.blob(output_file_name)
    try:
        output_blob.upload_from_string(
            html_content, content_type="text/html; charset=UTF-8"
        )
        print(f"Successfully uploaded {output_file_name} to GCS.")

        public_url = (
            f"https://storage.googleapis.com/{OUTPUT_BUCKET_NAME}/{output_file_name}"
        )
        return (
            jsonify(
                {
                    "message": "Content processed and uploaded to GCS successfully.",
                    "output_url": public_url,
                    "image_url_if_uploaded": image_url,
                    "content": html_content,
                }
            ),
            200,
        )
    except Exception as e:
        print(f"Error uploading HTML to GCS: {e}")
        return (
            jsonify({"error": "Failed to upload HTML to GCS.", "details": str(e)}),
            500,
        )


def health_check():
    """
    ヘルスチェック用エンドポイント
    """
    return (
        jsonify(
            {"status": "healthy", "service": "eniki-html-generator", "version": "1.0.0"}
        ),
        200,
    )


if __name__ == "__main__":
    # ローカルでのテスト用
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
