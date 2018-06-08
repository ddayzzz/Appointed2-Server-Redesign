# coding=utf-8
__doc__ = '路由信息'
import inspect
from urllib import parse
from aiohttp import web
from packages import logger


class Router(object):

    def __init__(self, method, route, doc, level, system, func, acquireAdmin):
        self.method = method
        self.route = route
        self.doc = doc
        self.level = level
        self.system = system
        self.func = func  # 关联的函数
        self.enable = True  # 这个路由是否启用
        # 计算可以作为标志的名称
        self.flagName = self.method + '_' + str(id(self))
        # 友好名称
        self.friendlyName = self.method + ' ' + self.route
        # 调用这个是否需要管理员登录
        self.acquireAdmin = acquireAdmin

    def __repr__(self):
        return 'Router< {method} : {route} at {addr}>'.format(method=self.method, route=self.route, addr=id(self))


    def __dict__(self):
        res = {
            'route': self.route,
            'method': self.method,
            'level': self.level,
            'system': self.system,
            'flagName': self.flagName,  # 这个是定义为可以作为标志符的名称
            'friendlyName': self.friendlyName,
            'enable': self.enable,
            'doc': self.doc,
            'acquireAdmin': self.acquireAdmin
        }
        return res

class RouterCallBack(object):

    logger = logger.get_logger('Server')

    def __init__(self, routerObj, app, isMainRouter):
        self.router = routerObj
        self.isMain = isMainRouter
        self.app = app

    async def __call__(self, request):
        __logger = logger.get_logger()
        # 提取可能的路由
        if not self.router.enable:
            raise ValueError(self.router.method + ' ' + self.router.route + " 不可用")
        # 检查是否需要管理员
        if self.router.acquireAdmin:
            # cookie 的信息
            if not request.__user__ or not request.__user__.admin:
                if request.method == 'POST':
                    if request.__user__:
                        __logger.info('用户：{user} 尝试 POST {path} 访问失败：需要管理员凭据'.format(user=request.__user__,
                                                                                     path=request.path))
                    else:
                        __logger.info('未知用户尝试 POST {path} 访问失败：需要管理员凭据'.format(path=request.path))
                    return (401, '访问未授权，需要管理员凭据')
                # 如果不存在登录的用户、或者还不是管理员账户
                # 跳转到登录界面
                redire = 'redirect:/signin?message=%20路由需要管理员权限%20&redirect=' + request.path_qs
                __logger.info('路由需要管理员的权限，重定向到 %s' % redire)
                return redire
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
        # 如果需要 websocket 通信
        if self.router.level == 'websocket' and 'wsResponse' in required_args:
            ws = web.WebSocketResponse()
            await ws.prepare(request)
            kw['wsResponse'] = ws  # 使用异步 for 就可以得出消息
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

        RouterCallBack.logger.info('使用参数 {paras} 调用路由：{method} {path} 关联的函数'.format(paras=kw, method=self.router.method,
                                                                       path=self.router.route))
        try:
            # return await self._func(**kw)
            # 记录请求
            self.app.runtimeInfo.addRequestCount(self.router.flagName)
            return await self.router.func(**kw)
        except Exception as e:
            # 出错记录
            RouterCallBack.logger.error('运行路由处理器期间发生‘%s’类型的错误，错误消息：', exc_info=True, stack_info=True)
            raise e