-- DDL: events テーブル（イベント情報マスタ）作成
-- Cloud SQL for MySQL 8.4
-- 高齢者向け安否確認＋イベント案内アプリ

-- データベースの使用を宣言
USE default;

-- events テーブル作成
CREATE TABLE events (
  event_id         CHAR(36)     PRIMARY KEY
                        DEFAULT (UUID())
                        COMMENT 'イベントID',
  title            VARCHAR(150) NOT NULL COMMENT 'イベントタイトル',
  description      TEXT                  COMMENT 'イベント詳細',
  start_datetime   DATETIME     NOT NULL COMMENT '開始日時',
  end_datetime     DATETIME     NOT NULL COMMENT '終了日時',
  postal_code      CHAR(8)               COMMENT '会場郵便番号',
  prefecture       VARCHAR(40)           COMMENT '会場都道府県',
  address_block    VARCHAR(100)          COMMENT '会場市区町村・町名・番地',
  address_building VARCHAR(100)          COMMENT '会場建物名・部屋番号',
  contact_name     VARCHAR(120)          COMMENT '問い合わせ窓口名',
  contact_phone    VARCHAR(14)           COMMENT '問い合わせ電話番号',
  event_url        VARCHAR(2083)         COMMENT 'イベント公式URL',
  created_at       TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                        COMMENT '作成日時（自動）',
  updated_at       TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                        COMMENT '更新日時（自動）'
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COMMENT='イベント情報マスタ';

SELECT 'events テーブルが作成されました' AS status;
