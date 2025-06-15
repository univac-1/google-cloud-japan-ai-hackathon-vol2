-- 曜日マッピング確認用SQLスクリプト
USE `default`;

-- 現在のテストデータの曜日を確認
SELECT 'テストデータの曜日確認' AS message;
SELECT last_name, first_name, call_time, call_weekday 
FROM users 
WHERE last_name LIKE 'テスト%' 
ORDER BY call_time;

-- 曜日を日曜日（sun）に変更してテスト
UPDATE users 
SET call_weekday = 'sun' 
WHERE last_name LIKE 'テスト%';

SELECT 'テストデータの曜日を日曜日に変更' AS message;
SELECT last_name, first_name, call_time, call_weekday 
FROM users 
WHERE last_name LIKE 'テスト%' 
ORDER BY call_time;
