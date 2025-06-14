"""CloudSQL implementation of EventRepository."""
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import os

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, Text, CHAR, TIMESTAMP
from google.cloud.sql.connector import Connector

from app.models.schemas import Event

logger = logging.getLogger(__name__)

Base = declarative_base()


class EventTable(Base):
    """イベントテーブルのORM定義"""
    __tablename__ = 'events'

    event_id = Column(CHAR(36), primary_key=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    postal_code = Column(CHAR(8), nullable=True)
    prefecture = Column(String(40), nullable=True)
    address_block = Column(String(100), nullable=True)
    address_building = Column(String(100), nullable=True)
    contact_name = Column(String(120), nullable=True)
    contact_phone = Column(String(14), nullable=True)
    event_url = Column(String(2083), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class CloudSQLEventRepository:
    """CloudSQLを使用したイベントリポジトリの実装"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        CloudSQLイベントリポジトリを初期化
        
        Args:
            connection_string: CloudSQL接続文字列
                例: "mysql+asyncmy://user:password@host:port/dbname"
        """
        if connection_string is None:
            # Cloud SQL Language Connectorを使用
            db_user = os.getenv('DEFAULT_USER', 'default')
            db_password = os.getenv('DEFAULT_PASSWORD', '')
            db_name = os.getenv('DB_NAME', 'default')
            instance_connection_name = os.getenv('CLOUD_SQL_CONNECTION_STRING')
            
            if instance_connection_name:
                # Cloud SQL Language Connectorを使用してカスタムcreator関数を作成
                connector = Connector()
                
                def getconn():
                    conn = connector.connect(
                        instance_connection_name,
                        "pymysql",
                        user=db_user,
                        password=db_password,
                        db=db_name,
                    )
                    return conn
                
                self.engine = create_async_engine(
                    "mysql+aiomysql://",
                    creator=getconn,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10
                )
            else:
                # フォールバック（開発環境など）
                db_host = os.getenv('DB_HOST', '127.0.0.1')
                db_port = os.getenv('DB_PORT', '3306')
                connection_string = f"mysql+aiomysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                
                self.engine = create_async_engine(
                    connection_string,
                    echo=False,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10
                )
        else:
            # 明示的に接続文字列が提供された場合
            self.engine = create_async_engine(
                connection_string,
                echo=False,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
        
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_all_events(self) -> List[Event]:
        """全てのイベントを取得"""
        try:
            async with self.async_session() as session:
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
            async with self.async_session() as session:
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
            async with self.async_session() as session:
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
            async with self.async_session() as session:
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
            
            async with self.async_session() as session:
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

    async def close(self):
        """データベース接続を閉じる"""
        await self.engine.dispose()