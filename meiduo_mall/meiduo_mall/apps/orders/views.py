from django.shortcuts import render
from decimal import Decimal

from django.utils.decorators import method_decorator
from django.views import View
from meiduo_mall.utils.view import info_required
from users.models import Address
from goods.models import SKU
from django_redis import get_redis_connection
from carts.utils import carts_cookie_encode, carts_cookie_decode
from django.http import JsonResponse
from django.utils import timezone
import json
from .models import OrderInfo, OrderGoods
# Create your views here.

class OrderSettlementView(View):
    @method_decorator(info_required)
    def get(self, request):
        user = request.user
        # 获取地址信息
        try:
            addresses = Address.objects.filter(user=user, is_deleted=False)
        except Exception as e:
            print(e)
            addresses = None

        # 获取商品信息
        conn = get_redis_connection('carts')
        cart_dict = conn.hgetall('carts_%s'%user.id)
        cart_selected = conn.smembers('selected_%s'%user.id)
        cart = {}
        for sku_id in cart_selected:
            cart[int(sku_id)] = int(cart_dict[sku_id])

        # 构建地址字典
        address_list = []
        for address in addresses:
            address_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })

        # 构建商品字典
        skus = SKU.objects.filter(id__in=cart.keys())
        skus_list = []
        for sku in skus:
            skus_list.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image_url.url,
                'count': cart[sku.id],
                'price': sku.price
            })

        # 运费
        freight = Decimal('10.00')

        # 渲染界面
        context = {
            'addresses': address_list,
            'skus': skus_list,
            'freight': freight
        }

        # 返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'context': context
        })

class OrderCommitView(View):
    """订单提交"""

    def post(self, request):
        """保存订单信息和订单商品信息"""
        _dict = json.loads(request.body.decode())
        address_id = _dict.get('address_id')
        pay_method = _dict.get('pay_method')
        if not all([address_id, pay_method]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({
                'code': 400,
                'errmsg': '参数address_id有误'
            })
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],
                              OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({
                'code': 400,
                'errmsg': '参数pay_method有误'
            })

        # 获取登录用户
        user = request.user
        # 生成订单编号：年月日时分秒＋用户编号
        order_id = timezone.localtime().strftime('%Y%m%d%H%M%S') + ('%09d'%user.id)
        # 保存订单基本信息OrderInfo
        order = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal('0'),
            freight=Decimal('10.00'),
            pay_method=pay_method,
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            if pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']
            else OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        )

        conn = get_redis_connection('carts')
        cart_dict = conn.hgetall('carts_%s'%user.id)
        cart_selected = conn.smembers('selected_%s'%user.id)
        carts = {}
        for sku_id in cart_selected:
            carts[int(sku_id)] = int(cart_dict[sku_id])
        sku_ids = carts.keys()

        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_count = carts[sku_id]
            # 判断SKU库存
            if sku_count > sku.stock:
                return JsonResponse({
                    'code': 400,
                    'errmsg': '库存不足'
                })

            # SKU减少库存，增加销量
            sku.stock -= sku_count
            sku.sales += sku_count
            sku.save()

            # 修改SPU销量
            sku.spu.sales += sku_count
            sku.spu.save()

            # 保存订单商品信息 OrderGoods
            OrderGoods.objects.create(
                order=order,
                sku=sku,
                count=sku_count,
                price=sku.price
            )

            # 保存商品订单中总价和总数量
            order.total_count += sku_count
            order.total_amount += (sku_count * sku.price)

        # 添加邮费和保存订单信息
        order.total_amount += order.freight
        order.save()

        # 清楚购物车中已结算的商品
        conn.hdel('carts_%s'%user.id, *cart_selected)
        conn.srem('selected_%s'%user.id, *cart_selected)

        # 响应提交订单结果
        return JsonResponse({
            'code': 0,
            'errmsg': '下单成功',
            'order_id': order.order_id
        })
