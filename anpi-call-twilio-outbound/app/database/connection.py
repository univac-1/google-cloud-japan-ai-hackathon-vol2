"""
データベース接続管理

Spring BootのDataSourceに相当する機能を提供
"""
import os
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from google.cloud.sql.connector import Connector

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """データベース接続とセッション管理を担当するクラス"""
    
    _instance: Optional['DatabaseConnection'] = None
    _engine = None
    _session_factory = None
    _connector = None
    _initialized = False
    
    def __new__(cls):
        """シングルトンパターンでインスタンス管理"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """データベース接続の初期化（遅延初期化）"""
        pass
    
    async def initialize(self):
        """データベース接続の初期化（非同期）"""
        if not self._initialized:
            await self._initialize_connection()
            self._initialized = True
    
    async def _initialize_connection(self):
        """CloudSQL接続の初期化"""
        # 環境変数から設定を取得
        db_user = os.getenv('DEFAULT_USER', 'default')
        db_password = os.getenv('DEFAULT_PASSWORD', '')
        db_name = os.getenv('DB_NAME', 'default')
        instance_connection_name = os.getenv('CLOUD_SQL_CONNECTION_STRING')
        
        if not instance_connection_name:
            raise ValueError("CLOUD_SQL_CONNECTION_STRING environment variable is required")
        
        logger.info(f"Initializing CloudSQL connection to: {instance_connection_name}")
        
        # Cloud SQL Language Connectorを使用
        self._connector = Connector()
        
        def getconn():
            """CloudSQL接続用のコネクター関数"""
            conn = self._connector.connect(
                instance_connection_name,
                "pymysql",
                user=db_user,
                password=db_password,
                db=db_name,
            )
            return conn
        
        # 非同期エンジンの作成
        self._engine = create_async_engine(
            "mysql+aiomysql://",
            creator=getconn,
            echo=False,  # SQLログ出力（開発時はTrueに変更可能）
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,  # 1時間でコネクションをリサイクル
        )
        
        # セッションファクトリーの作成
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("CloudSQL connection initialized successfully")
    
    @property
    def engine(self):
        """SQLAlchemyエンジンを取得"""
        return self._engine
    
    async def get_session(self) -> AsyncSession:
        """新しいデータベースセッションを取得"""
        if not self._initialized:
            await self.initialize()
        if self._session_factory is None:
            raise RuntimeError("Database connection not initialized")
        return self._session_factory()
    
    async def close(self):
        """データベース接続をクローズ"""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database engine disposed")
        
        if self._connector:
            await self._connector.close_async()
            logger.info("CloudSQL connector closed")
    
    async def health_check(self) -> bool:
        """データベース接続の健全性チェック"""
        try:
            session = await self.get_session()
            async with session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# グローバルインスタンス
db_connection = DatabaseConnection()


async def get_db_session() -> AsyncSession:
    """
    データベースセッションを取得するヘルパー関数
    FastAPIの依存性注入で使用可能
    """
    return await db_connection.get_session()