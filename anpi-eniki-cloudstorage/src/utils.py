import datetime
import uuid

from google.cloud import storage
from werkzeug.datastructures import (
    FileStorage,
)  # Flaskのリクエストファイルオブジェクトの型ヒント用

# --- 画像タイプを判別する補助関数 ---
# よく使われる画像形式のマジックバイトを定義
# より多くの形式に対応するには、ここに追加
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"GIF87a": "gif",
    b"GIF89a": "gif",
    b"BM": "bmp",  # BMPはサイズ情報も含むため、完全な判別には追加ロジックが必要な場合も
    b"RIFF....WEBPVP8": "webp",  # WEBPもバリアントがあるため、完璧ではない
}


def get_image_type_from_bytes(image_bytes: bytes) -> str | None:
    """
    バイト列の先頭数バイトから画像タイプを判別します。
    """
    for signature, img_type in IMAGE_SIGNATURES.items():
        if image_bytes.startswith(signature):
            return img_type
    return None


def upload_image_to_gcs(
    image_file: FileStorage, image_bucket: storage.Bucket
) -> str | None:
    """
    画像をGCSにアップロードし、その公開URLを返します。
    失敗した場合はNoneを返します。
    """
    try:
        image_bytes = image_file.read()
        # 新しい補助関数で画像タイプを判別
        image_type = get_image_type_from_bytes(image_bytes)

        if not image_type:
            print("Uploaded file is not a recognized image type.")
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        image_filename_in_gcs = f"B/images/{timestamp}-{unique_id}.{image_type}"

        image_blob = image_bucket.blob(image_filename_in_gcs)
        image_blob.upload_from_string(image_bytes, content_type=f"image/{image_type}")
        # image_blob.make_public() # バケット全体が公開なら不要

        image_url = f"https://storage.googleapis.com/{image_bucket.name}/{image_filename_in_gcs}"
        print(f"Image uploaded to GCS: {image_url}")
        return image_url
    except Exception as e:
        print(f"Error uploading image to GCS: {e}")
        return None


def check_image_exists_in_gcs(
    image_bucket: storage.Bucket, user_id: str, call_id: str
) -> bool:
    """
    指定されたユーザーIDとCall IDに基づいて、GCSに画像ファイルが存在するかどうかを確認します。

    Args:
        image_bucket (storage.Bucket): 画像が保存されているGCSバケットのオブジェクト。
        user_id (str): 画像のパスに含まれるユーザーID。
        call_id (str): 画像のパスに含まれるCall ID。

    Returns:
        bool: ファイルが存在すればTrue、そうでなければFalse。
    """
    # ユーザーが指定したパス形式: https://storage.googleapis.com/eniki-completed/illustrations/｛ユーザーID｝/｛call ID｝.png
    image_filename_in_gcs = f"illustrations/{user_id}/{call_id}.png"

    # GCSのBlobオブジェクトを取得
    blob = image_bucket.blob(image_filename_in_gcs)

    # blob.exists() メソッドでファイルの存在を確認
    return blob.exists()


def generate_html_content(text_content: str, image_url: str | None) -> str:
    """
    テキストと画像URLからHTMLコンテンツを生成します。
    """
    image_html = ""
    if image_url:
        image_html = f'<p><img src="{image_url}" alt="Uploaded Image" style="max-width:100%; height:auto;"></p>'

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Processed Content</title>
</head>
<body>
<h1>AI絵日記</h1>
{image_html}
<pre>
{text_content}
</pre>
</body>
</html>"""
    return html
