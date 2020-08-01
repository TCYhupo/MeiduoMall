from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from meiduo_mall.settings import dev

# 设置用户密码：AbstractUser.set_password()
# 校验密码：AbtractUser.check_password()
# Django默认给我们提供了身份认证，权限检查等功能，而这些功能都必须依赖AbstractUser
from meiduo_mall.utils.BaseModel import BaseModel

class User(AbstractUser):
    mobile = models.CharField(
        unique=True,
        verbose_name='手机号',
        null=True,
        max_length=11
    )

    email_active = models.BooleanField(default=False, verbose_name="邮箱验证状态")

    default_address = models.ForeignKey('Address',
                                        related_name='users',
                                        null=True,
                                        blank=True,
                                        on_delete=models.SET_NULL,
                                        verbose_name='默认地址')

    class Meta:
        db_table = 'tb_users'   # 指定模型类User所映射的mysql表名
        verbose_name = '用户'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.username

    def generate_verify_email_url(self):
        # 设置验证有效期为１天
        serializer = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in= 60 * 60 * 24)

        # 拼接参数
        data = {'user_id': self.id, 'email': self.email}

        # 加密生成token值,bytes类型
        token = serializer.dumps(data).decode()

        # 拼接url
        verify_url = dev.EMAIL_VERIFY_URL + token

        # 返回
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        # 邮件验证链接有效期为1天
        serializer = TimedJSONWebSignatureSerializer(dev.SECRET_KEY, expires_in=60 * 60 * 24)

        try:
            # 解析传入的token值, 获取数据data
            data = serializer.loads(token)
        except BadData:
            return None
        else:
            # 如果有值, 则获取
            user_id = data.get('user_id')
            email = data.get('email')

        # 尝试从User表中获取对应的用户
        try:
            user = User.objects.get(id=user_id, email=email)
        except Exception as e:
            return None
        else:
            return user

class Address(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name='用户'
    )
    province = models.ForeignKey(
        'areas.Area',
        on_delete=models.PROTECT,
        related_name='province_addresses',
        verbose_name='省'
    )
    city = models.ForeignKey(
        'areas.Area',
        on_delete=models.PROTECT,
        related_name='city_addresses',
        verbose_name='市'
    )
    district = models.ForeignKey(
        'areas.Area',
        on_delete=models.PROTECT,
        related_name='district_addresses',
        verbose_name='区'
    )
    title = models.CharField(max_length=20, verbose_name='地址名称')
    receiver = models.CharField(max_length=20, verbose_name='收货人')
    place = models.CharField(max_length=50, verbose_name='地址')
    mobile = models.CharField(max_length=11, verbose_name='手机')
    tel = models.CharField(max_length=20,
                           null=True,
                           blank=True,
                           default='',
                           verbose_name='固定电话')

    email = models.CharField(max_length=30,
                             null=True,
                             blank=True,
                             default='',
                             verbose_name='电子邮箱')

    is_deleted = models.BooleanField(default=False, verbose_name='逻辑删除')

    class Meta:
        db_table = 'tb_addresses'
        verbose_name = '用户地址'
        verbose_name_plural = verbose_name

        # 定义默认查询集排序方式
        ordering = ['-update_time']