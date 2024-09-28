#!/usr/bin/sh
ps -ef | grep 'only_api_app' | awk '{print $2}'  | xargs -r kill -9
ps -ef | grep 'only_api_app' | awk '{print $2}'  | xargs -r kill -9
sleep 2
#nohup python3.10 only_api_app.py >> backend.log &
nohup gunicorn 'only_api_app:create_app()'  --log-level debug --workers 1 --bind 127.0.0.1:5000  >> ./backend.log 2>&1 &
