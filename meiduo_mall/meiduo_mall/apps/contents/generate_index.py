from django.template import loader
# loader : 读取/加载模板文件
from goods.models import GoodsChannel, GoodsCategory
from contents.models import Content,ContentCategory
from django.conf import settings
import os

def render_template_demo():
    template = loader.get_template('demo.html')

    context = {
        'name' : 'dong',
        'age': 21
    }

    html_text = template.render(context=context)

    with open('demo.html', 'w') as f:
        f.write(html_text)


# 渲染出完整的index.html首页静态文件
def generate_static_index_html():
    # 广告首页渲染
    # 1.获取模板对象
    template = loader.get_template('index.html')

    # 2.传入模板参数,渲染页面
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

    contents = {}
    content_cats = ContentCategory.objects.all()
    for content_cat in content_cats:
        contents[content_cat.key] = Content.objects.filter(category=content_cat, status=True).order_by('sequence')

    context = {
        'categories': categories,
        'contents': contents
    }
    html_text = template.render(context)

    # 3.写入front_end_pc文件夹下的index.html静态文件中
    with open(os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html'), 'w') as f:
        f.write(html_text)