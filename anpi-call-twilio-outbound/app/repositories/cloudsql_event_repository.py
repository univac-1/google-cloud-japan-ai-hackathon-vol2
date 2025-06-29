"""CloudSQL implementation of EventRepository."""
from datetime import datetime, timedelta
from typing import List
import logging

from sqlalchemy import select, and_

from models.schemas import Event
from database import get_db_session, EventTable

logger = logging.getLogger(__name__)


class CloudSQLEventRepository:
    """
    CloudSQLを使用したイベントリポジトリの実装

    データベース接続は分離され、ビジネスロジックに集中
    """

    async def get_all_events(self) -> List[Event]:
        """全てのイベントを取得"""
        try:
            session = await get_db_session()
            async with session:
                result = await session.execute(
                    select(EventTable).order_by(EventTable.start_datetime)
                )
                events = result.scalars().all()

                return [self._to_event_model(event) for event in events]
        except Exception as e:
            logger.error(f"イベント取得中にエラーが発生しました: {e}")
            raise Exception(f"イベント取得中にエラーが発生しました: {str(e)}")

    async def get_events_by_prefecture(self, prefecture: str) -> List[Event]:
        """都道府県でイベントをフィルタリング"""
        try:
            session = await get_db_session()
            async with session:
                result = await session.execute(
                    select(EventTable)
                    .where(EventTable.prefecture == prefecture)
                    .order_by(EventTable.start_datetime)
                )
                events = result.scalars().all()

                return [self._to_event_model(event) for event in events]
        except Exception as e:
            logger.error(f"都道府県別イベント取得中にエラーが発生しました: {e}")
            raise Exception(f"都道府県別イベント取得中にエラーが発生しました: {str(e)}")

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Event]:
        """日付範囲でイベントをフィルタリング"""
        try:
            session = await get_db_session()
            async with session:
                result = await session.execute(
                    select(EventTable)
                    .where(
                        and_(
                            EventTable.start_datetime >= start_date,
                            EventTable.start_datetime <= end_date
                        )
                    )
                    .order_by(EventTable.start_datetime)
                )
                events = result.scalars().all()

                return [self._to_event_model(event) for event in events]
        except Exception as e:
            logger.error(f"日付範囲別イベント取得中にエラーが発生しました: {e}")
            raise Exception(f"日付範囲別イベント取得中にエラーが発生しました: {str(e)}")

    async def get_events_by_prefecture_and_date_range(
        self,
        prefecture: str,
        start_date: datetime,
        end_date: datetime,
        max_count: int = 100
    ) -> List[Event]:
        """都道府県と日付範囲でイベントをフィルタリング"""
        try:
            session = await get_db_session()
            async with session:
                result = await session.execute(
                    select(EventTable)
                    .where(
                        and_(
                            EventTable.prefecture == prefecture,
                            EventTable.start_datetime >= start_date,
                            EventTable.start_datetime <= end_date
                        )
                    )
                    .order_by(EventTable.start_datetime)
                    .limit(max_count)
                )
                events = result.scalars().all()

                return [self._to_event_model(event) for event in events]
        except Exception as e:
            logger.error(f"都道府県・日付範囲別イベント取得中にエラーが発生しました: {e}")
            raise Exception(f"都道府県・日付範囲別イベント取得中にエラーが発生しました: {str(e)}")

    async def get_upcoming_events_by_prefecture(
        self,
        prefecture: str,
        weeks_ahead_min: int = 1,
        weeks_ahead_max: int = 4,
        max_count: int = 100
    ) -> List[Event]:
        """指定された都道府県の今後のイベントを取得"""
        try:
            now = datetime.now()
            start_date = now + timedelta(weeks=weeks_ahead_min)
            end_date = now + timedelta(weeks=weeks_ahead_max)

            session = await get_db_session()
            async with session:
                result = await session.execute(
                    select(EventTable)
                    .where(
                        and_(
                            EventTable.prefecture == prefecture,
                            EventTable.start_datetime >= start_date,
                            EventTable.start_datetime <= end_date
                        )
                    )
                    .order_by(EventTable.start_datetime)
                    .limit(max_count)
                )
                events = result.scalars().all()
                logger.info(events)

                return [self._to_event_model(event) for event in events]
        except Exception as e:
            logger.error(f"今後のイベント取得中にエラーが発生しました: {e}")
            raise Exception(f"今後のイベント取得中にエラーが発生しました: {str(e)}")

    def _to_event_model(self, event_table: EventTable) -> Event:
        """EventTableオブジェクトをEventモデルに変換"""
        return Event(
            event_id=event_table.event_id,
            title=event_table.title,
            description=event_table.description,
            start_datetime=event_table.start_datetime,
            end_datetime=event_table.end_datetime,
            postal_code=event_table.postal_code,
            prefecture=event_table.prefecture,
            address_block=event_table.address_block,
            address_building=event_table.address_building,
            contact_name=event_table.contact_name,
            contact_phone=event_table.contact_phone,
            event_url=event_table.event_url,
            created_at=event_table.created_at,
            updated_at=event_table.updated_at
        )
