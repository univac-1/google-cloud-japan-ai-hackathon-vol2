import json
import os
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.schemas import Event


class EventRepository:
    """イベント情報を管理するリポジトリ"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or "/workspace/realtime-api-test/db/sample/event.json"
        self._events_cache: Optional[List[Event]] = None
    
    def _load_events(self) -> List[Event]:
        """イベントデータをファイルから読み込み"""
        if self._events_cache is not None:
            return self._events_cache
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                events_data = json.load(f)
                # Event型のリストに変換
                self._events_cache = [Event(**event_data) for event_data in events_data]
                return self._events_cache
        except Exception as e:
            raise Exception(f"イベントデータの読み込みエラー: {str(e)}")
    
    async def get_all_events(self) -> List[Event]:
        """全てのイベントを取得"""
        return self._load_events()
    
    async def get_events_by_prefecture(self, prefecture: str) -> List[Event]:
        """県でイベントを絞り込み"""
        events = self._load_events()
        return [event for event in events if event.prefecture == prefecture]
    
    async def get_events_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Event]:
        """日付範囲でイベントを絞り込み"""
        events = self._load_events()
        return [
            event for event in events 
            if start_date <= event.start_datetime <= end_date
        ]
    
    async def get_events_by_prefecture_and_date_range(
        self, 
        prefecture: str, 
        start_date: datetime, 
        end_date: datetime,
        max_count: int = 100
    ) -> List[Event]:
        """県と日付範囲でイベントを絞り込み、開始日順でソート"""
        events = self._load_events()
        
        # フィルタリング
        filtered_events = [
            event for event in events 
            if event.prefecture == prefecture 
            and start_date <= event.start_datetime <= end_date
        ]
        
        # 開始日でソート
        filtered_events.sort(key=lambda x: x.start_datetime)
        
        # 最大件数で制限
        return filtered_events[:max_count]
    
    async def get_upcoming_events_by_prefecture(
        self, 
        prefecture: str,
        weeks_ahead_min: int = 1,
        weeks_ahead_max: int = 4,
        max_count: int = 100
    ) -> List[Event]:
        """指定県の今後のイベントを取得（デフォルト: 1週間後〜4週間後）"""
        now = datetime.now()
        start_date = now + timedelta(weeks=weeks_ahead_min)
        end_date = now + timedelta(weeks=weeks_ahead_max)
        
        return await self.get_events_by_prefecture_and_date_range(
            prefecture, start_date, end_date, max_count
        )