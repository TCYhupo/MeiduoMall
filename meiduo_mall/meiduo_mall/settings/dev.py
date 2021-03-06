"""
Django settings for meiduo_mall project.

Generated by 'django-admin startproject' using Django 2.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/

"""
# 开发阶段使用的配置文件

import os
import sys
import corsheaders

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# __file__:当前文件——dev.py
# os.path.abspath(__file__):/Users/weiwei/Desktop/meiduo_mall/meiduo_mall/settings/dev.py
# os.path.dirname(os.path.abspath(__file__)): /Users/weiwei/Desktop/meiduo_mall/meiduo_mall/settings/
# os.path.dirname(os.path.dirname(os.path.abspath(__file__))):/Users/weiwei/Desktop/meiduo_mall/meiduo_mall/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

apps_path = os.path.join(BASE_DIR, "apps")
sys.path.insert(0, apps_path)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ')bw8w1jd+*e8tns!s-3_m6rlsv2q4dv-831jqfu#j*m-nl-9@m'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Django允许绑定到的域名
ALLOWED_HOSTS = ['www.meiduo.site',
                 '127.0.0.1',
                 'localhost',
                 'api.meiduo.site'
                 ]
# ALLOWED_HOSTS = ['*'] # 所有合法域名都能够绑定


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'users.apps.UsersConfig',
    'verifications',
    'oauth',
    'areas',
    'contents',
    'goods',
    'django_crontab',
    'haystack',
    'carts',
    'orders',
    'payment',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meiduo_mall.urls'


# 设置django工程的模版参数
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        # 指定当前django工程查找模版文件的目录
        'DIRS': [os.path.join(BASE_DIR, 'templates')],

        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'meiduo_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

# 配置数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # 表示使用mysql
        'NAME': 'meiduo_mall_db',
        'HOST': '127.0.0.1', # mysql服务所在主机ip
        'PORT': 3306, # 表示一个服务进程
        'USER': 'root',
        'PASSWORD': 'mysql'
    },
    'slave': {
        'ENGINE': 'django.db.backends.mysql', # 表示使用mysql
        'NAME': 'meiduo_mall_db',
        'HOST': '127.0.0.1', # mysql服务所在主机ip
        'PORT': 8306, # 表示一个服务进程
        'USER': 'root',
        'PASSWORD': '123456'
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'


# 配置当前工程使用的缓存数据库
CACHES = {
    "default": { # 默认存储信息: 存到 0 号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": { # session 信息: 存到 1 号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "verify_code":{ # 验证码信息： 存到2号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history":{ # 浏览历史，存到3号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "carts":{ # 浏览历史，存到4号库
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}
# 指定session使用缓存存储
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
# 指定使用sessoin配置项的缓存
SESSION_CACHE_ALIAS = "session"

# django的日志配置模版
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/meiduo.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

AUTH_USER_MODEL = 'users.User'

# CORS跨域请求白名单设置
CORS_ORIGIN_WHITELIST = (
    'http://127.0.0.1:8080',
    'http://localhost:8080',
    'http://www.meiduo.site:8080',
)

CORS_ALLOW_CREDENTIALS = True  # 允许携带cookie

AUTHENTICATE_BACKENDS = ['users.utils.UsernameMobileAuthBackend']

# 发送邮件的设置
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# smtp服务器地址
EMAIL_HOST = 'smtp.163.com'
# 端口号
EMAIL_PORT = 25
# 发送邮件的邮箱
EMAIL_HOST_USER = 'nephi_meiduo@163.com'
# 在邮箱中设置的客户端授权密码
EMAIL_HOST_PASSWORD = 'PWKBRTROZGHNJYSS'
# 收件人看到的发件人
EMAIL_FROM = 'Nephi<nephi_meiduo@163.com>'
# 邮箱验证链接
EMAIL_VERIFY_URL = 'http://www.meiduo.site:8080/success_verify_email.html?token='

# QQ登录参数
# 我们申请的 客户端id
QQ_CLIENT_ID = '101474184'
# 我们申请的 客户端秘钥
QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c'
# 我们申请时添加的: 登录成功后回调的路径
QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'

# 指定当前工程使用的存储后端
DEFAULT_FILE_STORAGE = 'meiduo_mall.utils.fastdfs.fastdfs_storage.FastDFSStorage'

# 指定fdfs服务器的域名
FDFS_URL = "http://image.meiduo.site:8888/"

# 封装静态页面文件根目录
GENERATED_STATIC_HTML_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), 'front_end_pc')

# 指定定时任务的执行规则
CRONJOBS = [
    (   # 分 时 日 月 周
        # =====周期执行=====
        #'30 * * * *'  # 每个小时的第30分钟执行一次
        # =====时间间隔执行=====
        # '*/1 * * * *' # 每间隔１分钟执行一次
        '*/1 * * * *',
        'contents.generate_index.generate_index.html',
        '>> ' + os.path.join(BASE_DIR, 'logs/crontab.log'))
]

# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://127.0.0.1:9200/', # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'meiduo_mall', # Elasticsearch建立的索引库的名称
    },
}

# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# 可以在 dev.py 中添加如下代码, 用于决定每页显示数据条数:
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 5

# 支付宝
ALIPAY_APPID = '2021000116686249'
ALIPAY_DEBUG = True
ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = "http://www.meiduo.site:8080/pay_success.html"

# 主从同步
DATABASE_ROUTERS = ['meiduo_mall.utils.db_router.MasterSlaveDBRouter']