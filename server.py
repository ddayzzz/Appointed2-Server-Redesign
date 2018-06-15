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
from factories import data_factory, logger_factory, response_factory, auth_factory
import config
import Appointed2WebApp
from packages import Package, logger, macros, dbManager
import subprocess
import os
import time
import initEnv
from BaseServer import BaseServer

__usage = '用法 %s [-h][-p][-l] [--help][--host][--port][--nolog] args' % sys.argv[0]


__logger_core = None

__run_loop = asyncio.get_event_loop()


def onSignal_KILL(signalNum, stackFrame):
    """
    处理系统的 SIGTERM 终止信号
    :param signalNum: 信号编号
    :param stackFrame: 栈
    :return: 不返回值
    """
    __logger_core.info('处理关闭服务信号')
    raise KeyboardInterrupt()


class Appointed2Server(BaseServer):

    logger = logger.get_logger('Server')

    def __init__(self, *args, **kwargs):
        super(Appointed2Server, self).__init__('服务端1')

        # 必须属性
        self.host = kwargs['host']  # 默认绑定的 IP 地址
        self.port = kwargs['port']  # 默认的端口号
        self.loop = kwargs['loop']   # 获取主默认的消息循环
        self.configMgr = kwargs['configMgr']  # 绑定的设置管理器
        self.closeSignal = kwargs['closeSignal']  # 通知监控程序的关闭信号
        self.restartSignal = kwargs['restartSignal'] # 通知监控程序的重启信号
        self.restartEnterManSignal = kwargs['maintenanceSignal']  # 重启进入维护模式的信号
        self.app = Appointed2WebApp.Appointed2WebApp(loop=self.loop, middlewares=[
            logger_factory.logger_factory,  data_factory.data_factory,
            auth_factory.auth_factory, response_factory.response_factory
        ], topServer=self)
        # 初始化其他的部件
        self.app.init_template(paths=['templates'])
        self.app.add_statics({'/static/': 'static', '/templates/':'templates'})
        # 加载模块管理器
        # args 是指定要加载的模块的名称
        self.packagesMgr = Package.PackagesManager(args)
        self.packagesMgr.loadPackages()
        # 服务器主路由
        # modObj = __import__('mainRouters', globals(), locals(), tuple())
        # mainPackage = Package.Package('main', modObj)
        # self.packagesMgr.addPackage(mainPackage)
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
        self.isMaintenance = False
        # 是否可以进行维护
        if len(self.packagesMgr.loadedPackages) == 1:
            self.isMaintenance = True
        # 初始化数据库
        db_name = kwargs.get('dbname', None)
        if not db_name:
            return   # 不需要数据库连接
        db_username = kwargs['dbusername']
        db_password = kwargs['dbpassword']
        db_addr = kwargs['dbaddress']
        db_port = kwargs['dbport']
        db_dbname = kwargs['dbdbname']
        self.dbPool = self.loop.run_until_complete(dbManager.createPool(self.loop, db_username, db_password, db_dbname, db_addr, db_port))

    def close(self):
        if not self.isRunning:
            return
        # self.loop.run_until_complete(dbManager.destroyPool())
        self.server.close()
        self.loop.run_until_complete(self.server.wait_closed())
        self.loop.run_until_complete(self.app.shutdown())
        self.loop.run_until_complete(self.handler.shutdown(60.0))
        self.loop.run_until_complete(self.app.cleanup())
        self.loop.run_until_complete(dbManager.destroyPool(self.dbPool))
        self.isRunning = False  # 服务关闭
        Appointed2Server.logger.info('Appointed2 服务已经关闭')

    def run(self):
        if self.isRunning:
            return
        self.isRunning = True
        Appointed2Server.logger.info('Appointed2 正在监听：http://%s:%d' % (self.host, self.port))
        self.loop.run_forever()
        # aiohttp.web.run_app(self.app, host=self.host, port=self.port)

    def user_restart(self, enterMaintenace=False):
        """
        重启服务：直接停止事件循环，并向监控程序发送消息
        :param enterMaintenace:是否进入维护模式？
        :return:
        """
        __logger = Appointed2Server.logger
        if enterMaintenace:
            __logger.info('正在重启 Appointed2 服务并进入维护模式')
        else:
            __logger.info('正在重启 Appointed2 服务')
        mpid = macros.Macro('MONITOR_PID', False)
        sig = self.restartEnterManSignal if enterMaintenace else self.restartSignal
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

    def user_close(self, sendSignal=True):
        """
        调用对象的关闭服务
        :param sendSignal: 是否向宿主程序发送信号
        :return:
        """
        __logger = Appointed2Server.logger
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
        global __logger_core
        initEnv.InitEnv(True)

        kws = dict()  # 运行参数
        loop = asyncio.get_event_loop()
        kws['loop'] = loop
        kws['logout'] = True
        # 加载配置设置器
        cfgr = config.getConfigManager()
        kws['configMgr'] = cfgr
        options, noOptArgs = getopt.getopt(sys.argv[1:], 'm:h:p:r:c:e:n',
                                           ('monitorpid=', 'host=', 'port=',
                                            'restartSignal=', 'closeSignal=',
                                            'dbname=', 'dbusername=', 'dbpassword=', 'dbaddress=', 'dbport=', 'dbdbname=',  # 数据库方面
                                            'maintenanceSignal=', 'nologout'))
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
            elif name in ('--closeSignal', '-c'):
                kws['closeSignal'] = value
            elif name in ('--maintenanceSignal', '-e'):
                kws['maintenanceSignal'] = value
            elif name in ('--dbname', ):
                kws['dbname'] = value
            elif name in ('--dbusername', ):
                kws['dbusername'] = value
            elif name in ('--dbpassword', ):
                kws['dbpassword'] = value
            elif name in ('--dbaddress', ):
                kws['dbaddress'] = value
            elif name in ('--dbdbname', ):
                kws['dbdbname'] = value
            elif name in ('--dbport', ):
                kws['dbport'] = int(value)
            else:  # 不允许有不同的参数。可能以后会有可选的配置
                print('%s\n\n未知的参数 ‘%s’' % (__usage, name), file=sys.stderr)
                exit(-1)
        # 是否限定了启动的限定的运行的模块
        if len(noOptArgs) == 0:
            # 读取所有的模块
            packages = cfgr.getInstalledPackages()
            noOptArgs = [name for name, infos in packages.items() if infos['enable']]
        macros.SetMacro('HOST', kws['host'])
        macros.SetMacro('PORT', kws['port'])
        macros.SetMacro('ADDRESS', 'http://%s:%d' % (kws['host'], kws['port']))
        signal.signal(signal.SIGTERM, onSignal_KILL)
        # 初始化日志系统
        fp = os.path.sep.join((macros.Macro('LOGROOT'), 'server-%s.txt' % str(time.time())))
        logger.init_logger(fp, kws['logout'])
        __logger_core = logger.get_logger()
    except Exception as e:
        msg = '无法运行Appointed2服务器，因为出现错误%s，消息：%s\n%s' % (str(type(e)), str(e.args),
                                                                          traceback.format_exc())
        if __logger_core:
            __logger_core.error(msg)
        else:
            print(msg, file=sys.stderr)
        exit(-1)
    else:
        webApp_obj = None
        try:
            # print(macros.macro)

            webApp_obj = Appointed2Server(*noOptArgs, **kws)
            webApp_obj.run()
        except KeyboardInterrupt:
            pass
        if webApp_obj:
            webApp_obj.close()


if __name__ == '__main__':
    run()
