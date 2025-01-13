#!/usr/bin/sh
ps -ef | grep 'aukus_2025_logs_alert.sh' | awk '{print $2}'  | xargs -r kill -9
sleep 2
ps -ef | grep 'v2025_only_api_app' | awk '{print $2}'  | xargs -r kill -9
ps -ef | grep 'v2025_only_api_app' | awk '{print $2}'  | xargs -r kill -9
ps -ef | grep 'v2025_background_jobs' | awk '{print $2}'  | xargs -r kill -9
sleep 2
mkdir old_logs
d=$(date +%Y-%m-%d-%H-%M-%S)
mv backend.log old_logs/backend_$d.log
#nohup python3.10 only_api_app.py >> backend.log &
nohup gunicorn 'v2025_only_api_app:create_app()'  --log-level debug --workers 4 --bind 127.0.0.1:5200  >> ./backend.log 2>&1 &
nohup python v2025_background_jobs.py  >> ./backend.log 2>&1 &
nohup sh aukus_2025_logs_alert.sh >/dev/null 2>&1 &
