# coding=utf-8
import functools
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['get', 'post']
__doc__ = 'Appointed2定义的路由包装器，包装get和post方法'


# 这个是用来附加模块
# GET获取数据
def get(path):
    """
    get是一个装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper
    return decorator


# POST包装器
def post(path):
    """
    post是一个装饰器
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kw):
            return func(*args, **kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper
    return decorator