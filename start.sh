source ./bin/activate
clear
# gunicorn -c gunicorn_config.py app:app
gunicorn -c gunicorn_config.py --preload app:app
# gunicorn -c gunicorn_dev_config.py app:app