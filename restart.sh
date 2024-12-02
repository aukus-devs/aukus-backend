#!/usr/bin/sh
gunicorn 'test_api_app:create_app()'  --log-level debug --workers 1 --bind 127.0.0.1:5100  >> ./backend.log 2>&1 &
