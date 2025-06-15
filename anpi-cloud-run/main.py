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
    --url=https://taskhandler-hkzk5xnm7q-uc.a.run.app/task-handler \
    --method=POST \
    --header=Content-Type:application/json \
    --body-content='{"message": "Direct from gcloud", "recipient_phone_number": "+819081729874"}'
```

or 

```bash
curl -X POST "https://taskhandler-hkzk5xnm7q-uc.a.run.app/enqueue-task" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Hello from Cloud Tasks!",
       "recipient_phone_number": "+819081729874",
       "delay_seconds": 0}'
```


"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from google.cloud import tasks_v2
from pydantic import BaseModel
from twilio.rest import Client

load_dotenv()

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 環境変数
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "my-test-project-462302")
LOCATION = os.environ.get("CLOUD_TASKS_LOCATION", "us-central1")
QUEUE_NAME = os.environ.get("CLOUD_TASKS_QUEUE", "my-queue")

ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_PHONE_NUMBER = os.environ["TWILIO_CALL_NUMBER"]

# Cloud Tasks クライアント
tasks_client = tasks_v2.CloudTasksClient()


class Message(BaseModel):
    message: str
    recipient_phone_number: str


class TaskRequest(BaseModel):
    message: str
    delay_seconds: Optional[int] = 0
    recipient_phone_number: str


class TaskResponse(BaseModel):
    task_name: str
    status: str
    scheduled_time: Optional[str] = None


@app.post("/task-handler")
async def task_handler(payload: Message):
    """Cloud Tasksから呼び出されるタスクハンドラー"""
    logger.info(
        f"Processing task to {payload.recipient_phone_number} with message: {payload.message}"
    )

    try:
        # Find your Account SID and Auth Token at twilio.com/console
        # and set the environment variables. See http://twil.io/secure
        client = Client(ACCOUNT_SID, AUTH_TOKEN)

        # As an example,
        call = client.calls.create(
            from_=TWILIO_PHONE_NUMBER,
            to=payload.recipient_phone_number,
            url="http://demo.twilio.com/docs/voice.xml",  # URL消したらどうなるか？
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
        payload = {
            "message": task_request.message,
            "recipient_phone_number": task_request.recipient_phone_number,
        }
        json_payload = json.dumps(payload).encode("utf-8")

        # HTTPリクエストを構築
        http_request = tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=task_url,
            headers={
                "Content-Type": "application/json",
            },
            oidc_token=tasks_v2.OidcToken(
                service_account_email="cloud-tasks-invoker@univac-aiagent.iam.gserviceaccount.com",
            ),
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


@app.post("/batch-enqueue")
async def batch_enqueue_tasks(batch_requests: list[TaskRequest]):
    """複数のタスクを一括でキューに追加"""
    results = []

    for i, task_req in enumerate(batch_requests):
        try:
            task_request = TaskRequest(
                message=f"Batch task {i+1}: {task_req.message}",
                recipient_phone_number=task_req.recipient_phone_number,
                delay_seconds=i * 10,  # 10秒間隔で実行
            )
            result = await enqueue_task(task_request)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to enqueue batch task {i+1}: {str(e)}")
            results.append(
                {"task_name": f"batch-task-{i+1}", "status": "failed", "error": str(e)}
            )

    return {"enqueued_tasks": results}


@app.get("/")
async def root():
    return {
        "message": "Task Handler Service",
        "endpoints": {
            "task_handler": "/task-handler",
            "enqueue_task": "/enqueue-task",
            "batch_enqueue": "/batch-enqueue",
        },
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
