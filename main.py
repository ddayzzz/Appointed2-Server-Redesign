# coding=utf-8
__doc__ = '这个是服务器的主程序（Linux/Unix），可以创建多个服务的实例'
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
import subprocess
import sys
import os
import signal
import time
import config
import getopt
import initEnv
from packages import logger, macros


class RunInfo():
    __doc__ = '定义服务的设置信息，可以转换为参数信息'

    def __init__(self, maintanceMode=False):
        """
        初始化运行参数
        :param maintanceMode: 是否是维护模式（仅仅启动必要的模块）
        """
        self._configMgr = config.getConfigManager()
        self.cmds = dict()
        self.noValsArgs = list() # 这个是针对没有指定参数的
        self.noOptsArgs = list() # 不要指定开关的参数
        self.pythonExec = sys.executable
        self.serverFileName = 'server.py'
        self._setDefaultAddress()
        self._setSignalNum(os.name)
        self._setLoadPackages(maintanceMode)
        self._setDatabaseInfo()
        # 根据实际设置参数
        self._checkCmdLine()
        # 设置监控程序 pid
        self.cmds['monitorpid'] = os.getpid()
        # 是否与用户交互
        self.interactive = self._configMgr['interactive']

    def _setLoadPackages(self, maintanceMode):
        packages = self._configMgr.getInstalledPackages()
        if maintanceMode:
            self.noOptsArgs = [name for name, infos in packages.items() if infos['main_package']]


    def _setSignalNum(self, sysname):
        """
        设置信号
        :param sysname: 系统名称, nt 等
        :return:
        """
        if sysname == 'nt':
            re_signal = int(self._configMgr['restart_signnum_win'], base=16)
            cl_signal = int(self._configMgr['close_signnum_win'], base=16)
            re_main_signal = int(self._configMgr['restart_enter_maintenance_win'], base=16)
        else:
            # 关联重启信号
            re_signal = self._configMgr['restart_signnum_unix']
            # 关联关闭服务信号
            cl_signal = self._configMgr['close_signnum_unix']
            re_main_signal = self._configMgr['restart_enter_maintenance_unix']
        self.cmds['closeSignal'] = cl_signal
        self.cmds['restartSignal'] = re_signal
        self.cmds['maintenanceSignal'] = re_main_signal  # 重启进入

    def _setDefaultAddress(self):
        """
        设置服务端绑定的端口（仅仅是默认值，需要解析系统的参数）
        :param sysname:
        :return:
        """
        p = self._configMgr['port']
        i = self._configMgr['host']
        self.cmds['port'] = p
        self.cmds['host'] = i

    def _setDatabaseInfo(self):
        """
        设置数据连接的参数
        :return:
        """
        db_obj = self._configMgr.get("mainDatabase", None)
        if not  db_obj:
            return
        db_name = "mysql"  # 目前这个版本的数据库
        db_username = db_obj['username']
        db_password = db_obj['password']
        db_addr = db_obj['address']
        db_port = db_obj['port']
        db_dbname = db_obj['dbname']
        # 写入参数
        self.cmds['dbname'] = db_name
        self.cmds['dbusername'] = db_username
        self.cmds['dbpassword'] = db_password
        self.cmds['dbaddress'] = db_addr
        self.cmds['dbport'] = db_port
        self.cmds['dbdbname'] = db_dbname



    @staticmethod
    def printUsage():
        print('用法 %s [-h][-p][-l] [--help][--host][--port][--nologout] args' % sys.argv[0])

    def _checkCmdLine(self):
        """
        这个根据指定的程序命令进行解析
        :return:
        """
        options, noOptArgs = getopt.getopt(sys.argv[1:], 'h:p:n',
                                           ('host=', 'port=', 'nologout', 'help'))  # 目前仅支持这些参数
        for name, value in options:
            if name in ('-h', '--host'):
                self.cmds['host'] = value
            elif name in ('-p', '--port'):
                self.cmds['port'] = value
            elif name in ('-n', '--nologout'):
                self.noValsArgs.append('--nologout')
            elif name == '--help':
                RunInfo.printUsage()
            else:
                raise ValueError("未知的参数：‘%s’" % name)

    def getInstalledPackages(self):
        """
        获取已经安装的包内容
        :return: 返回一个 dict表示 packagename->信息关联
        """
        _installed = self._configMgr.get('installed', None)
        if not _installed:
            return dict()  # 不存在信息
        return _installed




    def generateCommandLine(self):
        """
        生成可以运行的命令行格式
        :return: 返回一个列表，形式[参数，值], 统一使用长格式
        """
        cmd = [self.pythonExec, self.serverFileName]

        # 长参数，且有值
        for k, v in self.cmds.items():
            cmd.extend(('--%s' % k, str(v)))
        # 无参数
        cmd.extend(self.noValsArgs)
        # 无开关
        cmd.extend(self.noOptsArgs)
        return cmd


def getSignalIDByStr(signalStr):
    si = getattr(signal, signalStr, None)
    if si:
        return si
    else:
        raise ValueError('signal 模块没有包含信号字符串：‘%s’' % signalStr)


if os.name == 'nt':
    import monitor_win_hook as hooker
    import win32gui
    import win32con
    from libs import sendMessage

__process = None
__runInfo = RunInfo()
__runInfo_maintance = RunInfo(True)



