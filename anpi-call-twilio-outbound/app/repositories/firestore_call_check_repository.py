"""通話チェック結果をFirestoreに保存するリポジトリ"""

import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient

from models.call_check import CallCheckResult


class FirestoreCallCheckRepository:
    """通話チェック結果をFirestoreに保存するリポジトリ"""

    def __init__(self, project_id: Optional[str] = None):
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.db: AsyncClient = firestore.AsyncClient(project=self.project_id)

    async def save_check_result(self, user_id: str, result: CallCheckResult) -> str:
        """
        通話チェック結果を保存
        
        Args:
            user_id: ユーザーID
            result: チェック結果
            
        Returns:
            保存されたドキュメントID
        """
        try:
            # チェックIDを生成（UUID）
            check_id = str(uuid.uuid4())
            
            # パス: /users/{user_id}/call_checks/{check_id}
            doc_ref = (self.db.collection("users")
                      .document(user_id)
                      .collection("call_checks")
                      .document(check_id))
            
            # 保存データ（resultの内容をそのまま保存）
            check_data = result.model_dump()
            check_data["created_at"] = firestore.SERVER_TIMESTAMP
            
            await doc_ref.set(check_data)
            
            return check_id
            
        except Exception as e:
            raise Exception(f"チェック結果保存エラー: {str(e)}")

    async def get_check_result(self, user_id: str, check_id: str) -> Optional[Dict[str, Any]]:
        """
        特定のチェック結果を取得
        
        Args:
            user_id: ユーザーID
            check_id: チェックID
            
        Returns:
            チェック結果データ
        """
        try:
            doc_ref = (self.db.collection("users")
                      .document(user_id)
                      .collection("call_checks")
                      .document(check_id))
            
            doc = await doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            raise Exception(f"チェック結果取得エラー: {str(e)}")

    async def get_recent_check_results(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ユーザーの最近のチェック結果を取得
        
        Args:
            user_id: ユーザーID
            limit: 取得件数
            
        Returns:
            チェック結果のリスト
        """
        try:
            query = (self.db.collection("users")
                    .document(user_id)
                    .collection("call_checks")
                    .order_by("analyzed_at", direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = await query.get()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["check_id"] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            raise Exception(f"最近のチェック結果取得エラー: {str(e)}")

    async def delete_check_result(self, user_id: str, check_id: str) -> bool:
        """
        チェック結果を削除
        
        Args:
            user_id: ユーザーID
            check_id: チェックID
            
        Returns:
            削除成功可否
        """
        try:
            doc_ref = (self.db.collection("users")
                      .document(user_id)
                      .collection("call_checks")
                      .document(check_id))
            
            await doc_ref.delete()
            return True
            
        except Exception as e:
            raise Exception(f"チェック結果削除エラー: {str(e)}")

    async def get_check_history_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        ユーザーのチェック履歴統計を取得
        
        Args:
            user_id: ユーザーID
            days: 集計期間（日数）
            
        Returns:
            統計データ
        """
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = (self.db.collection("users")
                    .document(user_id)
                    .collection("call_checks")
                    .where("analyzed_at", ">=", cutoff_date)
                    .order_by("analyzed_at"))
            
            docs = await query.get()
            
            total_checks = len(docs)
            issue_count = 0
            latest_check = None
            
            for doc in docs:
                data = doc.to_dict()
                
                severity_level = data.get("severity_level", "通常")
                if severity_level in ["要観察", "異常"]:
                    issue_count += 1
                
                if latest_check is None or data.get("analyzed_at") > latest_check:
                    latest_check = data.get("analyzed_at")
            
            return {
                "user_id": user_id,
                "period_days": days,
                "total_checks": total_checks,
                "issue_count": issue_count,
                "issue_rate": issue_count / total_checks if total_checks > 0 else 0.0,
                "latest_check": latest_check
            }
            
        except Exception as e:
            raise Exception(f"チェック履歴統計取得エラー: {str(e)}")

