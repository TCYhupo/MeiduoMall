from django.template import loader
from goods.utils import get_categories, get_goods_and_spec
import os
from django.conf import settings
from celery_tasks.main import celery_app

@celery_app.task(name='detail_html')
def generate_static_sku_detail_html(sku_id):
    template = loader.get_template('detail.html')

    categories = get_categories()
    goods, sku, specs = get_goods_and_spec(sku_id)
    context = {
        'categories': categories,
        'goods': goods, # 当前sku从属的spu
        'specs': specs, # 规格和选项信息
        'sku': sku      # 当前sku商品对象
    }

    html_text = template.render(context)

    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'goods/%s.html'%sku_id)
    with open(file_path, 'w') as f:
        f.write(html_text)