import datetime

from google.cloud import storage


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
    プロダクションレベルの絵日記にふさわしいデザインを適用します。
    """
    image_html = ""
    # 画像URLが提供されている場合のみimgタグを生成
    if image_url:
        image_html = f"""
            <div class="diary-image-wrapper">
                <img src="{image_url}" alt="AI生成画像">
            </div>
        """

    # 現在の日付を取得し、日本語形式にフォーマット
    current_date = datetime.date.today().strftime("%Y年%m月%d日")

    # HTMLコンテンツを構築
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI絵日記</title>
    <style>
        /* Basic Reset & Font */
        body {{
            font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f8f8; /* Light grey background */
            color: #333;
        }}

        /* Container for the diary entry */
        .diary-container {{
            max-width: 800px;
            margin: 40px auto;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            padding: 30px 40px;
            box-sizing: border-box; /* Include padding in width/height */
        }}

        /* Header */
        .diary-header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }}

        .diary-header h1 {{
            font-size: 2.5em;
            color: #4a4a4a;
            margin: 0;
            font-weight: 700;
        }}

        /* Image Styling */
        .diary-image-wrapper {{
            text-align: center;
            margin-bottom: 30px;
        }}

        .diary-image-wrapper img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
            border: 1px solid #ddd;
            display: block; /* Remove extra space below image */
            margin: 0 auto; /* Center image */
        }}

        /* Text Content Styling */
        .diary-content {{
            background-color: #fdfdfd;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 25px;
            line-height: 1.8;
            font-size: 1.1em;
            color: #555;
            white-space: pre-wrap; /* Preserve whitespace and wrap lines */
            word-wrap: break-word; /* Break long words */
        }}

        /* For pre tag specifically, if user wants to keep it */
        .diary-content pre {{
            margin: 0; /* Remove default pre margin */
            font-family: inherit; /* Inherit font from body */
            white-space: pre-wrap; /* Ensure pre content wraps */
            word-wrap: break-word;
        }}

        /* Footer */
        .diary-footer {{
            text-align: right;
            margin-top: 30px;
            font-size: 0.9em;
            color: #888;
        }}
    </style>
</head>
<body>
    <div class="diary-container">
        <header class="diary-header">
            <h1>AI絵日記</h1>
        </header>
        <main>
            {image_html}
            <div class="diary-content">
                <pre>{text_content}</pre>
            </div>
        </main>
        <footer class="diary-footer">
            <p>日付: {current_date}</p>
        </footer>
    </div>
</body>
</html>"""
    return html
