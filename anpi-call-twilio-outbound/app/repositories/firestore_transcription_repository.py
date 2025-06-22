"""Firestoreを使用した文字起こしリポジトリの実装"""

import os
from datetime import datetime
from typing import Optional, List
from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from google.cloud.firestore_v1.async_batch import AsyncWriteBatch

from models.transcription import TranscriptionMessage


class FirestoreTranscriptionRepository:
    """Firestoreを使用した文字起こしストレージリポジトリの実装"""

    def __init__(self, project_id: Optional[str] = None, auto_save_interval: int = 1000):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.db: AsyncClient = firestore.AsyncClient(project=self.project_id)
        self.auto_save_interval = auto_save_interval
        self.transcriptions: List[TranscriptionMessage] = []
        self.message_count = 0
        self.user_id: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.call_started_at: Optional[datetime] = None

    def start_transcription(self, user_id: Optional[str], call_sid: str):
        self.user_id = user_id
        self.call_sid = call_sid
        self.call_started_at = datetime.now()
        self.transcriptions.clear()
        self.message_count = 0

    async def add_transcription(self, speaker: str, text: str) -> bool:
        if not self.call_sid:
            raise ValueError(
                "Transcription not started. Call start_transcription first.")

        self.transcriptions.append(TranscriptionMessage(
            speaker=speaker,
            text=text,
            timestamp=datetime.now(),
            call_sid=self.call_sid,
            user_id=self.user_id if speaker == "user" else None
        ))
        self.message_count += 1

        if self.message_count % self.auto_save_interval == 0:
            await self._save()
            return True
        return False

    async def _save(self) -> Optional[str]:
        if not self.transcriptions or not self.call_sid:
            return None

        user_id_str = self.user_id or "anonymous"
        doc_ref = (
            self.db.collection("users")
            .document(user_id_str)
            .collection("calls")
            .document(self.call_sid)
        )

        batch: AsyncWriteBatch = self.db.batch()

        batch.set(
            doc_ref,
            {
                "user_id": self.user_id,
                "call_sid": self.call_sid,
                "call_started_at": self.call_started_at,
            },
            merge=True,
        )

        batch.update(
            doc_ref,
            {
                "transcriptions": firestore.ArrayUnion(
                    [msg.model_dump() for msg in self.transcriptions]
                )
            },
        )

        await batch.commit()

        self.transcriptions.clear()
        return doc_ref.path

    async def close(self):
        await self._save()
