# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['run']
__doc__ = 'Appointed2服务器定义'
import getopt
import sys
import signal
import traceback
import asyncio
from factories import data_factory, logger_factory, response_factory, requestCheck_factory
import Appointed2WebApp
from packages import Package, logger, macros
import subprocess
import os
import time
import initEnv
__usage = '用法 %s [-h][-p][-l] [--help][--host][--port][--nolog] args' % sys.argv[0]
__logger = logger.get_logger()
__run_loop = asyncio.get_event_loop()


def onSignal_KILL(signalNum, stackFrame):
    """
    处理系统的 SIGTERM 终止信号
    :param signalNum: 信号编号
    :param stackFrame: 栈
    :return: 不返回值
    """
    __logger.info('处理关闭服务信号')
    raise KeyboardInterrupt()




class Appointed2Server(object):

    def __init__(self, **kwargs):
        # 日志记录
        self._init_log(kwargs['logout'])
        # 必须属性
        self.host = kwargs['host']  # 默认绑定的 IP 地址
        self.port = kwargs['port']  # 默认的端口号
        self.loop = kwargs['loop']   # 获取主默认的消息循环
        # self.configMgr = kwargs['configMgr']  # 绑定的设置管理器
        self.closeSignal = kwargs['closeSignal']  # 通知监控程序的关闭信号
        self.restartSignal = kwargs['restartSignal'] # 通知监控程序的重启信号
        self.app = Appointed2WebApp.Appointed2WebApp(loop=self.loop, middlewares=[
            logger_factory.logger_factory, requestCheck_factory.requestCheck_factory, data_factory.data_factory, response_factory.response_factory
        ], topServer=self)
        # 初始化其他的部件
        self.app.init_template(paths=['templates'])
        self.app.add_statics({'/static/': 'static'})
        # self.app.on_cleanup.append(self.close)
        # 加载模块管理器
        self.packagesMgr = Package.PackagesManager()
        self.packagesMgr.loadPackages()
        # 服务器主路由
        modObj = __import__('mainRouters', globals(), locals(), tuple())
        mainPackage = Package.Package('main', modObj)
        self.packagesMgr.addPackage(mainPackage)
        # 添加模块的路由
        self.app.add_routersBridge(self.packagesMgr)
        # 创建服务器实例
        handler = self.app.make_handler()
        # 创建服务器
        srv = self.loop.run_until_complete(self.loop.create_server(handler, self.host, self.port))
        # 添加资源
        # 设置其他的属性
        self.server = srv
        self.handler = handler
        self.isRunning = False

    async def _init_database(self):
        # 初始化数据库
        # await init_database(self.loop)
        pass

    def close(self):
        if not self.isRunning:
            return
        # self.loop.run_until_complete(dbManager.destroyPool())
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.run_until_complete(self.app.shutdown())
        self.loop.run_until_complete(self.handler.shutdown(60.0))
        self.loop.run_until_complete(self.app.cleanup())
        self.isRunning = False  # 服务关闭
        print('closed')

    def run(self):
        if self.isRunning:
            return
        self.isRunning = True
        logger.get_logger().info('Appointed2 正在监听：http://%s:%d' % (self.host, self.port))
        self.loop.run_forever()
        # aiohttp.web.run_app(self.app, host=self.host, port=self.port)

    def _init_log(self, toScreen):
        # 初始化日记系统
        fp = os.path.sep.join((macros.Macro('LOGROOT'), 'log-%s.txt' % str(time.time())))
        logger.init_logger('Server', fp, toScreen, False)


    def restart_server(self):
        """
        重启服务：直接停止事件循环，并向监控程序发送消息
        :return:
        """
        __logger = logger.get_logger()
        __logger.info('正在重启 Appointed2 服务')
        mpid = macros.Macro('MONITOR_PID', False)
        sig = self.restartSignal
        if mpid:
            if os.name == 'nt':
                from libs import sendMessage as t
                # 获取重启的信号
                __logger.info('向监控进程 ‘%d’ 发送重启信号：‘%s’' % (mpid, sig))
                self.loop.stop()
                t.post(mpid, int(sig))
            else:
                self.loop.stop()
                subprocess.Popen(['kill', '-' + sig, str(mpid)])  # 默认是 SIGUSR2 信号
                __logger.info('成功向监控进程 ‘%d’ 发送重启信号：‘%s’' % (mpid, sig))

    def close_server(self, sendSignal=True):
        """
        调用对象的关闭服务
        :param sendSignal: 是否向宿主程序发送信号
        :return:
        """
        __logger = logger.get_logger()
        __logger.info('正在关闭 Appointed2 服务')
        mpid = macros.Macro('MONITOR_PID', False)
        sig = self.closeSignal
        if mpid:
            if os.name == 'nt':
                from libs import sendMessage as t
                # 获取重启的信号
                __logger.info('向监控进程 ‘%d’ 发送关闭信号：‘%s’' % (mpid, sig))
                self.loop.stop()
                if sendSignal:
                    t.post(mpid, int(sig))
            else:
                self.loop.stop()
                subprocess.Popen(['kill', '-' + sig, str(mpid)])  # 默认是 SIGUSR2 信号
                __logger.info('成功向监控进程 ‘%d’ 发送关闭信号：‘%s’' % (mpid, sig))

def run():
    """
    运行服务
    :return: 不返回值
    """
    try:
        initEnv.InitEnv(True)
        # 加载配置设置器
        kws = dict()  # 运行参数
        loop = asyncio.get_event_loop()
        kws['loop'] = loop
        kws['logout'] = True
        print(sys.argv)
        options, noOptArgs = getopt.getopt(sys.argv[1:], 'm:h:p:r:c:n', ('host=', 'port=', 'monitorpid=',
                                                                     'restartSignal=', 'closeSignal=',
                                                                     'nologout'))
        for name, value in options:
            if name in ('-h', '--host'):
                kws['host'] = value
            elif name in ('-p', '--port'):
                kws['port'] = int(value)
            elif name in ('-n', '--nologout'):
                kws['logout'] = False  # 不显示输出
            elif name in ('-m', '--monitorpid'):
                # 设置监控器PID
                macros.SetMacro('MONITOR_PID', int(value))
            elif name in ('--restartSignal', '-r'):
                kws['restartSignal'] = value
            elif name in ('--closeSignal', '-r'):
                kws['closeSignal'] = value
            else:  # 不允许有不同的参数。可能以后会有可选的配置
                __logger.error('未知的参数 ‘%s’' % name)
                exit(2)
        macros.SetMacro('HOST', kws['host'])
        macros.SetMacro('PORT', kws['port'])
        macros.SetMacro('ADDRESS', 'http://%s:%d' % (kws['host'], kws['port']))
        signal.signal(signal.SIGTERM, onSignal_KILL)
    except Exception as e:
        __logger.error('无法运行Appointed2服务器，因为出现错误%s，消息：%s\n%s' % (str(type(e)), str(e.args),
                                                                            traceback.format_exc()))
    else:
        try:
            # print(macros.macro)

            webApp_obj = Appointed2Server(**kws)
            # from packages import setupTool as st
            # st.Install('WordBook.zip', 'WordBook', webApp_obj)
            webApp_obj.run()
        except KeyboardInterrupt:
            pass
        __logger.info('再见')
        if webApp_obj:
            webApp_obj.close()


if __name__ == '__main__':
    run()
