import aiohttp
from packages import logger, APIError
__logger = logger.get_logger()

async def requestCheck_factory(app, handler):
    """
    仅仅是对404这个错误进行处理
    :param app: 网页服务器实例
    :param handler: 路由处理器
    :return: 返回一个封装的可调用对象
    """
    async def request_check(request):
        if isinstance(request.match_info, aiohttp.web_urldispatcher.MatchInfoError):  # http://aiohttp.readthedocs.io/en/v0.21.5/_modules/aiohttp/web_urldispatcher.html
            # print(request.match_info.http_exception.status)  # 检查错误信息
            # 检查是否是来自热安装的URL请求。不再需要热安装支持。安装、卸载、更新后需要重新启动服务
            # for obj_name, obj_ModObj in __hotInstalledPackages.items():  # 模块名称，模块的对象
            #     for router_fnc, info_dict in obj_ModObj.routers.items():
            #         if info_dict['method'] == request.method and info_dict['route'] == request.path:
            #             dispatcher = aiohttp.web.UrlDispatcher()
            #             dispatcher.add_route(request.method, request.path, router_fnc)
            #             req = await dispatcher.resolve(request)
            #             return await router_fnc(request)
            #
            msg = ('%s 没有定义' % request.path, )
            __logger.error(msg[0])
            if request.path.startswith('/api'):
                return APIError.ProcessHTTPNotFound(app, messages=msg, format='api')
            else:
                return APIError.ProcessHTTPNotFound(app, messages=msg, format='normal')

        return (await handler(request))

    return request_check