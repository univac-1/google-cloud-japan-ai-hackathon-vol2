import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from google.cloud import storage
from google.cloud.exceptions import NotFound
import asyncio

from .file_storage_repository import FileMetadata

logger = logging.getLogger(__name__)


class GCSFileStorageRepository:
    """Google Cloud Storage を使用したファイルストレージリポジトリの実装（1通話1インスタンス）"""

    def __init__(self, bucket_name: Optional[str] = None, auto_save_interval: int = 10):
        """
        Args:
            bucket_name: GCSバケット名（環境変数GCS_BUCKET_NAMEからも取得可能）
            auto_save_interval: 自動保存する会話数の間隔（デフォルト: 10メッセージごと）
        """
        self.bucket_name = bucket_name or os.getenv("GCS_BUCKET_NAME", "univac-aiagent-transcription")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)
        
        # ファイルプレフィックス
        self.files_prefix = "transcriptions/"
        
        # 通話データの管理
        self.user_id: Optional[str] = None
        self.call_started_at = datetime.now()
        self.transcriptions = []
        self.message_count = 0
        self.auto_save_interval = auto_save_interval
        self.last_saved_at: Optional[datetime] = None
        self.save_count = 0  # 保存回数
        
        # 非同期実行用のスレッドプール（同期的なGCS APIを非同期で実行するため）
        self.executor = ThreadPoolExecutor(max_workers=1)
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def start_transcription(self, user_id: Optional[str] = None):
        """文字起こしを開始"""
        self.user_id = user_id
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
        transcription = {
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
        
        self.transcriptions.append(transcription)
        self.message_count += 1
        
        # 自動保存の判断
        should_save = (
            self.message_count % self.auto_save_interval == 0 and
            self.message_count > 0
        )
        
        if should_save:
            await self._save()
            self.logger.info(f"自動保存を実行しました（{self.message_count}メッセージ）")
            return True
        
        return False

    async def _save(self, is_final: bool = False) -> FileMetadata:
        """
        現在のデータをGCSに保存

        Args:
            is_final: 最終保存かどうか

        Returns:
            FileMetadata: 保存されたファイルのメタデータ
        """
        try:
            # 保存回数をインクリメント
            self.save_count += 1
            
            # ファイル名の生成（保存回数を含める）
            timestamp = self.call_started_at.strftime("%Y%m%d_%H%M%S")
            user_id_str = f"_{self.user_id}" if self.user_id else "_anonymous"
            filename = f"transcription{user_id_str}_{timestamp}_{self.save_count:03d}.json"
            
            # フォーマットされたテキストを生成
            formatted_text = []
            for item in self.transcriptions:
                speaker = "ユーザー" if item["speaker"] == "user" else "エージェント"
                formatted_text.append(f"{speaker}: {item['text']}")
            
            # データの準備
            data = {
                'user_id': self.user_id,
                'call_started_at': self.call_started_at.isoformat(),
                'saved_at': datetime.now().isoformat(),
                'is_final': is_final,
                'message_count': self.message_count,
                'transcriptions': self.transcriptions,
                'formatted_text': "\n".join(formatted_text)
            }
            
            content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            
            # ファイルパスを生成
            if self.user_id:
                file_path = f"{self.files_prefix}{self.user_id}/{filename}"
            else:
                file_path = f"{self.files_prefix}anonymous/{filename}"
            
            # ファイルを非同期でアップロード
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                self._upload_file_sync,
                file_path,
                content
            )
            
            # メタデータを作成
            file_metadata = FileMetadata(
                filename=filename,
                user_id=self.user_id,
                created_at=self.call_started_at,
                updated_at=datetime.now(),
                file_type='json',
                file_size=len(content),
                file_path=f"gs://{self.bucket_name}/{file_path}",
                metadata={}  # 空にする
            )
            
            # 最後の保存時刻を更新
            self.last_saved_at = datetime.now()
            
            self.logger.info(f"文字起こしをGCSに保存しました: {filename} (is_final: {is_final})")
            return file_metadata
            
        except Exception as e:
            self.logger.error(f"GCS保存エラー: {e}", exc_info=True)
            raise Exception(f"文字起こしの保存に失敗しました: {str(e)}")


    def _upload_file_sync(self, blob_name: str, content: bytes):
        """同期的にファイルをアップロード"""
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(content)

    async def close(self):
        """リソースをクリーンアップ"""
        # まだ保存されていないデータがあれば最終保存
        if self.transcriptions and (self.last_saved_at is None or len(self.transcriptions) > 0):
            self.logger.info(f"終了時に未保存のデータを保存します（{self.message_count}メッセージ）")
            await self._save(is_final=True)
        
        # スレッドプールを終了
        self.executor.shutdown(wait=True)