from django.contrib import admin
from django.urls import path, re_path
from . import views
# 路由映射表
urlpatterns = [
    # 用户名是否重复检查接口
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # 手机号是否重复检查接口
    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
]