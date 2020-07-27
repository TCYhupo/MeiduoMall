from django.shortcuts import render
from django.views import View
from users.models import User
from django.http import JsonResponse
import logging
logger = logging.getLogger('django')
# Create your views here.

# 验证用户名重复
class UsernameCountView(View):
    def get(self, request, username):
        try:
            # 1.统计用户数量
            count = User.objects.filter(username=username).count()
        except Exception as e:
            print(e)
            # 写日志
            logger.error(e)

        # 2.构建相应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })

class MobileCountView(View):
    def get(self, request, mobile):
        try:
            # 1.根据手机号统计数量
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            print(e)
            logger.error(e)
        # 2.构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'count': count
        })