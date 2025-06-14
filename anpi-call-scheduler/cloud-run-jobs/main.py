#!/usr/bin/env python3
"""
安否確認呼び出しスケジューラー - Cloud Run Job
データベースの設定に基づいて現在時刻に実行すべき安否確認呼び出しを即座に実行する
"""

import os
import sys
import logging
from datetime import datetime, timedelta, time
import json
from google.cloud import tasks_v2
import mysql.connector
from mysql.connector import Error

def setup_logging():
    """ログ設定を初期化"""
    log_level = os.environ.get('LOG_LEVEL', 'info').upper()
    
    # ログレベルの設定
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    level = level_map.get(log_level, logging.INFO)
    
    # 開発環境向けの詳細ログフォーマット
    format_str = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def create_cloud_task(project_id, location, queue_name, target_url, task_name=None, user_info=None):
    """Cloud Tasksに即時実行タスクを作成する
    
    Args:
        project_id: Google Cloud Project ID
        location: Cloud Tasks location
        queue_name: Cloud Tasks queue name
        target_url: タスク実行先URL
        task_name: タスク名（オプション）
        user_info: ユーザー情報（オプション）
    """
    logger.info(f"Cloud Tasksに即時実行タスクを作成中: {task_name or 'unnamed-task'}")
    
    # Cloud Tasksクライアントを初期化
    client = tasks_v2.CloudTasksClient()
    
    # キューのパスを作成
    parent = client.queue_path(project_id, location, queue_name)
    
    # タスクの設定
    task_payload = {
        'message': 'Immediate anpi call task',
        'timestamp': datetime.now().isoformat(),
        'task_name': task_name or 'unnamed-task',
        'user_info': user_info or {},
        'execution_type': '即時実行'
    }
    
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': target_url,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(task_payload).encode()
        }
    }
    
    # タスク名を設定（オプション）
    if task_name:
        task['name'] = f"{parent}/tasks/{task_name}"
    
    try:
        # タスクを作成（即時実行）
        response = client.create_task(parent=parent, task=task)
        logger.info(f"即時実行タスクが正常に作成されました: {response.name}")
        return response
    except Exception as e:
        logger.error(f"即時実行タスク作成でエラーが発生しました: {str(e)}")
        raise

def get_db_connection():
    """データベース接続を取得する"""
    try:
        # Cloud SQL接続の判定
        use_cloud_sql = os.environ.get('USE_CLOUD_SQL', 'false').lower() == 'true'
        is_cloud_run_service = os.environ.get('K_SERVICE') is not None
        is_cloud_run_job = os.environ.get('IS_CLOUD_RUN_JOB', 'false').lower() == 'true'
        
        if use_cloud_sql or is_cloud_run_service or is_cloud_run_job:
            # Cloud SQL Proxyソケット接続（Cloud Run環境）
            unix_socket = f"/cloudsql/{os.environ.get('GOOGLE_CLOUD_PROJECT', 'univac-aiagent')}:asia-northeast1:cloudsql-01"
            logger.info(f"Cloud SQL接続を使用: {unix_socket}")
            connection = mysql.connector.connect(
                unix_socket=unix_socket,
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                auth_plugin='mysql_native_password',
                autocommit=True,
                sql_mode='TRADITIONAL'
            )
        else:
            # 通常のTCP接続（開発環境など）
            db_host = os.environ.get('DB_HOST', '127.0.0.1')
            logger.info(f"TCP接続を使用: {db_host}")
            connection = mysql.connector.connect(
                host=db_host,
                port=int(os.environ.get('DB_PORT', '3306')),
                user=os.environ.get('DB_USER', 'default'),
                password=os.environ.get('DB_PASSWORD'),
                database=os.environ.get('DB_NAME', 'default'),
                charset='utf8mb4',
                auth_plugin='mysql_native_password',
                autocommit=True
            )
        return connection
    except Error as e:
        logger.error(f"データベース接続エラー: {e}")
        raise

