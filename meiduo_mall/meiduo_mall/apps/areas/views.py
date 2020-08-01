from django.shortcuts import render
from django.views import View
from areas.models import Area
from django import http
from django.core.cache import cache
from django.http import JsonResponse
# Create your views here.

class ProvinceAreasView(View):
    def get(self, request):
        # 有先判断缓存中有没有数据
        p_list = cache.get('province_list')

        if not p_list:
            provinces = Area.objects.filter(parent=None)

            # 把所有的模型类对象转化成字典{id, name}
            p_list = []
            for province in provinces:
                p_list.append({
                    'id': province.id,
                    'name': province.name
                })
            cache.set('province_list', p_list, 3600)

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'province_list': p_list
        })

class SubAreasView(View):
    def get(self, request, pk):
        # 路径中传入的ｐｋ
        # 1. pk是省的主键，请求所有市信息
        # 2. pk是市的逐渐，请求所有区信息
        sub_data = cache.get('sub_area_%s'%pk)

        if not sub_data:
            p_area = Area.objects.get(pk=pk)

            subs = Area.objects.filter(parent_id=pk)
            sub_list = []
            for sub in subs:
                sub_list.append({
                    'id': sub.id,
                    'name': sub.name
                })

            sub_data = {
                'id': p_area.id,
                'name': p_area.name,
                'subs': sub_list
            }

            cache.set('sub_area_%s'%pk, sub_data, 3600)

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'sub_data': sub_data
        })