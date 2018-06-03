# coding=utf-8
__doc__ = '定义了 http 服务的类'
from aiohttp.web import Application
import os
import psutil
from packages.Router import RouterCallBack
from packages import logger, macros, dbManager
from jinja2 import Environment, FileSystemLoader
from datetime import datetime

class RuntimeInfo():
    """
    这个是Appointed2 网页服务的信息
    """
    def __init__(self):
        self.routerInfo = dict()

    def _ensureRouterObjExisted(self, routerObjRepr):
        """

        :param routerObjRepr:
        :return:
        """
        obj = self.routerInfo.get(routerObjRepr, None)
        if not obj:
            self.routerInfo[routerObjRepr] = {'count': 0, 'enable': False}
        return self.routerInfo[routerObjRepr]

    def addRequestCount(self, routerObjRepr):
        """
        获取请求计数
        :param routerObjRepr:
        :return:
        """
        self._ensureRouterObjExisted(routerObjRepr)
        self.routerInfo[routerObjRepr]['count'] += 1

    def changeEnableStatus(self, routerObjRepr, val):
        self._ensureRouterObjExisted(routerObjRepr)
        self.routerInfo[routerObjRepr]['enable'] = val

    def getRealTimeInfo(self):
        return self.__dict__()

    def __dict__(self):
        cpurate = psutil.cpu_percent()  # 获取当前CPU 使用率
        mem = psutil.virtual_memory()
        mem_ava = mem.used / 1024 / 1024  # 换算成 MB
        mem_rate = mem.percent
        ctime = datetime.fromtimestamp(psutil.Process(macros.Macro('MONITOR_PID')).create_time())
        delta_time = datetime.now() - ctime
        res = {
            'cpuRate': '%f%%' % cpurate,
            'memoryUsage': '%dMB, %f%%' % (mem_ava, mem_rate),
            'routerInfo': self.routerInfo,
            'bindHost': macros.Macro('HOST'),
            'bindPort': macros.Macro('PORT'),
            'runningTime': '{days}天，{seconds}秒。创建于{ct}'.format(
                days=delta_time.days,
                seconds=delta_time.seconds,
                ct=ctime,
            )
        }
        return res



class Appointed2WebApp(Application):

    logger = logger.get_logger('Server')

    def __init__(self, loop, middlewares, topServer):
        Application.__init__(self, middlewares=middlewares, loop=loop)
        self.template = None
        self.topServer = topServer
        self.runtimeInfo = RuntimeInfo()


    def add_statics(self, routerToDirName):
        for router, folder in routerToDirName.items():
            realpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), folder)
            Appointed2WebApp.logger.info(
                '设置静态资源路径: %s' % realpath)
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
        path = kw.get('path', None)
        if path is None:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        env = Environment(loader=FileSystemLoader(path), **options)
        Appointed2WebApp.logger.info(
            '设置 jinja2 模板的路径: %s' % os.path.join(os.path.dirname(os.path.abspath(__file__)), path))
        filters = kw.get('filters', None)
        if filters is not None:
            for name, f in filters.items():
                env.filters[name] = f
        self.template = env

    def add_routersBridge(self, packagesMgr):
        for packname, pack in packagesMgr.loadedPackages.items():
            for target_key, routerObj in pack.routers.items():
                self.router.add_route(routerObj.method, routerObj.route, RouterCallBack(routerObj, self, routerObj.system))
                Appointed2WebApp.logger.info('成功添加模块：‘%s’, 路由: %s' % (packname, str(routerObj)))
                # 初始化路由的基本信息
                self.runtimeInfo.changeEnableStatus(routerObj.flagName, routerObj.enable)