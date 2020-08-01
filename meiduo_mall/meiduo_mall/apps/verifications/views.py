from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha
import logging
logger = logging.getLogger("django")
import random
from django import http
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code
# Create your views here.

class ImageCodeView(View):
    "返回图形验证码的类视图"
    def get(self, request, uuid):
        '''
        生成图形验证码，保存到redis中，另外返回图片
        :param request: 请求对象
        :param uuid: 浏览器端生成的唯一id
        :return: 一个图片
        '''

        # 1.调用工具类 captcha 生成图形验证码
        text, image = captcha.generate_captcha()

        # 2.链接 redis， 获取链接对象
        redis_conn = get_redis_connection("verify_code")

        # 3.利用链接对象，保存数据到 redis， 使用setex函数
        redis_conn.setex("img_%s" % uuid, 300, text)

        # 4.返回图片
        return HttpResponse(image, content_type="image/jpg")


class SMSCodeView(View):
    def get(self, request, mobile):
        # 接收参数
        image_code_client = request.GET.get("image_code")
        uuid = request.GET.get("image_code_id")

        # 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            }, status=400)

        # 创建连接到redis的对象
        redis_conn = get_redis_connection("verify_code")

        # 提取图形验证码
        image_code_server = redis_conn.get("img_%s" % uuid)
        if image_code_server is None:
            # 图形验证码过期或不存在
            return http.JsonResponse({
                'code': 400,
                'errmsg': '图形验证码失效'
            }, status=400)

        # 删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete("img_%s", uuid)
        except Exception as e:
            logger.error(e)

        # 对比图形验证码，需要将ｂｙｔｅｓ转字符串
        image_code_server = image_code_server.decode()

        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({
                'code': 400,
                'errmsg': '输入图形验证码有误'
            }, status=400)

        # 生成短信验证码：生成６位数验证码
        sms_code = '%06d' % random.randint(0, 999999)

        # 验证标志位，防止用户恶意频繁发送验证码
        flag = redis_conn.get('flag_%s' % mobile)
        if flag:
            return http.JsonResponse({
                'code': 400,
                'errmsg': '有效期内不能重复发送'
            }, status=400)

        # 创建pipeline，将多个任务一起执行
        p = redis_conn.pipeline()
        # 保存短信验证码，短信验证码有效期３００ｓ
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # 设定60s标志位
        redis_conn.setex('flag_%s' % mobile, 60, 1)
        #　执行pipeline
        p.execute()

        # 发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)
        ccp_send_sms_code.delay(mobile, sms_code)
        print("已发送, 手机验证码：", sms_code)

        # 相应结果
        return http.JsonResponse({
            'code': 0,
            'errmsg': '发送短信成功'
        })
