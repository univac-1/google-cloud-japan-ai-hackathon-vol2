#!/usr/bin/env python3
"""
安否確認呼び出しスケジューラー - Cloud Run Job
Cloud Run Jobとしてバッチ処理を実行し、Cloud Tasksを使って将来の安否確認呼び出しをスケジュール
"""

import os
import sys
import logging
import time as time_module
from datetime import datetime, timedelta, time
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
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

def check_task_exists(client, project_id, location, queue_name, task_name):
    """指定されたタスクが既に存在するかチェック"""
    try:
        parent = client.queue_path(project_id, location, queue_name)
        
        # キューから全てのタスクを取得
        request = tasks_v2.ListTasksRequest(parent=parent)
        response = client.list_tasks(request)
        
        # タスク名をチェック
        full_task_name = f"{parent}/tasks/{task_name}"
        for task in response:
            if task.name == full_task_name:
                logger.debug(f"タスクが既に存在します: {task_name}")
                return True
        
        return False  # タスクが存在しない
    except Exception as e:
        logger.debug(f"タスク存在チェックでエラー: {str(e)}")
        return False  # エラーが発生した場合は存在しないものとして処理

def create_cloud_task(project_id, location, queue_name, schedule_time, target_url, task_name=None, schedule=None):
    """Cloud Tasksにタスクを作成する"""
    logger.info(f"Cloud Tasksにタスクを作成中: {task_name or 'unnamed-task'}")
    
    # Cloud Tasksクライアントを初期化
    client = tasks_v2.CloudTasksClient()
    
    # タスクが既に存在するかチェック
    if task_name and check_task_exists(client, project_id, location, queue_name, task_name):
        logger.warning(f"タスクが既に存在するためスキップします: {task_name}")
        return None
    
    # キューのパスを作成
    parent = client.queue_path(project_id, location, queue_name)
    
    # タスクの設定
    task = {
        'http_request': {
            'http_method': tasks_v2.HttpMethod.POST,
            'url': target_url,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Scheduled anpi call task',
                'timestamp': datetime.now().isoformat(),
                'task_name': task_name or 'unnamed-task',
                'user_info': schedule.get('user_info', {}) if schedule else {}
            }).encode()
        }
    }
    
    # 実行時刻を設定（Unix timestamp）
    if schedule_time:
        timestamp = timestamp_pb2.Timestamp()
        timestamp.FromDatetime(schedule_time)
        task['schedule_time'] = timestamp
    
    # タスク名を設定（オプション）
    if task_name:
        task['name'] = f"{parent}/tasks/{task_name}"
    
    try:
        # タスクを作成
        response = client.create_task(parent=parent, task=task)
        logger.info(f"タスクが正常に作成されました: {response.name}")
        return response
    except Exception as e:
        error_msg = str(e)
        
        # 409エラー（重複）の場合の処理
        if "409" in error_msg and "task with this name existed too recently" in error_msg:
            logger.warning(f"タスク名が重複しています。スキップします: {task_name}")
            return None
        else:
            logger.error(f"タスク作成でエラーが発生しました: {error_msg}")
            raise

