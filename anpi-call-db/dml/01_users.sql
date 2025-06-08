-- DML: users テーブルのサンプルデータ
-- Cloud SQL for MySQL 8.4
-- 高齢者向け安否確認＋イベント案内アプリ

-- データベースの使用を宣言
USE default;

-- users テーブルにサンプルデータを挿入
INSERT INTO users (
  last_name, first_name, last_name_kana, first_name_kana,
  postal_code, prefecture, address_block, address_building,
  phone_number, email, gender, birth_date,
  call_time, call_weekday
) VALUES 
  ('田中', '太郎', 'タナカ', 'タロウ',
   '100-0001', '東京都', '千代田区千代田1-1-1', 'サンプルマンション101',
   '03-1234-5678', 'tanaka@example.com', 'male', '1950-04-15',
   '09:00:00', 'mon'),
   
  ('佐藤', '花子', 'サトウ', 'ハナコ',
   '530-0001', '大阪府', '大阪市北区梅田1-1-1', 'テストビル202',
   '06-9876-5432', 'sato@example.com', 'female', '1955-08-22',
   '10:00:00', 'wed'),
   
  ('鈴木', '一郎', 'スズキ', 'イチロウ',
   '231-0045', '神奈川県', '横浜市中区伊勢佐木町1-1-1', 'よこはまマンション304',
   '045-1111-2222', 'suzuki@example.com', 'male', '1945-12-03',
   '08:30:00', 'tue'),
   
  ('山田', '美智子', 'ヤマダ', 'ミチコ',
   '450-0002', '愛知県', '名古屋市中村区名駅1-1-1', 'なごやタワー505',
   '052-3333-4444', 'yamada@example.com', 'female', '1952-07-18',
   '09:30:00', 'thu'),
   
  ('高橋', '次郎', 'タカハシ', 'ジロウ',
   '810-0001', '福岡県', '福岡市中央区天神1-1-1', 'てんじんビル601',
   '092-5555-6666', 'takahashi@example.com', 'male', '1948-11-25',
   '10:00:00', 'fri');

SELECT 'users テーブルにサンプルデータを挿入しました' AS status;
SELECT CONCAT('挿入件数: ', COUNT(*), '件') AS count FROM users;
