from itsdangerous import BadData, TimedJSONWebSignatureSerializer
from django.conf import settings

def check_access_token(access_token):
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=600)

    try:
        data = serializer.loads(access_token)
    except BadData:
        # 未获取到数据 表明验证不通过
        return None
    else:
        # 能获取到数据 表明验证通过
        return data.get('openid')

def generate_access_token(openid):
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, expires_in=600)
    data = {'openid': openid}
    token = serializer.dumps(data)
    return token.decode()