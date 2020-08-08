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
from django.db import transaction
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
        if not cart_selected:
            return JsonResponse({
                'code': 400,
                'errmsg':'未选中商品'
            })
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

        conn = get_redis_connection('carts')
        cart_dict = conn.hgetall('carts_%s'%user.id)
        cart_selected = conn.smembers('selected_%s'%user.id)
        carts = {}
        for sku_id in cart_selected:
            carts[int(sku_id)] = int(cart_dict[sku_id])
        sku_ids = carts.keys()

        with transaction.atomic():
            # 事务：关键的时间节点－－order订单新建节点
            save_id = transaction.savepoint()   # 事务执行的保存点

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

            for sku_id in sku_ids:
                # 乐观锁：增加一个死循环
                while True:
                    sku = SKU.objects.get(id=sku_id)

                    # 乐观锁：读取原始库存
                    origin_stock = sku.stock
                    origin_sales = sku.sales

                    sku_count = carts[sku_id]
                    # 判断SKU库存
                    if sku_count > sku.stock:
                        # 事务：由于库存不足，事务需要回滚到，订单新建之前的节点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({
                            'code': 400,
                            'errmsg': '库存不足'
                        }, status=400)

                    # SKU减少库存，增加销量
                    # sku.stock -= sku_count
                    # sku.sales += sku_count
                    # sku.save()

                    # 乐观锁：更新库存和销量
                    # 乐观锁：计算差值
                    new_stock = origin_stock - sku_count
                    new_sales = origin_sales + sku_count
                    # 乐观锁：在原有旧数据的基础上更新
                    result = SKU.objects.filter(
                        id=sku_id,
                        stock=origin_stock,
                        sales=origin_sales
                    ).update(stock=new_stock, sales=new_sales)

                    # 乐观锁：如果下单失败，但是库存充足，继续下单直到下单成功或库存不足
                    if result == 0:
                        continue

                    # 乐观锁：下单成功或失败跳出循环
                    break
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
            # 事务：清除保存点
            transaction.savepoint_commit(save_id)

        # 清楚购物车中已结算的商品
        conn.hdel('carts_%s'%user.id, *cart_selected)
        conn.srem('selected_%s'%user.id, *cart_selected)

        # 响应提交订单结果
        return JsonResponse({
            'code': 0,
            'errmsg': '下单成功',
            'order_id': order.order_id
        })
