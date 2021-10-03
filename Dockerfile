FROM ubuntu:20.04

RUN mkdir /usr/src/app
WORKDIR /usr/src

RUN apt-get update && apt-get install python3-pip sqlite3 -y
COPY requirements.txt . 
COPY app ./app
RUN pip install --no-cache-dir -r requirements.txt

#CMD [ "flask", "run" ,"--host=0.0.0.0"]
CMD [ "gunicorn","-b", "0.0.0.0:5000", "app:app","--timeout","3600"]
#CMD ["tail","-f","/dev/null"]
