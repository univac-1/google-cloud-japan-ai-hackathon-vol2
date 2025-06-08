#!/usr/bin/env python3
"""
安否確認呼び出しスケジューラー - Cloud Run Job
Cloud Run Jobとしてバッチ処理を実行し、Cloud Tasksを使って将来の安否確認呼び出しをスケジュール
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import time
import json
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

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

def create_cloud_task(project_id, location, queue_name, schedule_time, target_url, task_name=None):
    """Cloud Tasksにタスクを作成する"""
    logger.info(f"Cloud Tasksにタスクを作成中: {task_name or 'unnamed-task'}")
    
    # Cloud Tasksクライアントを初期化
    client = tasks_v2.CloudTasksClient()
    
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
                'message': 'Scheduled task execution',
                'timestamp': datetime.now().isoformat(),
                'task_name': task_name or 'unnamed-task'
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
        logger.error(f"タスク作成でエラーが発生しました: {str(e)}")
        raise

def get_mock_schedules():
    """モックの予定データを取得（将来的にはDBから取得予定）"""
    logger.info("モック予定データを取得中...")
    
    # サンプルの予定データ（将来的にはDBから取得）
    current_time = datetime.now()
    schedules = [
        {
            'id': 1,
            'name': 'morning-safety-check',
            'schedule_time': current_time + timedelta(minutes=2),
            'target_url': 'https://httpbin.org/post'  # テスト用のエンドポイント
        },
        {
            'id': 2,
            'name': 'afternoon-safety-check',
            'schedule_time': current_time + timedelta(minutes=5),
            'target_url': 'https://httpbin.org/post'  # テスト用のエンドポイント
        },
        {
            'id': 3,
            'name': 'evening-safety-check',
            'schedule_time': current_time + timedelta(minutes=10),
            'target_url': 'https://httpbin.org/post'  # テスト用のエンドポイント
        }
    ]
    
    logger.info(f"取得した予定件数: {len(schedules)}")
    return schedules

def process_safety_check_schedules():
    """安否確認の予定を処理してCloud Tasksに登録"""
    logger.info("安否確認スケジュールの処理を開始")
    
    # 環境変数から設定を取得
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'unknown')
    location = os.environ.get('CLOUD_TASKS_LOCATION', 'asia-northeast1')
    queue_name = os.environ.get('CLOUD_TASKS_QUEUE', 'anpi-call-queue')
    
    logger.info(f"Cloud Tasks設定 - プロジェクト: {project_id}, 場所: {location}, キュー: {queue_name}")
    
    # モック予定データを取得
    schedules = get_mock_schedules()
    
    created_tasks = []
    for schedule in schedules:
        try:
            logger.info(f"予定を処理中: {schedule['name']} (実行予定: {schedule['schedule_time']})")
            
            # Cloud Tasksにタスクを作成
            task_name = f"{schedule['name']}-{int(schedule['schedule_time'].timestamp())}"
            response = create_cloud_task(
                project_id=project_id,
                location=location,
                queue_name=queue_name,
                schedule_time=schedule['schedule_time'],
                target_url=schedule['target_url'],
                task_name=task_name
            )
            
            created_tasks.append({
                'schedule_id': schedule['id'],
                'task_name': response.name,
                'schedule_time': schedule['schedule_time']
            })
            
            logger.info(f"タスク登録完了: {schedule['name']}")
            
        except Exception as e:
            logger.error(f"スケジュール処理エラー (ID: {schedule['id']}): {str(e)}")
            continue
    
    logger.info(f"Cloud Tasksタスク登録完了: {len(created_tasks)}件")
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
    
    # 処理のシミュレーション（5回のステップ）
    logger.info("追加のバッチ処理を実行中...")
    for i in range(3):  # 短縮して3回に変更
        logger.info(f"処理中... {i+1}/3")
        logger.debug(f"ステップ {i+1} の詳細処理を実行")
        time.sleep(1)
    
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