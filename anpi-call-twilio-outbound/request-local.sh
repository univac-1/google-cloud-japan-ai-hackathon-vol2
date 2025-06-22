# python main.py --call=+818079399927 --user-id=4CC0CA6A-657C-4253-99FF-C19219D30AE2

curl -X POST "http://localhost:8081/client/call/check" \
    -H "Content-Type: application/json" \
    -d '{"user_id": "4CC0CA6A-657C-4253-99FF-C19219D30AE2"}'