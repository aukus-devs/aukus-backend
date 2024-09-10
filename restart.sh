#!/usr/bin/sh
ps -ef | grep 'only_api_app' | awk '{print $2}'  | xargs -r kill -9
sleep 2
nohup python3.10 only_api_app.py > backend.log &
