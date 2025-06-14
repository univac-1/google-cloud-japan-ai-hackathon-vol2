"""CloudSQL implementation of UserRepository."""
from typing import Optional
import logging
from sqlalchemy import select

from app.models.schemas import User
from app.database import get_db_session, UserTable

logger = logging.getLogger(__name__)


class CloudSQLUserRepository:
    """
    CloudSQLを使用したユーザーリポジトリの実装

    データベース接続は分離され、ビジネスロジックに集中
    """

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        ユーザーIDでユーザー情報を取得

        Args:
            user_id: ユーザーID

        Returns:
            User: ユーザー情報、見つからない場合はNone
        """
        try:
            session = await get_db_session()
            async with session:
                stmt = select(UserTable).where(UserTable.user_id == user_id)
                result = await session.execute(stmt)
                user_row = result.scalar_one_or_none()

                if user_row is None:
                    logger.warning(f"User not found: {user_id}")
                    return None

                return self._to_user_model(user_row)

        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {str(e)}")
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
