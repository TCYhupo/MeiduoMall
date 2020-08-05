from django.contrib.auth import login
from django.shortcuts import render
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django.http import JsonResponse
import json, re
import logging
from users.models import User
from .utils import check_access_token
from .models import OAuthQQUser
from oauth.utils import generate_access_token
from carts.utils import merge_cart_cookie_to_redis
from django_redis import get_redis_connection
logger = logging.getLogger('django')
# Create your views here.
class QQFirstView(View):
    def get(self, request):
        # 接收参数
        next_url = request.GET.get('next')

        # 创建OAuthQQ类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next_url)

        # 获取ＱＱ登录页面链接
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'login_url': login_url
        })

class QQUserView(View):
    def get(self, request):
        # 接收参数
        code = request.GET.get('code')

        if not code:
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少code参数'
            })

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            # 获取access token
            access_token = oauth.get_access_token(code)

            # 获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            print(e)
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '认证失败'
            })

        try:
            oauth_qq = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            # openid 没有绑定商城用户
            access_token = generate_access_token(openid)
            return JsonResponse({
                'code': 300,
                'errmsg': 'ok',
                'access_token': access_token
            })

        user = oauth_qq.user
        login(request, user)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', user.username, max_age=3600*24*14)

        # 合并购物车
        response = merge_cart_cookie_to_redis(request, user, response)
        return response

    def post(self, request):
        # 获取参数
        _dict = json.loads(request.body.decode())
        mobile = _dict.get('mobile')
        password = _dict.get('password')
        sms_code = _dict.get('sms_code')
        access_token = _dict.get('access_token')

        # 校验参数
        if not all([mobile, password, sms_code, access_token]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数'
            })

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})
        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})
        # 判断短信验证码是否一致
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        if sms_code_server is None:
            return JsonResponse({
                'code': 400,
                'errmsg': '输入的验证码有误'
            })

        openid = check_access_token(access_token)
        if not openid:
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少openid'
            })
        try:
            user = User.objects.get(mobile=mobile)
        except Exception as e:
            user = User.objects.create_user(
                username=mobile,
                password=password,
                mobile=mobile
            )
        else:
            if not user.check_password(password):
                return JsonResponse({
                    'code': 400,
                    'errmsg': '输入的密码不正确'
                })

        try:
            OAuthQQUser.objects.create(openid=openid, user=user)
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '往数据库添加数据失败'
            })

        # 状态保持
        login(request, user)

        # 创建相应对象
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 合并购物车
        response = merge_cart_cookie_to_redis(request, user, response)

        # 返回响应
        return response