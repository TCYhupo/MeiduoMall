from django.template import loader
from django.conf import settings
import os
from goods.models import GoodsCategory, GoodsChannel, SKUSpecification, SKU, SpecificationOption, SPUSpecification
from copy import deepcopy

def get_breadcrumb(catagory):
    _dict = {
        'cat1': '',
        'cat2': '',
        'cat3': ''
    }
    # 一级
    if catagory.parent is None:
        _dict['cat1'] = catagory.name
    # 二级
    elif catagory.parent.parent is None:
        _dict['cat1'] = catagory.parent.name
        _dict['cat2'] = catagory.name
    # 三级
    elif catagory.parent.parent.parent is None:
        _dict['cat1'] = catagory.parent.parent.name
        _dict['cat2'] = catagory.parent.name
        _dict['cat3'] = catagory.name

    return _dict

def get_categories():
    categories = {}
    channels = GoodsChannel.objects.order_by('group_id', 'sequence')
    for channel in channels:
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                'channels': [],
                'sub_cats': []
            }
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        for cat2 in cat2s:
            cat3_list = []
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            for cat3 in cat3s:
                cat3_list.append({
                    'id': cat3.id,
                    'name': cat3.name
                })
            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3_list
            })
    return categories

def get_goods_and_spec(sku_id):
    # 当前SKU商品
    sku = SKU.objects.get(pk=sku_id)
    sku.default_image_url = sku.default_image_url.url

    # 记录当期sku的选项组合
    cur_sku_spec_options = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')
    cur_sku_options = []    # 选项列表
    for temp in cur_sku_spec_options:
        cur_sku_options.append(temp.option_id)
    # spu对象（ＳＰＵ商品）
    goods = sku.spu
    sku_options_mapping = {}
    skus = SKU.objects.filter(spu=goods)
    for temp_sku in skus:
        sku_spec_options = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')
        sku_options = []
        for temp in sku_spec_options:
            sku_options.append(temp.option_id)
        sku_options_mapping[tuple(sku_options)] = temp_sku.id

    # specs当前页面需要渲染的所有规格
    specs = SPUSpecification.objects.filter(spu=goods).order_by('id')
    for index, spec in enumerate(specs):
        options = SpecificationOption.objects.filter(spec=spec)
        temp_list = deepcopy(cur_sku_options)
        for option in options:
            temp_list[index] = option.id
            option.sku_id = sku_options_mapping.get(tuple(temp_list))
        # 在每一个规格对象中动态添加一个属性spec_options来记录当前规格有哪些选项
        spec.spec_options = options
    return goods, sku, specs
