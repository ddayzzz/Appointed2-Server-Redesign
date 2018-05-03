# coding=utf-8
__doc__ = '定义了服务器的类'
from aiohttp.web import Application
import os
from packages.Router import RouterCallBack
from packages import logger
from jinja2 import Environment, FileSystemLoader


class Appointed2WebApp(Application):

    def __init__(self, loop, middlewares, topServer):
        Application.__init__(self, middlewares=middlewares, loop=loop)
        self.template = None
        self.topServer = topServer

    def add_statics(self, routerToDirName):
        for router, folder in routerToDirName.items():
            realpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
            self.router.add_static(router, realpath)

    def init_template(self, **kw):
        if self.template:
            return
        options = dict(
            autoescape=kw.get('autoescape', True),
            block_start_string=kw.get('block_start_string', '{%'),
            block_end_string=kw.get('block_end_string', '%}'),
            variable_start_string=kw.get('variable_start_string', '{{'),
            variable_end_string=kw.get('variable_end_string', '}}'),
            auto_reload=kw.get('auto_reload', True)
        )
        paths = kw.get('paths', None)
        if paths is None:
            paths = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')]
        for path in paths:
            # logger.get_logger().info('设置 jinja2 模板的路径: %s' % os.path.join(os.path.dirname(os.path.abspath(__file__)), path))
            env = Environment(loader=FileSystemLoader(path), **options)
        filters = kw.get('filters', None)
        if filters is not None:
            for name, f in filters.items():
                env.filters[name] = f
        self.template = env

    def add_routersBridge(self, packagesMgr):
        lo = logger.get_logger()
        for packname, pack in packagesMgr.loadedPackages.items():
            for target_key, routerObj in pack.routers.items():
                self.router.add_route(routerObj.method, routerObj.route, RouterCallBack(routerObj, self, routerObj.system))
                lo.info('成功添加模块：‘%s’, 路由: %s' % (packname, str(routerObj)))
