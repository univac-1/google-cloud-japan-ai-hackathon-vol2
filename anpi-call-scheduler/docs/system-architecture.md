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

## デプロイメント実行フロー

```mermaid
flowchart LR
    subgraph "開発環境"
        DEV[開発者]
        ENV_FILE[.env設定ファイル]
        DEPLOY[deploy.sh実行]
    end
    
    subgraph "Cloud Build処理"
        CONFIG[cloudbuild.yaml読み込み]
        BUILD[Dockerビルド<br/>Dockerfile]
        PUSH[イメージプッシュ<br/>Container Registry]
        JOBS[Cloud Run Jobs<br/>デプロイ]
    end
    
    subgraph "スケジューラー設定"
        SCHED[Cloud Scheduler<br/>作成・更新]
        CRON[Cron設定<br/>定時実行]
    end
    
    DEV --> ENV_FILE
    ENV_FILE --> DEPLOY
    DEPLOY --> CONFIG
    CONFIG --> BUILD
    BUILD --> PUSH
    PUSH --> JOBS
    JOBS --> SCHED
    SCHED --> CRON
    
    classDef dev fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    classDef build fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    classDef schedule fill:#34a853,stroke:#333,stroke-width:2px,color:#fff
    
    class DEV,ENV_FILE,DEPLOY dev
    class CONFIG,BUILD,PUSH,JOBS build
    class SCHED,CRON schedule
```

## ファイル構成と役割

```mermaid
graph TB
    subgraph "メインアプリケーション"
        MAIN[main.py<br/>バッチ処理メインロジック]
        REQ[requirements.txt<br/>Python依存関係]
    end
    
    subgraph "Docker設定"
        DOCKER[Dockerfile<br/>コンテナイメージ定義]
    end
    
    subgraph "デプロイメント設定"
        DEPLOY[deploy.sh<br/>デプロイスクリプト]
        BUILD[cloudbuild.yaml<br/>Cloud Build設定]
        ENV[.env<br/>環境変数設定]
    end
    
    subgraph "GCPリソース定義"
        JOB[job.yaml<br/>Cloud Run Job設定]
        SCHED[scheduler.yaml<br/>Cloud Scheduler設定]
    end
    
    subgraph "ドキュメント"
        README[README.md<br/>プロジェクト概要]
        DOCS[docs/<br/>詳細ドキュメント]
    end
    
    %% 関係性
    DEPLOY --> ENV
    DEPLOY --> BUILD
    BUILD --> DOCKER
    DOCKER --> MAIN
    DOCKER --> REQ
    BUILD -.->|参考| JOB
    DEPLOY -.->|参考| SCHED
    
    classDef app fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef docker fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef deploy fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    classDef config fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    classDef docs fill:#fafafa,stroke:#757575,stroke-width:2px
    
    class MAIN,REQ app
    class DOCKER docker
    class DEPLOY,BUILD,ENV deploy
    class JOB,SCHED config
    class README,DOCS docs
```

## 実行環境構成

```mermaid
graph TB
    subgraph "Cloud Run Jobs実行環境"
        direction TB
        CRJ[Cloud Run Jobs<br/>anpi-call-scheduler]
        
        subgraph "実行時設定"
            CPU[CPU: 1 vCPU]
            MEM[Memory: 512Mi]
            TIMEOUT[Timeout: 300s]
            RETRY[Max Retry: 1]
        end
        
        subgraph "環境変数"
            PROJECT[GOOGLE_CLOUD_PROJECT]
            ENV_VAR[ENVIRONMENT]
            LOG[LOG_LEVEL]
            JOB_NAME[CLOUD_RUN_JOB]
        end
    end
    
    subgraph "Cloud Scheduler設定"
        SCHEDULE[スケジュール実行<br/>Cron: 0 * * * *]
        TIMEZONE[タイムゾーン<br/>Asia/Tokyo]
        HTTP[HTTP Trigger<br/>Cloud Run Jobs API]
    end
    
    subgraph "ログ・監視"
        LOGGING[Cloud Logging<br/>実行ログ]
        MONITOR[実行履歴<br/>成功/失敗]
    end
    
    %% 実行フロー
    SCHEDULE --> HTTP
    HTTP --> CRJ
    CRJ --> LOGGING
    CRJ --> MONITOR
    
    %% 設定の関係
    CPU -.-> CRJ
    MEM -.-> CRJ
    TIMEOUT -.-> CRJ
    RETRY -.-> CRJ
    PROJECT -.-> CRJ
    ENV_VAR -.-> CRJ
    LOG -.-> CRJ
    JOB_NAME -.-> CRJ
    
    classDef job fill:#4285f4,stroke:#333,stroke-width:2px,color:#fff
    classDef config fill:#34a853,stroke:#333,stroke-width:2px,color:#fff
    classDef schedule fill:#ff9800,stroke:#333,stroke-width:2px,color:#fff
    classDef logging fill:#9c27b0,stroke:#333,stroke-width:2px,color:#fff
    
    class CRJ job
    class CPU,MEM,TIMEOUT,RETRY,PROJECT,ENV_VAR,LOG,JOB_NAME config
    class SCHEDULE,TIMEZONE,HTTP schedule
    class LOGGING,MONITOR logging
```

## 環境別構成

```mermaid
graph TB
    subgraph "開発環境設定"
        DEV_ENV[ENVIRONMENT=development]
        DEV_LOG[LOG_LEVEL=debug]
        DEV_JOB[anpi-call-scheduler-dev]
        DEV_SCHED[anpi-call-scheduler-dev-hourly]
    end
    
    subgraph "本番環境設定"
        PROD_ENV[ENVIRONMENT=production]
        PROD_LOG[LOG_LEVEL=info]
        PROD_JOB[anpi-call-scheduler-prod]
        PROD_SCHED[anpi-call-scheduler-prod-hourly]
    end
    
    subgraph "共通リソース"
        CR[Container Registry<br/>gcr.io/PROJECT_ID/anpi-call-scheduler]
        CL[Cloud Logging]
        CB[Cloud Build<br/>cloudbuild.yaml]
    end
    
    subgraph ".env設定による切り替え"
        ENV_FILE[.env<br/>環境変数設定]
        DEPLOY_SCRIPT[deploy.sh<br/>設定読み込み]
    end
    
    %% 共通リソース使用
    DEV_JOB --> CR
    PROD_JOB --> CR
    DEV_JOB --> CL
    PROD_JOB --> CL
    
    %% デプロイメント
    ENV_FILE --> DEPLOY_SCRIPT
    DEPLOY_SCRIPT --> CB
    CB --> DEV_JOB
    CB --> PROD_JOB
    
    %% 環境固有設定
    DEV_ENV -.-> DEV_JOB
    DEV_LOG -.-> DEV_JOB
    DEV_SCHED -.-> DEV_JOB
    PROD_ENV -.-> PROD_JOB
    PROD_LOG -.-> PROD_JOB
    PROD_SCHED -.-> PROD_JOB
    
    classDef dev fill:#e8f5e8,stroke:#4caf50,stroke-width:2px
    classDef prod fill:#ffebee,stroke:#f44336,stroke-width:2px
    classDef shared fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    classDef config fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    
    class DEV_ENV,DEV_LOG,DEV_JOB,DEV_SCHED dev
    class PROD_ENV,PROD_LOG,PROD_JOB,PROD_SCHED prod
    class CR,CL,CB shared
    class ENV_FILE,DEPLOY_SCRIPT config
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
