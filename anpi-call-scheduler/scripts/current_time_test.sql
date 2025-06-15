-- 現在時刻（01:55頃）に近いテストデータを追加
USE `default`;

-- 既存のテストデータを削除
DELETE FROM users WHERE last_name LIKE 'テスト%';

-- 現在時刻（01:55頃）に近いテストデータを追加
INSERT INTO users (user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at) VALUES
('test-current-01', 'テスト現在時刻', '太郎', '090-1111-1111', '01:55:00', 'sun', NOW()),
('test-current-02', 'テスト1分前', '次郎', '090-2222-2222', '01:54:00', 'sun', NOW()),
('test-current-03', 'テスト1分後', '三郎', '090-3333-3333', '01:56:00', 'sun', NOW()),
('test-current-04', 'テスト2分前', '四郎', '090-4444-4444', '01:53:00', 'sun', NOW()),
('test-current-05', 'テスト2分後', '五郎', '090-5555-5555', '01:57:00', 'sun', NOW());

-- 追加されたデータを確認
SELECT 'テストデータ確認（現在時刻対応）' AS message;
SELECT last_name, first_name, phone_number, call_time, call_weekday 
FROM users 
WHERE last_name LIKE 'テスト%' 
ORDER BY call_time;
