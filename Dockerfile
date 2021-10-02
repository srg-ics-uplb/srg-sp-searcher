FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

#CMD [ "flask", "run" ,"--host=0.0.0.0"]
CMD [ "gunicorn","-b", "0.0.0.0:5000", "app:app"]

