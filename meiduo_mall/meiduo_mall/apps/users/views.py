from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.http import JsonResponse
from users.models import User, Address
import logging
logger = logging.getLogger('django')
import json
import re
from django_redis import get_redis_connection
from django import http
from django.contrib.auth import login, authenticate, logout
from meiduo_mall.utils.view import info_required

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

class RegisterView(View):
    def post(self, request):
        # 1.读取参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        sms_code = dict.get('sms_code')
        allow = dict.get('allow')

        # 2.校验参数
        if not all([username, password, password2, mobile, sms_code]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误'
            })

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            })

        if password != password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '重复密码有误'
            })

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({
                'code': 400,
                'errmsg': '手机号格式有误'
            })

        if not allow:
            return JsonResponse({
                'code': 400,
                'errmsg': '请勾选用户协议'
            })

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s'%mobile)
        if not sms_code_server:
            return JsonResponse({
                'code': 400,
                'errmsg': '短信验证码过期'
            })

        if sms_code != sms_code_server.decode():
            return JsonResponse({
                'code': 400,
                'errmsg': '验证码有误'
            })

        # 3.新建数据
        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                mobile=mobile
            )
        except Exception as e:
            print(e)
            logger.error(e)
            return http.JsonResponse({
                'code': 400,
                'errmsg': '保存到数据库出错'
            })

        # 实现状态保持
        login(request, user)

        # 4.构建响应
        # return http.JsonResponse({
        #     'code': 0,
        #     'errmsg': 'ok'
        # })
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response

class LoginView(View):
    def post(self, request):
        # 加载参数
        dict = json.loads(request.body)
        username = dict['username']
        password = dict['password']
        remembered = dict['remembered']

        # 校验参数
        if not all([username, password]):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数不全'
            })

        if not re.match(r'^\w{5,20}$', username):
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误'
            })

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            })

        # 校验数据
        user = authenticate(username=username, password=password)
        # 返回响应
        if user is None:
            return JsonResponse({
                'code': 400,
                'errmsg': '用户名或密码错误'
            })
        # 状态保持
        login(request, user)

        # 判断用户是否记住用户
        if remembered:
            # 记住，默认两周
            request.session.set_expiry(None)
        else:
            # 没记住，浏览器关闭时session失效
            request.session.set_expiry(0)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        # 写入ｃｏｏｋｉｅ
        response.set_cookie('username',
                            user.username,
                            max_age=3600 * 24 * 14)
        return response

class LogoutView(View):
    def delete(self, request):
        # 清理session
        logout(request)
        # 创建response对象
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.delete_cookie('username')
        return response

class UserInfoView(View):
    @method_decorator(info_required)
    def get(self, request):
        info_data = {'username': request.user.username,
                    'mobile': request.user.mobile,
                    'email': request.user.email,
                    'email_active': request.user.email_active
         }
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': info_data
        })

class EmailView(View):
    def put(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少email参数'
            })
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数email有误'
            })

        # 赋值 email 字段
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '添加邮箱失败'
            })

        email = '<' + email + '>'

        from celery_tasks.email.tasks import send_verify_email
        # 调用发送的函数
        verify_url = request.user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url)

        # 响应添加邮箱结果
        return JsonResponse({
            'code': 0,
            'errmsg': '添加邮箱成功'
        })

class VerifyEmailView(View):
    def put(self, request):
        # 接收参数
        token = request.GET.get('token')
        # 校验参数
        if not token:
            return JsonResponse({
                'code': 400,
                'errmsg': '无效的token'
            })
        # 调用上面封装好的方法,将token传入
        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({
                'code': 400,
                'errmsg': '无效的token'
            })
        # 修改 email_active的值为True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '激活邮箱失败'
            })
        # 返回邮箱验证结果
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })

class CreateAddressView(View):
    def post(self, request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 判断用户地址数量是否超过２０
        user = request.user
        count = Address.objects.filter(user=user).count()
        if count >= 20:
            return JsonResponse({
                'code': 400,
                'errmsg': '数量达到上限'
            })

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 写入/更新数据
        try:
            address = Address.objects.create(
                user=user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver,
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel
            )
            # 设置默认地址
            if not user.default_address:
                user.default_address = address
                user.save()
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '新增地址失败'
            })

        address_info = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_info
        })

class AddressView(View):
    def get(self, request):
        # 得到当前用户的所有地址
        user = request.user
        addresses = Address.objects.filter(user=user, is_deleted=False)

        # 将地址转化为字典
        address_list = []
        for address in addresses:
            if address.id != user.default_address_id:
                address_list.append({
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
            else:
                address_list.insert(0, {
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'default_address_id': user.default_address_id,
            'addresses': address_list
        })

class UpdateDestroyAddressView(View):
    def put(self, request, address_id):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        try:
            # 更新地址信息
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            # 地址不存在
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '更新地址失败'
            })

        # 构建响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新结果
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_dict
        })

    def delete(self, request, address_id):
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '地址不存在'
            }, status=404)
        # 真删除
        # address.delete()

        # 逻辑删除
        address.is_deleted = True
        address.save()
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })

class DefaultAddressView(View):
    def put(self, request, address_id):
        user = request.user
        # 改对象，不常用
        # user.default_address = Address.objects.get(pk=address_id)
        # 改主键，常用
        user.default_address_id = address_id
        user.save()
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })

class UpdateTitleAddressView(View):
    def put(self, request, address_id):
        # 获取更新数据
        data = json.loads(request.body.decode())
        title = data.get('title')
        try:
            # 获取被修改的地址对象
            address = Address.objects.get(pk=address_id)
            # 修改并返回响应
            address.title = title
            address.save()
        except Exception as e:
            print(e)
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '地址不存在'
            }, status=404)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })

class ChangePasswordView(View):
    def put(self, request):
        _dict = json.loads(request.body.decode())
        old_password = _dict.get('old_password')
        new_password = _dict.get('new_password')
        new_password2 = _dict.get('new_password2')

        if not all([old_password, new_password, new_password2]):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数缺失'
            })

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码最少8位， 最长20位'
            })
        if new_password != new_password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次输入密码不一致'
            })

        user = request.user
        if not user.check_password(old_password):
            return JsonResponse({
                'code': 400,
                'errmsg':'旧密码有误'
            })

        user.set_password(new_password)
        user.save()

        logout(request)

        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.delete_cookie('username')
        return response