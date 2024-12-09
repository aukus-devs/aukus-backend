ps -ef | grep 'test_api_app' | awk '{print $2}'  | xargs -r kill -9
ps -ef | grep 'test_api_app' | awk '{print $2}'  | xargs -r kill -9
mkdir old_logs
d=$(date +%Y-%m-%d-%H-%M-%S)
mv backend.log old_logs/backend_$d.log
nohup gunicorn 'test_api_app:create_app()'  --log-level debug --workers 1 --bind 127.0.0.1:5100  >> ./backend.log 2>&1 &
