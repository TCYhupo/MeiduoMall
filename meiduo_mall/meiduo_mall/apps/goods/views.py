from django.shortcuts import render
from django.views import View
from goods.models import SKU, GoodsCategory
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage
from .utils import get_breadcrumb
from haystack.views import SearchView
# Create your views here.
class ListView(View):
    def get(self, request, category_id):
        # 提取参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')

        # 校验参数
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '获取数据库数据失败'
            })

        breadcrumb = get_breadcrumb(category)
        try:
            skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '获取数据库数据失败'
            })

        # 分页--> django分页器
        paginator = Paginator(skus, page_size)
        # 获取指定页
        try:
            cur_page = paginator.page(number=page)
        except EmptyPage as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '空页'
            })

        # 构建响应返回
        ret_list = []
        for sku in cur_page:
            ret_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'count': paginator.num_pages,
            'list': ret_list
        })

class HotGoodsView(View):
    def get(self, request, category_id):
        # 1.获取热销商品
        skus = SKU.objects.filter(
            category_id=category_id,
            is_launched=True
        ).order_by('-sales')[:2]

        # 2.构建响应返回
        hot_skus_list = []
        for sku in skus:
            hot_skus_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url.url,
                'name': sku.name,
                'price': sku.price
            })
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'hot_skus': hot_skus_list
        })

# 使用Haystack提供的搜索视图，实现搜索
# SearchView搜索师徒基类，它提供的视图对应的接口就是：
# 请求方式：ＧＥＴ
# 请求路径：search/
# 请求参数：?q=keyword&page=1&page_size=3
class MySearchView(SearchView):
    def create_response(self):
        context = self.get_context()

        sku_list = []
        for sku in context['page'].object_list:
            sku_list.append({
                'id': sku.object.id,
                'name': sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image_url.url,
                'searchkey': context['query'],
                'page_size': context['paginator'].per_page,
                'count': context['paginator'].count
            })
        return JsonResponse(sku_list, safe=False)