import pickle, base64
from django_redis import get_redis_connection

def carts_cookie_encode(cart_dict):
    return base64.b64encode(
        pickle.dumps(cart_dict)
    ).decode()


def carts_cookie_decode(cart_str):
    return pickle.loads(
        base64.b64decode(cart_str.encode())
    )

def merge_cart_cookie_to_redis(request, user, response):
    # 获取Cookie中的购物车数据
    cookie_cart = request.COOKIES.get('carts')
    if not cookie_cart:
        # 购物车没数据,直接返回
        return response
    cart_dict = carts_cookie_decode(cookie_cart)

    new_dict = {}
    new_add = []
    new_remove = []
    for key, value in cart_dict.items():
        new_dict[key] = value['count']
        if value['selected']:
            new_add.append(key)
        else:
            new_remove.append(key)

    conn = get_redis_connection('carts')
    conn.hmset('carts_%s'%user.id, new_dict)
    if new_add:
        conn.sadd('selected_%s'%user.id, *new_add)
    else:
        conn.srem('selected_%s'%user.id, *new_remove)

    response.delete_cookie('carts')
    return response