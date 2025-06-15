-- テストデータ追加用SQLスクリプト
USE `default`;

-- 既存のテストデータを削除
DELETE FROM users WHERE last_name LIKE 'テスト%';

-- 現在時刻に基づいたテストデータを追加（土曜日対応）
INSERT INTO users (user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at) VALUES
('test-01', 'テスト現在時刻', '太郎', '090-1111-1111', '10:35:00', 'sat', NOW()),
('test-02', 'テスト1分前', '次郎', '090-2222-2222', '10:34:00', 'sat', NOW()),
('test-03', 'テスト1分後', '三郎', '090-3333-3333', '10:36:00', 'sat', NOW()),
('test-04', 'テスト2分前', '四郎', '090-4444-4444', '10:33:00', 'sat', NOW()),
('test-05', 'テスト2分後', '五郎', '090-5555-5555', '10:37:00', 'sat', NOW());

-- 追加されたデータを確認
SELECT 'テストデータ確認' AS message;
SELECT last_name, first_name, phone_number, call_time, call_weekday 
FROM users 
WHERE last_name LIKE 'テスト%' 
ORDER BY call_time;
