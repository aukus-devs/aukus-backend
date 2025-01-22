#docker run --env-file ../.env_2024_prod --net=host -p 5000:5000 -it $(docker build -t olegsvs/aukus:2024-prod -q .)
#docker run -d -e AUKUS_BACKEND_PORT=5000 --env-file ../.env_2024_prod --net=host --name aukus_2024_prod -it olegsvs/aukus:2024-prod
nohup bash aukus_logs_alert.sh >/dev/null 2>&1 &
nohup python background_jobs.py  >> ./backend.log 2>&1 &
gunicorn 'only_api_app:create_app()'  --access-logfile backend.log --error-logfile backend.log --capture-output --log-level debug --workers 4 --bind 0.0.0.0:${AUKUS_BACKEND_PORT} | tail -F ./backend.log
