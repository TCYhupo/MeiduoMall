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