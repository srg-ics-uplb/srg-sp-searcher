source ./venv/bin/activate
killall -9 gunicorn
clear
gunicorn -c gunicorn_config.py --reload app:app
