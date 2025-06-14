# システム構造図

本ドキュメントでは、安否確認呼び出しスケジューラー（バッチ処理システム）の構造をMermaid図で記載します。

## バッチ処理システム構成

```mermaid
graph TB
    %% 開発・デプロイフロー
    DEV[開発者]
    REPO[Gitリポジトリ<br/>このリポジトリ]
    
    %% Cloud Build
    CB[Cloud Build<br/>cloudbuild.yaml]
    
    %% Container Registry
    CR[Container Registry<br/>Dockerイメージ]
    
    %% Cloud Run Jobs
    CRJ[Cloud Run Jobs<br/>anpi-call-scheduler]
    
    %% Cloud Scheduler
    CS[Cloud Scheduler<br/>定時実行]
    
    %% ログ・監視
    CL[Cloud Logging]
    
    %% デプロイフロー
    DEV -->|git push| REPO
    REPO -->|./deploy.sh| CB
    CB -->|Dockerfile| CR
    CB -->|gcloud run jobs deploy| CRJ
    
    %% 実行フロー
    CS -->|HTTP Trigger| CRJ
    CRJ -->|Pull Image| CR
    CRJ -->|main.py実行| CL
    
    %% ファイル構成表示
    subgraph "リポジトリ構成"
        FILES[main.py<br/>Dockerfile<br/>requirements.txt<br/>cloudbuild.yaml<br/>deploy.sh<br/>job.yaml<br/>scheduler.yaml<br/>.env]
    end
    
    REPO --> FILES
    
    %% スタイリング
    classDef gcp fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    classDef repo fill:#34a853,stroke:#333,stroke-width:2px,color:#fff
    classDef user fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    
    class CB,CR,CRJ,CS,CL gcp
    class REPO,FILES repo
    class DEV user
```

## バッチ処理実行フロー

```mermaid
flowchart TD
    START([処理開始])
    INIT[ログ設定初期化<br/>setup_logging()]
    ENV[環境変数取得<br/>PROJECT_ID, JOB_NAME等]
    LOG_INFO[実行情報ログ出力<br/>プロジェクトID, 環境等]
    BATCH[バッチ処理シミュレーション<br/>5ステップの繰り返し処理]
    SUCCESS[成功ログ出力]
    END([処理終了<br/>exit_code=0])
    ERROR[例外処理<br/>エラーログ出力]
    FAIL([処理失敗<br/>exit_code=1])
    
    START --> INIT
    INIT --> ENV
    ENV --> LOG_INFO
    LOG_INFO --> BATCH
    BATCH --> SUCCESS
    SUCCESS --> END
    
    %% エラーハンドリング
    INIT -.->|例外| ERROR
    ENV -.->|例外| ERROR
    LOG_INFO -.->|例外| ERROR
    BATCH -.->|例外| ERROR
    ERROR --> FAIL
    
    %% スタイリング
    classDef process fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef endpoint fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef error fill:#ffebee,stroke:#d32f2f,stroke-width:2px
    
    class INIT,ENV,LOG_INFO,BATCH,SUCCESS process
    class START,END endpoint
    class ERROR,FAIL error
```

## 安否確認スケジューラー詳細処理フロー

