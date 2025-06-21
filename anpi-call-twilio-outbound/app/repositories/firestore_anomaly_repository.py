"""Firestoreを使用した異常検知結果リポジトリの実装"""

import os
import logging
from datetime import datetime
from typing import Optional
from google.cloud import firestore

from .anomaly_result_repository import AnomalyResultRepository
from analysis.detect_anomaly import AnomalyResult

logger = logging.getLogger(__name__)


class FirestoreAnomalyRepository(AnomalyResultRepository):
    """Firestoreを使用した異常検知結果リポジトリ"""
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Args:
            project_id: GCPプロジェクトID（環境変数GCP_PROJECT_IDからも取得可能）
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.db = firestore.Client(project=self.project_id)
        self.collection_name = "anomaly_results"
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def save_result(self, user_id: str, result: AnomalyResult) -> str:
        """
        異常検知結果をFirestoreに保存
        
        Args:
            user_id: ユーザーID
            result: 異常検知結果
            
        Returns:
            str: 保存されたドキュメントID
        """
        try:
            # Firestoreに保存するデータを準備
            document_data = {
                "user_id": user_id,
                "has_anomaly": result.has_anomaly,
                "reason": result.reason,
                "confidence": result.confidence,
                "detected_issues": result.detected_issues,
                "source_files": result.source_files,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            # ドキュメントを追加
            doc_ref = self.db.collection(self.collection_name).document()
            doc_ref.set(document_data)
            
            document_id = doc_ref.id
            
            self.logger.info(f"異常検知結果をFirestoreに保存: user_id={user_id}, doc_id={document_id}, has_anomaly={result.has_anomaly}")
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"Firestore保存エラー: user_id={user_id}, error={e}", exc_info=True)
            raise Exception(f"異常検知結果の保存に失敗しました: {str(e)}")