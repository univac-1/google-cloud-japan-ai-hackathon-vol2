import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from illustration.prompt_builder import build_prompt

from google.cloud import storage
import io

PROJECT_ID = "univac-aiagent"
BUCKET_NAME = "ai-diary"

def generate_illustration(diary_text: str, user_id: str, gender: str, call_id: str) -> str:
    """
    絵日記本文から画像を生成し、GCSにその画像を保存してURLを返します。
    """
    
    prompt = build_prompt(diary_text, gender)

    vertexai.init(project=PROJECT_ID, location="us-central1")
    generation_model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-001")

    images = generation_model.generate_images(
        prompt=prompt,
        number_of_images=1,
        language="ja",
        aspect_ratio="1:1",
        safety_filter_level="block_some",
        person_generation="allow_all",
    )

    # GCSへ保存
    image_data = images[0]._image_bytes
    return upload_image_to_gcs(image_data, user_id, call_id)


def upload_image_to_gcs(image_bytes: bytes, user_id: str, call_id: str) -> str:
    """
    GCS に画像をアップロードして、公開URLを返す
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)

    # 一意なファイル名を生成
    filename = f"illustrations/{user_id}/{call_id}.png"
    blob = bucket.blob(filename)

    blob.upload_from_file(io.BytesIO(image_bytes), content_type="image/png")

    return blob.public_url
