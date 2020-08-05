from celery import Celery
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")
django.setup()

celery_app = Celery('meiduo')

# 将刚刚的config配置给celery
# 里面的参数为我们创建的config配置文件
celery_app.config_from_object('celery_tasks.config')

# 让celery_app自动捕获目标地址下的任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email', 'celery_tasks.html'])