def get_users_from_db():
    """DBからユーザー情報を取得する"""
    logger.info("データベースからユーザー情報を取得中...")
    
    connection = None
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 電話希望時刻と曜日が設定されているユーザーを取得
        query = """
        SELECT user_id, last_name, first_name, phone_number, 
               call_time, call_weekday
        FROM users 
        WHERE call_time IS NOT NULL 
          AND call_weekday IS NOT NULL
        """
        
        cursor.execute(query)
        users = cursor.fetchall()
        
        logger.info(f"取得したユーザー数: {len(users)}")
        return users
        
    except Error as e:
        logger.error(f"ユーザー情報取得エラー: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()



def should_call_now(call_weekday, call_time, tolerance_minutes=5):
    """現在時刻に基づいて即座に電話をかけるべきかどうかを判定する
    
    Args:
        call_weekday: 指定曜日 ('mon', 'tue', etc.)
        call_time: 指定時刻 (time object or timedelta)
        tolerance_minutes: 許容時間（分）。指定時刻の前後この時間内なら実行対象
    
    Returns:
        bool: 今すぐ電話をかけるべきならTrue
    """
    # 曜日のマッピング
    weekday_map = {
        'sun': 6, 'mon': 0, 'tue': 1, 'wed': 2,
        'thu': 3, 'fri': 4, 'sat': 5
    }
    
    # call_timeがtimedeltaの場合、timeオブジェクトに変換
    if isinstance(call_time, timedelta):
        total_seconds = int(call_time.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        call_time = time(hours, minutes, seconds)
    
    current_datetime = datetime.now()
    current_weekday = current_datetime.weekday()
    current_time = current_datetime.time()
    
    target_weekday = weekday_map.get(call_weekday)
    if target_weekday is None:
        logger.warning(f"不正な曜日指定: {call_weekday}")
        return False
    
    # 今日が指定曜日でない場合は即時実行しない
    if current_weekday != target_weekday:
        logger.debug(f"今日({current_weekday})は指定曜日({target_weekday})ではありません")
        return False
    
    # 指定時刻をdatetimeに変換
    target_datetime = datetime.combine(current_datetime.date(), call_time)
    
    # 現在時刻と指定時刻の差分を計算（秒単位）
    time_diff_seconds = (current_datetime - target_datetime).total_seconds()
    time_diff_minutes = time_diff_seconds / 60
    
    logger.debug(f"時刻差分: {time_diff_minutes:.2f}分 (現在: {current_datetime.time()}, 指定: {call_time})")
    
    # 許容時間内で実行対象かチェック
    # 指定時刻の tolerance_minutes 分前から tolerance_minutes 分後まで
    if -tolerance_minutes <= time_diff_minutes <= tolerance_minutes:
        logger.debug(f"許容時間内({tolerance_minutes}分): 即時実行対象")
        return True
    
    logger.debug(f"許容時間外: 即時実行対象外")
    return False

def get_immediate_call_users():
    """現在時刻に基づいて即座に電話をかけるべきユーザーを取得する"""
    logger.info("即時実行対象ユーザーを確認中...")
    
    # 即時実行の許容時間を環境変数から取得（デフォルト5分）
    tolerance_minutes = int(os.environ.get('IMMEDIATE_CALL_TOLERANCE_MINUTES', '5'))
    logger.info(f"即時実行許容時間: {tolerance_minutes}分")
    
    # データベースからユーザー情報を取得
    users = get_users_from_db()
    immediate_users = []
    
    for user in users:
        try:
            if should_call_now(user['call_weekday'], user['call_time'], tolerance_minutes):
                immediate_users.append(user)
                logger.info(f"即時実行対象: {user['last_name']} {user['first_name']} (曜日: {user['call_weekday']}, 時刻: {user['call_time']})")
        except Exception as e:
            logger.error(f"ユーザー {user['user_id']} の即時実行判定エラー: {e}")
            continue
    
    logger.info(f"即時実行対象ユーザー数: {len(immediate_users)}")
    return immediate_users

def create_immediate_tasks():
    """即時実行すべきユーザーのタスクを作成する"""
    logger.info("即時実行タスクの作成を開始")
    
    # 環境変数から設定を取得
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'unknown')
    location = os.environ.get('CLOUD_TASKS_LOCATION', 'asia-northeast1')
    queue_name = os.environ.get('CLOUD_TASKS_QUEUE', 'anpi-call-queue')
    
    # 即時実行対象ユーザーを取得
    immediate_users = get_immediate_call_users()
    
    if not immediate_users:
        logger.info("即時実行対象のユーザーはいません")
        return []
    
    created_tasks = []
    current_time = datetime.now()
    
    for user in immediate_users:
        try:
            # 安否確認呼び出しのターゲットURL
            target_url = os.environ.get('ANPI_CALL_URL', 'https://asia-northeast1-speech-assistant-openai-894704565810.asia-northeast1.run.app/webhook')
            
            # 即時実行タスクの名前（タイムスタンプ付き）
            task_name = f"anpi-call-immediate-{user['user_id'][:8]}-{int(current_time.timestamp())}"
            
            # ユーザー情報の作成
            user_info = {
                'user_id': user['user_id'],
                'name': f"{user['last_name']} {user['first_name']}",
                'phone_number': user['phone_number']
            }
            
            logger.info(f"即時タスク作成中: {user['last_name']} {user['first_name']}")
            
            # Cloud Tasksにタスクを作成（即時実行）
            response = create_cloud_task(
                project_id=project_id,
                location=location,
                queue_name=queue_name,
                target_url=target_url,
                task_name=task_name,
                user_info=user_info
            )
            
            created_tasks.append({
                'user_id': user['user_id'],
                'task_name': response.name,
                'execution_time': current_time,
                'user_name': f"{user['last_name']} {user['first_name']}"
            })
            
            logger.info(f"即時タスク作成完了: {task_name}")
            
        except Exception as e:
            logger.error(f"即時タスク作成エラー (ユーザーID: {user['user_id']}): {str(e)}")
            continue
    
    logger.info(f"即時実行タスク作成完了: {len(created_tasks)}件")
    return created_tasks

def main():
    """メイン処理"""
    logger.info("=== 安否確認呼び出しスケジューラー 即時実行処理開始 ===")
    
    # 環境変数の確認
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'unknown')
    job_name = os.environ.get('CLOUD_RUN_JOB', 'unknown')
    execution_id = os.environ.get('CLOUD_RUN_EXECUTION', 'unknown')
    environment = os.environ.get('ENVIRONMENT', 'development')
    
    logger.info(f"プロジェクトID: {project_id}")
    logger.info(f"ジョブ名: {job_name}")
    logger.info(f"実行ID: {execution_id}")
    logger.info(f"環境: {environment}")
    
    # 現在の時刻を表示
    current_time = datetime.now().isoformat()
    logger.info(f"実行時刻: {current_time}")
    
    # 即時実行処理
    logger.info("=== 即時実行対象者の処理を開始 ===")
    immediate_tasks_count = 0
    try:
        immediate_tasks = create_immediate_tasks()
        immediate_tasks_count = len(immediate_tasks)
        logger.info(f"即時実行対象者処理完了: {immediate_tasks_count}件のタスクを作成")
        
        # 即時実行タスクの詳細をログ出力
        for task in immediate_tasks:
            logger.info(f"作成タスク: {task}")
            
    except Exception as e:
        logger.error(f"即時実行対象者処理でエラーが発生: {str(e)}")
        return 1
    
    # 処理完了メッセージ
    logger.info("=== 即時実行処理が正常に完了しました ===")
    logger.info(f"作成タスク数: {immediate_tasks_count}件")
    logger.info("=== 安否確認呼び出しスケジューラー 即時実行処理終了 ===")
    
    return 0

if __name__ == "__main__":
    """Cloud Run Jobとしてバッチ処理を実行"""
    try:
        logger.info("Cloud Run Jobとしてバッチ処理を開始")
        
        # バッチ処理を実行
        result = main()
        
        if result == 0:
            logger.info("Cloud Run Jobバッチ処理が正常に完了しました")
            sys.exit(0)
        else:
            logger.error("Cloud Run Jobバッチ処理でエラーが発生しました")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Cloud Run Jobでエラーが発生: {str(e)}")
        sys.exit(1)