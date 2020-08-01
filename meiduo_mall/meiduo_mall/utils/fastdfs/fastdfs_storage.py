"""
自定义django存储后端，修改ImageField类型字段url属性输出的结果
"""

from django.core.files.storage import Storage
from django.conf import settings

class FastDFSStorage(Storage):

    def open(self, name, mode='rb'):
        return None

    def save(self, name, content, max_length=None):
        pass

    def url(self, name):
        # 该函数返回的结果就是，ImageField.url属性的输出结果
        # 参数：name就是该文件类型字段在mysql中存储的
        return settings.FDFS_URL + name