from .db_connection import get_db_connection
from mysql.connector import Error

def get_user_info(user_id):
    """userIDをもとにユーザー情報を取得する"""
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # ユーザー情報を取得
        query = """
        SELECT 
            user_id,
            last_name,
            first_name,
            last_name_kana,
            first_name_kana,
            postal_code,
            prefecture,
            address_block,
            address_building,
            phone_number,
            email,
            gender,
            birth_date,
            call_time,
            call_weekday,
            created_at,
            updated_at
        FROM users 
        WHERE user_id = %s
        """
        cursor.execute(query, (user_id,))
        user_info = cursor.fetchone()
        
        if user_info:
            # 日時型を文字列に変換
            if user_info.get('birth_date'):
                user_info['birth_date'] = user_info['birth_date'].strftime('%Y-%m-%d')
            if user_info.get('call_time'):
                user_info['call_time'] = str(user_info['call_time'])
            if user_info.get('created_at'):
                user_info['created_at'] = user_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if user_info.get('updated_at'):
                user_info['updated_at'] = user_info['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return user_info
        else:
            return None
            
    except Error as e:
        print(f"ユーザー情報取得エラー: {e}")
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def test_get_user():
    """ユーザー情報取得のテスト"""
    # テスト用のダミーID（実際のIDに置き換えてテスト）
    test_user_id = "test-user-id"
    user_info = get_user_info(test_user_id)
    if user_info:
        print(f"ユーザー情報取得成功: {user_info}")
    else:
        print("ユーザーが見つかりませんでした") 