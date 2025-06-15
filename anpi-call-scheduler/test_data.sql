-- テストデータ追加用SQLファイル
-- 現在のデータベース構造を確認
USE anpi_call_scheduler;

-- 既存のユーザーデータを確認
SELECT 'Existing users:' as info;
SELECT id, name, phone_number, notify_saturday, notify_sunday FROM users LIMIT 5;

-- 今日（土曜日）に通知を送るテストユーザーを追加
INSERT INTO users (name, phone_number, emergency_contact_phone, notify_saturday, created_at, updated_at) 
VALUES ('テストユーザー土曜日', '090-1234-5678', '090-8765-4321', TRUE, NOW(), NOW());

-- 即時実行用のテストユーザーも追加（現在時刻の10:40に設定）
INSERT INTO users (name, phone_number, emergency_contact_phone, notify_saturday, call_time, created_at, updated_at) 
VALUES ('即時実行テスト', '090-9999-9999', '090-0000-0000', TRUE, '10:40:00', NOW(), NOW());

-- 追加されたユーザーを確認
SELECT 'New Saturday users:' as info;
SELECT id, name, phone_number, notify_saturday, call_time FROM users WHERE notify_saturday = TRUE;