```mermaid
flowchart TD
    START([Cloud Run Job開始])
    INIT[環境設定・ログ初期化]
    
    subgraph "データベース処理"
        DB_CONN[Cloud SQL接続<br/>Unix Socket/TCP]
        DB_QUERY[usersテーブル照会<br/>call_time, call_weekday]
        DB_FETCH[ユーザー情報取得<br/>phone_number, user_id]
    end
    
    subgraph "スケジュール計算"
        CALC_START[各ユーザー処理開始]
        WEEKDAY_MAP[曜日マッピング<br/>mon:0, tue:1, ...sun:6]
        NEXT_DATETIME[次回実行日時計算<br/>現在時刻+曜日オフセット]
        TASK_NAME[タスク名生成<br/>anpi-call-task-{ID}-{DATE}]
    end
    
    subgraph "Cloud Tasks登録"
        TASK_CHECK[既存タスク重複チェック]
        CREATE_TASK[新規タスク作成]
        TASK_CONFIG[タスク設定<br/>HTTP POST, Target URL]
        SCHEDULE_TIME[実行時刻設定<br/>Unix Timestamp]
    end
    
    subgraph "外部システム連携"
        TARGET_URL[安否確認システム<br/>Twilioサービス]
        WEBHOOK[Webhook呼び出し<br/>ユーザー情報付き]
    end
    
    RESULT[処理結果ログ出力<br/>新規作成/スキップ件数]
    END([処理完了])
    ERROR[エラーハンドリング]
    
    START --> INIT
    INIT --> DB_CONN
    DB_CONN --> DB_QUERY
    DB_QUERY --> DB_FETCH
    DB_FETCH --> CALC_START
    
    CALC_START --> WEEKDAY_MAP
    WEEKDAY_MAP --> NEXT_DATETIME
    NEXT_DATETIME --> TASK_NAME
    TASK_NAME --> TASK_CHECK
    
    TASK_CHECK -->|新規| CREATE_TASK
    TASK_CHECK -->|重複| RESULT
    CREATE_TASK --> TASK_CONFIG
    TASK_CONFIG --> SCHEDULE_TIME
    SCHEDULE_TIME --> TARGET_URL
    TARGET_URL --> WEBHOOK
    WEBHOOK --> RESULT
    
    RESULT --> END
    
    %% エラーハンドリング
    DB_CONN -.->|接続エラー| ERROR
    DB_QUERY -.->|SQLエラー| ERROR  
    CREATE_TASK -.->|APIエラー| ERROR
    ERROR --> END
    
    %% スタイリング
    classDef database fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    classDef calculation fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    classDef tasks fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
    classDef external fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
    classDef process fill:#607D8B,stroke:#333,stroke-width:2px,color:#fff
    classDef endpoint fill:#F44336,stroke:#333,stroke-width:2px,color:#fff
    
    class DB_CONN,DB_QUERY,DB_FETCH database
    class CALC_START,WEEKDAY_MAP,NEXT_DATETIME,TASK_NAME calculation
    class TASK_CHECK,CREATE_TASK,TASK_CONFIG,SCHEDULE_TIME tasks
    class TARGET_URL,WEBHOOK external
    class INIT,RESULT process
    class START,END,ERROR endpoint
```

## データフロー構成図

```mermaid
graph TB
    subgraph "定時実行基盤"
        CS[Cloud Scheduler<br/>毎時0分実行<br/>Cron: 0 * * * *]
        CRJ[Cloud Run Job<br/>anpi-call-scheduler]
    end
    
    subgraph "データベース層"
        SQL[Cloud SQL<br/>MySQL Instance]
        subgraph "テーブル構成"
            USERS[usersテーブル<br/>• user_id<br/>• phone_number<br/>• call_time<br/>• call_weekday]
        end
    end
    
    subgraph "タスクキュー"
        CT[Cloud Tasks<br/>anpi-call-queue]
        subgraph "登録タスク"
            TASK1[anpi-call-task-<br/>user1-20250614-0900]
            TASK2[anpi-call-task-<br/>user2-20250615-1030]
            TASK3[anpi-call-task-<br/>user3-20250616-1400]
        end
    end
    
    subgraph "外部システム"
        TWILIO[Twilio安否確認サービス<br/>anpi-call-twilio]
        PHONE[📞 電話発信<br/>音声ガイダンス]
    end
    
    subgraph "ログ・監視"
        CL[Cloud Logging<br/>実行ログ・エラーログ]
        CM[Cloud Monitoring<br/>実行メトリクス]
    end
    
    %% メインフロー
    CS -->|定時トリガー| CRJ
    CRJ -->|SELECT query| SQL
    SQL -->|ユーザー情報| CRJ
    CRJ -->|次週スケジュール計算| CT
    CT -->|指定時刻にHTTP POST| TWILIO
    TWILIO -->|電話発信| PHONE
    
    %% テーブル詳細
    SQL --> USERS
    
    %% タスク詳細
    CT --> TASK1
    CT --> TASK2  
    CT --> TASK3
    
    %% ログ出力
    CRJ --> CL
    CRJ --> CM
    TWILIO --> CL
    
    %% スタイリング
    classDef scheduler fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    classDef database fill:#34a853,stroke:#333,stroke-width:2px,color:#fff
    classDef tasks fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    classDef external fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff
    classDef monitoring fill:#607d8b,stroke:#333,stroke-width:2px,color:#fff
    
    class CS,CRJ scheduler
    class SQL,USERS database
    class CT,TASK1,TASK2,TASK3 tasks
    class TWILIO,PHONE external
    class CL,CM monitoring
```

