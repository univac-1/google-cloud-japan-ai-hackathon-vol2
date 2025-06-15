-- テストデータ追加用SQLファイル
-- 現在時刻（土曜日）に実行されるユーザーを追加

USE `default`;

-- 既存のテストデータを削除
DELETE FROM users WHERE last_name LIKE 'テスト%';

-- 土曜日の現在時刻に近いテストユーザーを追加
INSERT INTO users (user_id, last_name, first_name, phone_number, call_time, call_weekday, created_at, updated_at) VALUES
('test-saturday-1', 'テスト土曜', 'ユーザー1', '090-1234-5678', '10:35:00', 'sat', NOW(), NOW()),
('test-saturday-2', 'テスト土曜', 'ユーザー2', '090-1234-5679', '10:36:00', 'sat', NOW(), NOW()),
('test-saturday-3', 'テスト土曜', 'ユーザー3', '090-1234-5680', '10:37:00', 'sat', NOW(), NOW()),
('test-saturday-4', 'テスト土曜', 'ユーザー4', '090-1234-5681', '10:34:00', 'sat', NOW(), NOW()),
('test-saturday-5', 'テスト土曜', 'ユーザー5', '090-1234-5682', '10:33:00', 'sat', NOW(), NOW());

-- 追加されたデータを確認
SELECT user_id, last_name, first_name, call_time, call_weekday 
FROM users 
WHERE last_name = 'テスト土曜'
ORDER BY call_time;

-- 土曜日に設定されているユーザー数を確認
SELECT COUNT(*) as saturday_users 
FROM users 
WHERE call_weekday = 'sat';
