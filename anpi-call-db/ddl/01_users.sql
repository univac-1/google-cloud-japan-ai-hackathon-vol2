-- DDL: users テーブル（高齢者利用者マスタ）作成
-- Cloud SQL for MySQL 8.4
-- 高齢者向け安否確認＋イベント案内アプリ

-- データベースの使用を宣言
USE default;

-- users テーブル作成
CREATE TABLE users (
  user_id          CHAR(36)     PRIMARY KEY
                        DEFAULT (UUID())
                        COMMENT '利用者ID',
  last_name        VARCHAR(64)  NOT NULL COMMENT '姓（漢字）',
  first_name       VARCHAR(64)  NOT NULL COMMENT '名（漢字）',
  last_name_kana   VARCHAR(64)            COMMENT 'セイ（全角カナ）',
  first_name_kana  VARCHAR(64)            COMMENT 'メイ（全角カナ）',
  postal_code      CHAR(8)               COMMENT '郵便番号（例: 123-4567）',
  prefecture       VARCHAR(40)           COMMENT '都道府県',
  address_block    VARCHAR(100)          COMMENT '市区町村・町名・番地など',
  address_building VARCHAR(100)          COMMENT '建物名・部屋番号など',
  phone_number     VARCHAR(14) NOT NULL  COMMENT '電話番号（国内10–11桁、ハイフン可）',
  email            VARCHAR(255)          COMMENT 'メールアドレス',
  gender           ENUM('male','female') DEFAULT NULL COMMENT '性別',
  birth_date       DATE                  COMMENT '生年月日',
  call_time        TIME                  COMMENT '電話希望時刻',
  call_weekday     ENUM('sun','mon','tue','wed','thu','fri','sat')
                        DEFAULT 'mon'
                        COMMENT '電話希望曜日',
  created_at       TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                        COMMENT '作成日時（自動）',
  updated_at       TIMESTAMP NOT NULL
                        DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                        COMMENT '更新日時（自動）'
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COMMENT='高齢者利用者マスタ';

SELECT 'users テーブルが作成されました' AS status;
