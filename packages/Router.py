# coding=utf-8
__doc__ = '路由信息'
import inspect
import traceback
from urllib import parse
from aiohttp import web
from packages import logger


class Router(object):

    def __init__(self, method, route, doc, level, system, func):
        self.method = method
        self.route = route
        self.doc = doc
        self.level = level
        self.system = system
        self.func = func  # 关联的函数
        self.enable = True  # 这个路由是否启用

    def __repr__(self):
        return '{method} : {route}'.format(method=self.method, route=self.route)

class RouterCallBack(object):

    def __init__(self, routerObj, app, isMainRouter):
        self.router = routerObj
        self.isMain = isMainRouter
        self.app = app

    async def __call__(self, request):
        __logger = logger.get_logger()
        # 提取可能的路由
        if not self.router.enable:
            raise ValueError(self.router.method + ' ' + self.router.route + " 不可用")
        # 获取函数的参数表
        required_args = inspect.signature(self.router.func).parameters
        # logger.get_logger().info('需要的参数: %s' % required_args)
        # 获取从GET或POST传进来的参数值，如果函数参数表有这参数名就加入

        if request.method == 'POST':
            # for k in dir(request):
            #     print(k + ':' + str(getattr(request, k)))
            if getattr(request, '__data__', None):
                kw = {arg: value for arg, value in request.__data__.items() if
                      arg in required_args}  # POST需要进行参数的一些转换，这个转换在data工厂中。数据存储在__data__属性中
            else:
                kw = dict()  # 只有传递了数据才会有__data__
        else:
            # GET参数有可能需要类似于http://xxx.com/blog?id=5&name=ff之类的参数
            qs = request.query_string
            if qs:
                # logger.get_logger().info('GET指令的query参数: %s' % request.query_string)
                kw = {arg: value if isinstance(value, list) and len(value) > 1 else value[0] for arg, value in
                      parse.parse_qs(qs,
                                     True).items()}  # 保留空格。将查询参数添加到kw已知的参数列表 ref https://raw.githubusercontent.com/icemilk00/Python_L_Webapp/master/www/coroweb.py。可以支持传递数组
            else:
                kw = {arg: value for arg, value in request.match_info.items() if arg in required_args}
        # 获取match_info的参数值，例如@get('/blog/{id}')之类的参数值
        kw.update(request.match_info)
        # 如果有request参数的话也加入
        if 'request' in required_args:
            kw['request'] = request
        # 如果有app参数，也添加app参数
        if self.isMain and 'app' in required_args:
            kw['app'] = self.app  # 主要用于main的路由设置

        # 检查参数表中有没参数缺失
        for key, arg in required_args.items():
            # request参数不能为可变长参数
            if key == 'request' and arg.kind in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                return web.HTTPBadRequest(text='request 参数不能是可变参数')
            # 如果参数类型不是变长列表和变长字典，变长参数是可缺省的
            if arg.kind not in (arg.VAR_POSITIONAL, arg.VAR_KEYWORD):
                # 如果还是没有默认值，而且还没有传值的话就报错
                if arg.default == arg.empty and arg.name not in kw:
                    raise ValueError('缺少的参数: %s' % arg.name)
                    # raise _exceptions.APIError('缺少的参数: %s' % arg.name)

        __logger.info('使用参数 {paras} 调用路由：{method} {path} 关联的函数'.format(paras=kw, method=self.router.method,
                                                                       path=self.router.route))
        try:
            # return await self._func(**kw)
            # 需要通过Pack 管理器的
            return await self.router.func(**kw)
        except Exception as e:
            # 出错记录
            msg = '运行路由处理器期间发生‘%s’类型的错误，错误消息如下：%s，堆栈信息：\n%s\n' % (str(type(e)), str(e.args), traceback.format_exc())
            __logger.error(msg)
            raise e