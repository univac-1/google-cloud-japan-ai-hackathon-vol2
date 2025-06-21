"""Firestoreから通話データを取得するリポジトリ"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient

from models.transcription import TranscriptionMessage


class FirestoreCallRepository:
    """Firestoreから通話データを取得するリポジトリ"""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.db: AsyncClient = firestore.AsyncClient(project=self.project_id)

    async def get_recent_calls(self, user_id: str, days: int = 7, max_calls: int = 5) -> List[Dict[str, Any]]:
        """
        指定ユーザーの最近の通話データを取得
        
        Args:
            user_id: ユーザーID
            days: 取得期間（日数）
            max_calls: 最大取得件数
            
        Returns:
            通話データのリスト
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            calls_ref = (self.db.collection("users")
                        .document(user_id)
                        .collection("calls"))
            
            # 最近の通話を取得
            query = (calls_ref
                    .where("call_started_at", ">=", cutoff_date)
                    .order_by("call_started_at", direction=firestore.Query.DESCENDING)
                    .limit(max_calls))
            
            docs = await query.get()
            
            calls = []
            for doc in docs:
                data = doc.to_dict()
                data["call_id"] = doc.id
                calls.append(data)
            
            return calls
            
        except Exception as e:
            raise Exception(f"通話データ取得エラー: {str(e)}")

    async def get_call_by_id(self, user_id: str, call_sid: str) -> Optional[Dict[str, Any]]:
        """
        特定の通話データを取得
        
        Args:
            user_id: ユーザーID
            call_sid: 通話ID
            
        Returns:
            通話データ
        """
        try:
            doc_ref = (self.db.collection("users")
                      .document(user_id)
                      .collection("calls")
                      .document(call_sid))
            
            doc = await doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["call_id"] = doc.id
                return data
            
            return None
            
        except Exception as e:
            raise Exception(f"通話データ取得エラー: {str(e)}")