def get_db_connection():
    """データベース接続を取得する"""
    try:
        # Cloud Run環境の判定 - Cloud Run JobsやCloud Run Servicesで動作中か判定
        is_cloud_run = (
            os.environ.get('K_SERVICE') is not None or  # Cloud Run Service
            os.environ.get('CLOUD_RUN_JOB') is not None or  # Cloud Run Job
            os.environ.get('K_CONFIGURATION') is not None  # Cloud Run (一般)
        )
        
        if is_cloud_run:
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
        
        # デバッグ情報：取得したユーザーの詳細をログ出力
        for user in users:
            logger.debug(f"ユーザー情報: ID={user['user_id']}, 名前={user['last_name']} {user['first_name']}, 曜日={user['call_weekday']}, 時刻={user['call_time']}")
        
        return users
        
    except Error as e:
        logger.error(f"ユーザー情報取得エラー: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def calculate_next_call_datetime(call_weekday, call_time):
    """次回の安否確認実行日時を計算する"""
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
    
    target_weekday = weekday_map[call_weekday]
    current_datetime = datetime.now()
    current_weekday = current_datetime.weekday()
    
    # 今日からの日数を計算
    days_until_target = (target_weekday - current_weekday) % 7
    
    # 今日が指定曜日で、かつ指定時刻がまだ過ぎていない場合は今日実行
    if days_until_target == 0:
        target_time = datetime.combine(current_datetime.date(), call_time)
        if target_time > current_datetime:
            return target_time
        else:
            # 今日の時刻は過ぎているので来週の同じ曜日
            days_until_target = 7
    
    # 指定曜日まで0日の場合は来週
    if days_until_target == 0:
        days_until_target = 7
    
    target_date = current_datetime.date() + timedelta(days=days_until_target)
    return datetime.combine(target_date, call_time)

def get_user_schedules():
    """ユーザーの安否確認スケジュールを取得する"""
    logger.info("ユーザーの安否確認スケジュールを生成中...")
    
    # データベースからユーザー情報を取得（モックは使用しない）
    users = get_users_from_db()
    logger.info(f"データベースからユーザー情報を取得しました: {len(users)}件")
    
    if not users:
        logger.warning("取得されたユーザーが0件です")
        return []
    
    schedules = []
    
    for user in users:
        try:
            next_call_datetime = calculate_next_call_datetime(
                user['call_weekday'], 
                user['call_time']
            )
            
            # 安否確認呼び出しのターゲットURL（実際のTwilioサービスのエンドポイント）
            target_url = os.environ.get('ANPI_CALL_URL', 'https://asia-northeast1-speech-assistant-openai-894704565810.asia-northeast1.run.app/webhook')
            
            schedule = {
                'id': user['user_id'],
                'name': f"anpi-call-{user['user_id'][:8]}",
                'schedule_time': next_call_datetime,
                'target_url': target_url,
                'user_info': {
                    'user_id': user['user_id'],
                    'name': f"{user['last_name']} {user['first_name']}",
                    'phone_number': user['phone_number']
                }
            }
            schedules.append(schedule)
            
            logger.debug(f"スケジュール生成: {user['last_name']} {user['first_name']} - {next_call_datetime}")
            
        except Exception as e:
            logger.error(f"ユーザー {user['user_id']} のスケジュール生成エラー: {e}")
            continue
    
    logger.info(f"生成したスケジュール数: {len(schedules)}")
    return schedules

def process_safety_check_schedules():
    """安否確認の予定を処理してCloud Tasksに登録"""
    logger.info("安否確認スケジュールの処理を開始")
    
    # 環境変数から設定を取得
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'unknown')
    location = os.environ.get('CLOUD_TASKS_LOCATION', 'asia-northeast1')
    queue_name = os.environ.get('CLOUD_TASKS_QUEUE', 'anpi-call-queue')
    
    logger.info(f"Cloud Tasks設定 - プロジェクト: {project_id}, 場所: {location}, キュー: {queue_name}")
    
    # DBからユーザーの安否確認スケジュールを取得
    schedules = get_user_schedules()
    
    created_tasks = []
    skipped_tasks = 0
    
    for schedule in schedules:
        try:
            logger.info(f"予定を処理中: {schedule['name']} (実行予定: {schedule['schedule_time']})")
            
            # タスク名を要件に従って生成: anpi-call-task-<ID>-<タスク実行予定日>
            schedule_date = schedule['schedule_time'].strftime('%Y%m%d-%H%M')
            user_id_short = schedule['id'][:8]  # ユーザーIDの最初の8文字
            task_name = f"anpi-call-task-{user_id_short}-{schedule_date}"
            
            logger.debug(f"生成されたタスク名: {task_name}")
            
            # Cloud Tasksにタスクを作成
            response = create_cloud_task(
                project_id=project_id,
                location=location,
                queue_name=queue_name,
                schedule_time=schedule['schedule_time'],
                target_url=schedule['target_url'],
                task_name=task_name,
                schedule=schedule
            )
            
            if response:
                created_tasks.append({
                    'schedule_id': schedule['id'],
                    'task_name': response.name,
                    'schedule_time': schedule['schedule_time']
                })
                logger.info(f"タスク登録完了: {task_name}")
            else:
                skipped_tasks += 1
                logger.info(f"タスクをスキップしました（既存または重複）: {task_name}")
            
        except Exception as e:
            logger.error(f"スケジュール処理エラー (ID: {schedule['id']}): {str(e)}")
            continue
    
    logger.info(f"Cloud Tasksタスク処理完了: 新規作成={len(created_tasks)}件, スキップ={skipped_tasks}件")
    return created_tasks

def main():
    """メイン処理"""
    logger.info("=== 安否確認呼び出しスケジューラー バッチ処理開始 ===")
    
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
    
    # バッチ処理のシミュレーション
    logger.info("バッチ処理を実行中...")
    logger.debug("開発環境モードで実行中")
    
    # Cloud Tasksを使った安否確認スケジュール処理
    try:
        created_tasks = process_safety_check_schedules()
        logger.info(f"安否確認スケジュール処理完了: {len(created_tasks)}件のタスクを登録")
        
        # 作成されたタスクの詳細をログ出力
        for task in created_tasks:
            logger.debug(f"登録タスク: {task}")
            
    except Exception as e:
        logger.error(f"安否確認スケジュール処理でエラーが発生: {str(e)}")
        return 1
    
    # 処理のシミュレーション（3回のステップ）
    logger.info("追加のバッチ処理を実行中...")
    for i in range(3):
        logger.info(f"処理中... {i+1}/3")
        logger.debug(f"ステップ {i+1} の詳細処理を実行")
        time_module.sleep(1)
    
    # 成功メッセージ
    logger.info("バッチ処理が正常に完了しました")
    logger.info("=== 安否確認呼び出しスケジューラー バッチ処理終了 ===")
    
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