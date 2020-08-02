"""
索引模型类，模块名固定
"""
from haystack import indexes
from .models import SKU

# 针对ES搜索引擎定义一个索引模型类
class SKUIndex(indexes.SearchIndex, indexes.Indexable):

    # text固定的字段
    # document=True 表示text字段用于被检索字段
    # use_template=True 表示使用模板来指定text字段中包含被检索的数据有哪些
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 获取被检索数据的模型类
        return SKU

    def index_queryset(self, using=None):
        # 返回被检索的查询集
        return self.get_model().objects.filter(is_launched=True)