## タスクスケジューリング処理詳細

```mermaid
flowchart LR
    subgraph "ユーザー設定例"
        USER1[ユーザーA<br/>曜日: mon<br/>時刻: 09:00]
        USER2[ユーザーB<br/>曜日: wed<br/>時刻: 14:30]
        USER3[ユーザーC<br/>曜日: fri<br/>時刻: 11:15]
    end
    
    subgraph "スケジュール計算ロジック"
        NOW[現在時刻<br/>2025-06-14 08:00<br/>土曜日]
        
        subgraph "ユーザーA計算"
            CALC_A1[月曜日まで: 2日後]
            CALC_A2[実行予定:<br/>2025-06-16 09:00]
        end
        
        subgraph "ユーザーB計算"
            CALC_B1[水曜日まで: 4日後]
            CALC_B2[実行予定:<br/>2025-06-18 14:30]
        end
        
        subgraph "ユーザーC計算"
            CALC_C1[金曜日まで: 6日後]
            CALC_C2[実行予定:<br/>2025-06-20 11:15]
        end
    end
    
    subgraph "Cloud Tasksタスク生成"
        TASK_A[anpi-call-task-12345678-20250616-0900<br/>スケジュール: 2025-06-16 09:00]
        TASK_B[anpi-call-task-87654321-20250618-1430<br/>スケジュール: 2025-06-18 14:30]
        TASK_C[anpi-call-task-11223344-20250620-1115<br/>スケジュール: 2025-06-20 11:15]
    end
    
    subgraph "実行時刻での処理"
        EXEC_A[2025-06-16 09:00<br/>→ Twilio API呼び出し<br/>→ ユーザーAに電話]
        EXEC_B[2025-06-18 14:30<br/>→ Twilio API呼び出し<br/>→ ユーザーBに電話]
        EXEC_C[2025-06-20 11:15<br/>→ Twilio API呼び出し<br/>→ ユーザーCに電話] 
    end
    
    %% フロー接続
    USER1 --> NOW
    USER2 --> NOW
    USER3 --> NOW
    
    NOW --> CALC_A1
    NOW --> CALC_B1
    NOW --> CALC_C1
    
    CALC_A1 --> CALC_A2
    CALC_B1 --> CALC_B2
    CALC_C1 --> CALC_C2
    
    CALC_A2 --> TASK_A
    CALC_B2 --> TASK_B
    CALC_C2 --> TASK_C
    
    TASK_A -.->|指定時刻| EXEC_A
    TASK_B -.->|指定時刻| EXEC_B
    TASK_C -.->|指定時刻| EXEC_C
    
    %% スタイリング
    classDef user fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef calc fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef task fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef exec fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    
    class USER1,USER2,USER3 user
    class NOW,CALC_A1,CALC_A2,CALC_B1,CALC_B2,CALC_C1,CALC_C2 calc
    class TASK_A,TASK_B,TASK_C task
    class EXEC_A,EXEC_B,EXEC_C exec
```

## コマンド実行例

### デプロイメント
```bash
# 開発環境デプロイ
./deploy.sh

# 本番環境用設定でデプロイ（.envを本番設定に変更後）
ENVIRONMENT=production ./deploy.sh
```

### 手動実行
```bash
# 開発環境ジョブの手動実行
gcloud run jobs execute anpi-call-scheduler-dev --region=asia-northeast1

# ログ確認
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=anpi-call-scheduler-dev" --limit=20
```

### 実行履歴確認
```bash
# 実行履歴表示
gcloud run jobs executions list --job=anpi-call-scheduler-dev --region=asia-northeast1 --limit=5
```

## 参考

- [setup-guide.md](setup-guide.md) - セットアップ手順
- [deployment.md](deployment.md) - デプロイメント詳細手順
- [gcp-resources.md](gcp-resources.md) - GCPリソースの詳細仕様
- [troubleshooting.md](troubleshooting.md) - トラブルシューティング
