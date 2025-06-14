"""CloudSQL implementation of UserRepository."""
from typing import Optional, Dict, Any
import logging
import os

from sqlalchemy import select, Column, String, Date, Time, DateTime, Enum, CHAR, VARCHAR, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from google.cloud.sql.connector import Connector

from app.models.schemas import User, Gender, Weekday

logger = logging.getLogger(__name__)

Base = declarative_base()


class UserTable(Base):
    """ユーザーテーブルのORM定義"""
    __tablename__ = 'users'

    user_id = Column(CHAR(36), primary_key=True)
    last_name = Column(VARCHAR(64), nullable=False)
    first_name = Column(VARCHAR(64), nullable=False)
    last_name_kana = Column(VARCHAR(64), nullable=True)
    first_name_kana = Column(VARCHAR(64), nullable=True)
    postal_code = Column(CHAR(8), nullable=True)
    prefecture = Column(VARCHAR(40), nullable=True)
    address_block = Column(VARCHAR(100), nullable=True)
    address_building = Column(VARCHAR(100), nullable=True)
    phone_number = Column(VARCHAR(14), nullable=False)
    email = Column(VARCHAR(255), nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    birth_date = Column(Date, nullable=True)
    call_time = Column(Time, nullable=True)
    call_weekday = Column(Enum(Weekday), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class CloudSQLUserRepository:
    """CloudSQLを使用したユーザーリポジトリの実装"""

    def __init__(self, connection_string: Optional[str] = None):
        """
        CloudSQLユーザーリポジトリを初期化
        
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

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        指定されたIDのユーザーを取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            User: ユーザー情報、存在しない場合はNone
        """
        try:
            async with self.async_session() as session:
                result = await session.execute(
                    select(UserTable).where(UserTable.user_id == user_id)
                )
                user_table = result.scalar_one_or_none()
                
                if user_table is None:
                    logger.info(f"ユーザーが見つかりません: {user_id}")
                    return None
                
                return self._to_user_model(user_table)
                
        except Exception as e:
            logger.error(f"ユーザー取得中にエラーが発生しました: {e}")
            raise Exception(f"ユーザー取得中にエラーが発生しました: {str(e)}")

    def _to_user_model(self, user_table: UserTable) -> User:
        """UserTableオブジェクトをUserモデルに変換"""
        return User(
            user_id=user_table.user_id,
            last_name=user_table.last_name,
            first_name=user_table.first_name,
            last_name_kana=user_table.last_name_kana,
            first_name_kana=user_table.first_name_kana,
            postal_code=user_table.postal_code,
            prefecture=user_table.prefecture,
            address_block=user_table.address_block,
            address_building=user_table.address_building,
            phone_number=user_table.phone_number,
            email=user_table.email,
            gender=user_table.gender,
            birth_date=user_table.birth_date,
            call_time=user_table.call_time,
            call_weekday=user_table.call_weekday,
            created_at=user_table.created_at,
            updated_at=user_table.updated_at
        )

    async def close(self):
        """データベース接続を閉じる"""
        await self.engine.dispose()