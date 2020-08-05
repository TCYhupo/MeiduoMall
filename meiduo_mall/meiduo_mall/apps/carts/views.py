from django.shortcuts import render
from django.views import View
import json
from django.http import JsonResponse
from carts.utils import carts_cookie_encode, carts_cookie_decode
from django_redis import get_redis_connection
from goods.models import SKU
# Create your views here.

class CartsView(View):

    def post(self, request):
        data = json.loads(request.body.decode())

        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)

        if not all([sku_id, count]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少参数'
            })

        if not isinstance(selected, bool):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数有误'
            })

        user = request.user
        if user.is_authenticated:
            # 登录写入Redis
            conn = get_redis_connection('carts')
            conn.hincrby('carts_%s'%user.id, sku_id, count)
            if selected:
                conn.sadd('selected_%s'%user.id, sku_id)
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
        else:
            # 提取用户Cookie购物车数据
            cart_dict = {}
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

            # 如果原来有Cookie则追加，没有则新建
            if sku_id in cart_dict:
                cart_dict[sku_id]['count'] += count
                cart_dict[sku_id]['selected'] = selected
            else:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            # 重新编码写入Cookie
            cart_str = carts_cookie_encode(cart_dict)
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
            response.set_cookie('carts', cart_str, max_age=None)
            return response

    # 展示购物车
    def get(self, request):
        cart_dict = {}

        user = request.user
        if user.is_authenticated:
            # 用户登录：从Redis读取购物车信息
            conn = get_redis_connection('carts')
            cart_redis_dict = conn.hgetall('carts_%s'%user.id)
            cart_redis_selected = conn.smembers('selected_%s'%user.id)
            for key, value in cart_redis_dict.items():
                cart_dict[int(key)] = {
                    'count': int(value),
                    'selected': key in cart_redis_selected
                }
        else:
            # 用户未登录：从Cookie读取购物车信息
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

        cart_skus = []
        for key, value in cart_dict.items():
            sku = SKU.objects.get(pk=key)
            cart_skus.append({
            'id':sku.id,
            'name': sku.name,
            'count': value['count'],
            'selected': value['selected'],
            'default_image_url': sku.default_image_url.url,
            'price': sku.price,
            'amount': value['count'] * sku.price
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus
        })

    # 修改购物车
    def put(self, request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)
        cart_dict = {}
        user = request.user
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            conn.hmset('carts_%s'%user.id, {sku_id: count}) # 覆盖写入，遵循幂等
            if selected:
                conn.sadd('selected_%s'%user.id, sku_id)
            else:
                conn.srem('selected_%s'%user.id, sku_id)
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'cart_sku': {
                    'id': sku_id,
                    'count': count,
                    'selected': selected
                }
            })
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

            if not cart_dict:
                return JsonResponse({
                    'code': 0,
                    'errmsg': 'ok'
                })
            if sku_id in cart_dict:
                cart_dict[sku_id]['count'] = count  # 幂等性
                cart_dict[sku_id]['selected'] = selected

            cart_str = carts_cookie_encode(cart_dict)

            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'cart_sku': {
                    'id': sku_id,
                    'count': count,
                    'selected': selected
                }
            })
            response.set_cookie('carts', cart_str)
            return response

    # 购物车删除商品
    def delete(self, request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')

        try:
            SKU.objects.get(pk=sku_id)
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '商品信息不存在'
            })

        user = request.user
        cart_dict = {}
        # 判断用户是否已登录
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            p = conn.pipeline()
            p.hdel('carts_%s'%user.id, sku_id)
            p.srem('selected_%s'%user.id, sku_id)
            p.execute()
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
        else:
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
            if sku_id in cart_dict:
                del cart_dict[sku_id]
                cart_str = carts_cookie_encode(cart_dict)
            response.set_cookie('carts', cart_str)
            return response

# 全选购物车
class CartSelectAllView(View):
    def put(self, request):
        data = json.loads(request.body.decode())
        selected = data['selected']

        if type(selected) != bool:
            return JsonResponse({
                'code': 400,
                'errmsg': '参数有误'
            })

        user = request.user
        # 判断用户是否登录
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            sku_dict = conn.hgetall('carts_%s'%user.id)
            sku_ids = sku_dict.keys()
            if selected:
                conn.sadd('selected_%s'%user.id, *sku_ids)
            else:
                conn.srem('selected_%s'%user.id, *sku_ids)
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
        else:
            carts_str = request.COOKIES.get('carts')
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
            if carts_str:
                carts_dict = carts_cookie_decode(carts_str)
                for key in carts_dict:
                    carts_dict[key]['selected'] = selected
                carts_str = carts_cookie_encode(carts_dict)
                response.set_cookie('carts', carts_str)
            return response

class CartsSimpleView(View):
    def get(self, request):
        user = request.user

        cart_dict = {}
        if user.is_authenticated:
            # 用户已登录，查Redis
            conn = get_redis_connection('carts')
            data_dict = conn.hgetall('carts_%s'%user.id)
            cart_selected = conn.smembers('selected_%s'%user.id)
            for key, value in data_dict.items():
                cart_dict[int(key)] = {
                    'count': int(value),
                    'selected': key in cart_selected
                }
        else:
            # 用户未登录，查Cookie
            cookie_cart = request.COOKIES.get('carts')
            if cookie_cart:
                cart_dict = carts_cookie_decode(cookie_cart)

        cart_skus = []
        sku_ids = cart_dict.keys()
        skus = SKU.objects.filter(id__in=sku_ids)
        for sku in skus:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': cart_dict.get(sku.id).get('count'),
                'default_image_url': sku.default_image_url.url
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus
        })


