from django.contrib import admin
from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'^qq/authorization/$', views.QQFirstView.as_view()),
    re_path(r'^oauth_callback/$', views.QQUserView.as_view()),
]