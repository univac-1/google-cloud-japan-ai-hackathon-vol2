import json
import os
from typing import Optional, Dict, Any
from app.models.schemas import User


class UserRepository:
    """ユーザー情報を管理するリポジトリ"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or "/workspace/realtime-api-test/db/sample/user.json"
        self._users_cache: Optional[Dict[str, Dict[str, Any]]] = None
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """ユーザーデータをファイルから読み込み"""
        if self._users_cache is not None:
            return self._users_cache
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
                # user_idをキーとした辞書に変換
                self._users_cache = {user["user_id"]: user for user in users_list}
                return self._users_cache
        except Exception as e:
            raise Exception(f"ユーザーデータの読み込みエラー: {str(e)}")
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """ユーザーIDでユーザー情報を取得"""
        users = self._load_users()
        user_data = users.get(user_id)
        
        if user_data:
            try:
                return User(**user_data)
            except Exception as e:
                raise Exception(f"ユーザーデータの変換エラー: {str(e)}")
        
        return None
    
