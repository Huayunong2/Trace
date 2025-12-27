"""
Gunicorn配置文件
"""
import multiprocessing

# 服务器socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker进程
workers = multiprocessing.cpu_count() * 2 + 1  # 推荐配置
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# 日志
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程名称
proc_name = "elderly_tracking"

# 用户和组（如果以root运行，可以设置）
# user = "www-data"
# group = "www-data"

# 其他选项
daemon = False
pidfile = "logs/gunicorn.pid"
umask = 0
tmp_upload_dir = None

