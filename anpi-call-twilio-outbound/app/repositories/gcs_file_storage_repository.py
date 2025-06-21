import os
import json
import logging
import asyncio
import copy
from datetime import datetime
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from google.cloud import storage
from google.cloud.exceptions import NotFound

from models.transcription import TranscriptionMessage
from utils.json_serializer import datetime_serializer

logger = logging.getLogger(__name__)


class GCSFileStorageRepository:
    """Google Cloud Storage を使用したファイルストレージリポジトリの実装（1通話1インスタンス）"""

    def __init__(self, bucket_name: Optional[str] = None, auto_save_interval: int = 2):
        """
        Args:
            bucket_name: GCSバケット名（環境変数GCS_BUCKET_NAMEからも取得可能）
            auto_save_interval: 自動保存する会話数の間隔（デフォルト: 2メッセージごと）
        """
        self.bucket_name = bucket_name or os.getenv(
            "GCS_BUCKET_NAME", "univac-aiagent-transcription")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

        # 通話データの管理
        self.user_id: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.call_started_at = datetime.now()
        self.transcriptions: list[TranscriptionMessage] = []
        self.message_count = 0
        self.auto_save_interval = auto_save_interval
        self.last_saved_at: Optional[datetime] = None
        self.save_count = 0  # 保存回数

        # 非同期実行用のスレッドプール（同期的なGCS APIを非同期で実行するため）
        self.executor = ThreadPoolExecutor(max_workers=1)

    def start_transcription(self, user_id: Optional[str], call_sid: str):
        """文字起こしを開始"""
        self.user_id = user_id
        self.call_sid = call_sid
        self.call_started_at = datetime.now()  # 開始時刻をリセット
        self.save_count = 0  # 保存回数をリセット

    async def add_transcription(self, speaker: str, text: str) -> bool:
        """
        文字起こしデータを追加（自動保存判断付き）

        Args:
            speaker: 話者（"user" または "assistant"）
            text: 文字起こしテキスト

        Returns:
            bool: 自動保存が実行されたかどうか
        """
        transcription = TranscriptionMessage(
            speaker=speaker,
            text=text,
            timestamp=datetime.now(),
            call_sid=self.call_sid,
            user_id=self.user_id if speaker == "user" else None
        )

        self.transcriptions.append(transcription)
        self.message_count += 1

        # 自動保存の判断
        should_save = (
            self.message_count % self.auto_save_interval == 0 and
            self.message_count > 0
        )

        if should_save:
            await self._save()
            logger.info(f"自動保存を実行しました（{self.message_count}メッセージ）")
            return True

        return False

    async def _save(self) -> str:
        """
        現在のデータをGCSに保存

        Returns:
            str: 保存されたファイルのGCSパス
        """
        try:
            # 保存回数をインクリメント
            self.save_count += 1

            # 保存対象のデータをdeep copyでスナップショット
            transcriptions_snapshot = copy.deepcopy(self.transcriptions)
            saved_messages_count = len(transcriptions_snapshot)
            
            # ファイル名の生成（call_sidを含める）
            timestamp = self.call_started_at.strftime("%Y%m%d_%H%M%S")
            filename = f"transcription_{self.call_sid}_{timestamp}_{self.save_count:03d}.json"

            # TranscriptionMessageのリストを直接JSON化
            transcriptions_data = {
                "call_started_at": self.call_started_at,
                "transcriptions": [msg.model_dump() for msg in transcriptions_snapshot]
            }

            # JSON文字列を生成してUTF-8でエンコード
            content = json.dumps(
                transcriptions_data,
                ensure_ascii=False,
                indent=2,
                default=datetime_serializer
            ).encode('utf-8')

            # ファイルパスを生成（user_id/conversation/日付/call_sid/ファイル名の階層）
            date_str = self.call_started_at.strftime("%Y-%m-%d")
            if self.user_id:
                file_path = f"{self.user_id}/conversation/{date_str}/{self.call_sid}/{filename}"
            else:
                file_path = f"anonymous/conversation/{date_str}/{self.call_sid}/{filename}"

            # ファイルを非同期でアップロード
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._upload_file_sync,
                file_path,
                content
            )

            # アップロード成功後の処理
            # 最後の保存時刻を更新
            self.last_saved_at = datetime.now()

            # GCSパスを生成
            gcs_path = f"gs://{self.bucket_name}/{file_path}"

            # 保存成功後、メモリから保存済みデータをクリア
            # 保存したメッセージ数分だけ削除（新たに追加されたものは残す）
            del self.transcriptions[:saved_messages_count]
            logger.info(
                f"文字起こしを保存しました: {filename} ({saved_messages_count}メッセージ)")

            return gcs_path

        except Exception as e:
            logger.error(f"GCS保存エラー: {e}", exc_info=True)
            raise Exception(f"文字起こしの保存に失敗しました: {str(e)}")

    def _upload_file_sync(self, blob_name: str, content: bytes):
        """同期的にファイルをアップロード"""
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            content, content_type='application/json; charset=utf-8')

    async def close(self):
        """リソースをクリーンアップ"""
        # まだ保存されていないデータがあれば保存
        if self.transcriptions:
            logger.info(
                f"終了時に未保存のデータを保存します（{len(self.transcriptions)}メッセージ）")
            await self._save()

        # スレッドプールを終了
        self.executor.shutdown(wait=True)
