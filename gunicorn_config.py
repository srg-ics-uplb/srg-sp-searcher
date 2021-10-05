bind = '0.0.0.0:5000'
timeout = 30
workers = 3
threads = 2
keepalive = 2

pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

#accesslog = '-'  #logging on stdout
#errorlog = '-'   #logging on stdout
accesslog = 'access.log'
errorlog = 'error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