def process_kill():
    """
    这个是服务端通知关闭调用的情况
    :return:
    """
    global  __process
    if __process:
        __process.wait()  # 接收到信号的时候已经关闭了，只需要等待退出即可
        __process = None


def process_start(runInfo):
    global  __process
    cmds = runInfo.generateCommandLine()
    __process = subprocess.Popen(cmds, cwd=os.path.realpath('.'), stderr=sys.stderr, stdin=sys.stdin,
                                 stdout=sys.stdout,
                                 shell=False)

def process_ctrlc():
    """
    在 Windows 下运行的时候，按 ctrl+c 表示的就是退出程序。这个作为信号 WM_CLOSE 传送给了注册的消息
    :return:
    """
    if __process:
        # 如果这个进程还是存在，向 http 端口发送关闭？
        try:
            from urllib import request
            r = request.Request(url='http://{host}:{port}/api/main_close/notCallMonitor'.format(host=__runInfo.cmds['host'],
                                                                                                port=__runInfo.cmds['port']))
            request.urlopen(r)  # 不需要返回值
        except ConnectionResetError as e:
            pass
        # __process.wait()
    else:
        # 如果这个进程已经退出
        pass  # 不会有这种情况


def onReceive_killSignal(num, st):
    """
    Linix 下关闭服务的信号
    :param num:
    :param st:
    :return:
    """
    global __process
    if __process:
        __process.send_signal(signal.SIGTERM)
        __process.wait()
        __process = None
    else:
        # 这个表示程序已经退出 但是还是被要求结束，直接结束程序
        raise KeyboardInterrupt



def process_restart(enterMaintenance=False):
    """
    处理监控程序发送的重启服务
    :param enterMaintenance:
    :return:
    """
    process_kill()
    if enterMaintenance:
        process_start(__runInfo_maintance)
    else:
        process_start(__runInfo)


def user_run(runInfo):
    process_start(runInfo)
    if os.name != 'nt':
        try:
            while True:
                time.sleep(0.01)
                if not __process:  # 如果已经终止， 退出
                    break
        except KeyboardInterrupt:
            pass
        process_kill()
    else:
        sin_win_restart = runInfo.cmds['restartSignal']
        sin_win_close = runInfo.cmds['closeSignal']
        sin_win_restart_enterMan = runInfo.cmds['maintenanceSignal']
        hooker.init(close_signalnum=sin_win_close, restartsignalnum=sin_win_restart,
                    closecall=process_kill, restartcall=process_restart, ctrlccall=process_ctrlc,
                    restartToManCall=lambda: process_restart(True), restartToManSignalnum=sin_win_restart_enterMan)
        hwnd, wc = hooker.regHook()
        # Windows 消息循环
        try:
            while __process:
                time.sleep(0.01)
                win32gui.PumpWaitingMessages()
        except KeyboardInterrupt:
            pass
        # 注意：需要向隐藏的窗体发送关闭消息
        sendMessage.send(os.getpid(), win32con.WM_MOUSEMOVE)
        hooker.destroy()


def user_display_installedPackages():
    rets = "\n已安装的模块：%d\n        模块名称|        版本|是否启用|系统模块\n%s"
    installed = __runInfo.getInstalledPackages()
    s = '\n'.join(['%16s|%12s|%8s|%8s' % (infos['name'], infos['version'], str(infos['enable']), str(infos['system'])) for k, infos in installed.items()])
    return rets % (len(installed), s)

if __name__ == '__main__':
    # 初始化环境
    initEnv.InitEnv(True)
    # 初始化logger 输出
    logger.init_logger(macros.sep.join((macros.Macro('LOGROOT'), 'main-%s.log' % str(time.time()))), True)
    if os.name != 'nt':
        signal.signal(signal.SIGTERM, onReceive_killSignal)  # 这个是默认的，用于关闭整个程序，Linux
        # 关联其他信号
        signal.signal(getSignalIDByStr(__runInfo.cmds['closeSignal']), lambda n,s:process_kill())
        signal.signal(getSignalIDByStr(__runInfo.cmds['restartSignal']), lambda n, s: process_restart())
        signal.signal(getSignalIDByStr(__runInfo.cmds['maintenanceSignal']), lambda n, s: process_restart(enterMaintenance=True))
    interactive = __runInfo.interactive
    # 进行用户交互
    if not interactive:
        code = 'RUN'
    else:
        code = ''
    try:
        while code != 'EXIT':
            if code == 'RUN':
                user_run(__runInfo)
            elif code == 'RUN MAINTANCE':
                user_run(__runInfo_maintance)
            elif code == 'LIST PACKAGES':
                print(user_display_installedPackages())
            elif code == 'I':
                from packages import setupTool
                setupTool.installPackage(setupTool.InstallRequest('测试安装2.tar.gz', immDisplayLogs=True))
            elif code == 'U':
                from packages import setupTool
                setupTool.uninstallPackage(setupTool.UninstallRequest('WordBook', True))
            elif code == 'M':
                from packages import tools
                s, o,e = tools.installDependentModules(['aiohttp', 'reques'])
                print(s, o, e)
            else:
                pass
            if interactive:
                code = input('\n>>>').upper()
            else:
                break  # 不需要交互直接退出
    except KeyboardInterrupt:
        pass








