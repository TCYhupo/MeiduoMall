from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser

# 设置用户密码：AbstractUser.set_password()
# 校验密码：AbtractUser.check_password()
# Django默认给我们提供了身份认证，权限检查等功能，而这些功能都必须依赖AbstractUser

class User(AbstractUser):
    mobile = models.CharField(
        unique=True,
        verbose_name='手机号',
        null=True,
        max_length=11
    )

    class Meta:
        db_table = 'tb_users'   # 指定模型类User所映射的mysql表名
        verbose_name = '手机号'
        verbose_name_plural = '手机号'
    
    def __str__(self):
        return self.username