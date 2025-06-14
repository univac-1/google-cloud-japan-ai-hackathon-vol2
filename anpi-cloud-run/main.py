"""

## Cloud run deploy

```bash
gcloud run deploy taskhandler --source . --platform managed --region us-central1 --allow-unauthenticated
```

## Cloud task setting

Create tasks with the name of `my-queue`.

```bash
gcloud tasks queues create my-queue --location=us-central1
```

Check the generated tasks.

```bash
gcloud tasks queues describe my-queue --location=us-central1
```

Submit a task.

```bash
gcloud tasks create-http-task my-task-1 \
    --queue=my-queue \
    --location=us-central1 \
    --url=https://taskhandler-hsr7mrfkca-uc.a.run.app/task-handler \
    --method=POST \
    --header=Content-Type:application/json \
    --body-content='{"message": "Direct from gcloud"}'
```

or 

```bash
curl -X POST "https://taskhandler-hsr7mrfkca-uc.a.run.app/enqueue-task" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hello from Cloud Tasks!",
       "delay_seconds": 0
```


"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from google.cloud import tasks_v2
from pydantic import BaseModel
from twilio.rest import Client

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 環境変数
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-test-project-462302")
LOCATION = os.environ.get("CLOUD_TASKS_LOCATION", "us-central1")
QUEUE_NAME = os.environ.get("CLOUD_TASKS_QUEUE", "my-queue")

# Cloud Tasks クライアント
tasks_client = tasks_v2.CloudTasksClient()


class Message(BaseModel):
    message: str


class TaskRequest(BaseModel):
    message: str
    delay_seconds: Optional[int] = 0


class TaskResponse(BaseModel):
    task_name: str
    status: str
    scheduled_time: Optional[str] = None


@app.post("/task-handler")
async def task_handler(payload: Message):
    """Cloud Tasksから呼び出されるタスクハンドラー"""
    logger.info(f"Processing task with message: {payload.message}")

    # ここでタスクの実際の処理を行う
    # 例: データベース更新、外部API呼び出し、ファイル処理など

    time.sleep(2)
    # curlで投げる場合は以下を利用
    # import subprocess

    try:

        # Find your Account SID and Auth Token at twilio.com/console
        # and set the environment variables. See http://twil.io/secure
        account_sid = os.environ["TWILIO_ACCOUNT_SID"]
        auth_token = os.environ["TWILIO_AUTH_TOKEN"]
        call_number_from = "+18313183757"  # FIXME:: hard code
        client = Client(account_sid, auth_token)

        # FIXME :: hard code
        call = client.calls.create(
            from_=call_number_from,
            to="+819081729874",
            url="http://demo.twilio.com/docs/voice.xml",
        )

        print(call.sid)

    except:
        logger.warning("CALL FAILED!!")
    logger.info(f"Task completed successfully: {payload.message}")

    return {
        "status": "completed",
        "message": f"Successfully processed: {payload.message}",
        "processed_at": datetime.utcnow().isoformat(),
    }


@app.post("/enqueue-task", response_model=TaskResponse)
async def enqueue_task(task_request: TaskRequest):
    """新しいタスクをCloud Tasksキューに追加"""
    try:
        # キューのパスを構築
        queue_path = tasks_client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)

        # Cloud Runサービスのエンドポイント
        current_url = os.environ.get(
            "SERVICE_URL", "https://taskhandler-hsr7mrfkca-uc.a.run.app"
        )
        task_url = f"{current_url}/task-handler"

        # ペイロードを準備
        payload = {"message": task_request.message}
        json_payload = json.dumps(payload).encode("utf-8")

        # HTTPリクエストを構築
        http_request = tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=task_url,
            headers={"Content-Type": "application/json"},
            body=json_payload,
        )

        # タスクを構築
        task = tasks_v2.Task(http_request=http_request)

        # 遅延実行の場合はスケジュール時間を設定
        scheduled_time = None
        if task_request.delay_seconds > 0:
            from google.protobuf import timestamp_pb2

            schedule_time = datetime.utcnow() + timedelta(
                seconds=task_request.delay_seconds
            )
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(schedule_time)
            task.schedule_time = timestamp
            scheduled_time = schedule_time.isoformat()

        # タスクを作成
        response = tasks_client.create_task(parent=queue_path, task=task)

        logger.info(f"≈: {response.name}")

        return TaskResponse(
            task_name=response.name, status="enqueued", scheduled_time=scheduled_time
        )

    except Exception as e:
        logger.error(f"Failed to enqueue task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to enqueue task: {str(e)}")


@app.get("/")
async def root():
    return {
        "message": "Task Handler Service",
        "endpoints": {
            "task_handler": "/task-handler",
            "enqueue_task": "/enqueue-task",
        },
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
