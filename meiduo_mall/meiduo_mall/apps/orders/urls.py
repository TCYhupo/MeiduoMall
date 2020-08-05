from django.contrib import admin
from django.urls import path, re_path, include
from . import views

urlpatterns = [
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    # 订单提交
    re_path(r'^orders/commit/$', views.OrderCommitView.as_view()),
]