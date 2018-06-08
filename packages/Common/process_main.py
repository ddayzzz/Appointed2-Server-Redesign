# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['main_restart','main_close', 'main_disable_package', 'main_close_notCallMonitor', 'main_restart_enterMan'
]
__doc__ = '提供Appointed2服务器的响应功能，通过命令行格式'
__cmdLines__ = {  # 用于指定工具的命令行的参数(面向用户)
}

from packages import regPackage as _reg, logger


# @_reg.get('/api/main_install')
# def main_install(app, file, packname):
#     """
#     安装
#     :param app:
#     :param file:
#     :param packname:
#     :return:
#     """
#     result = ''
#     logger.get_logger().info('正在安装来自用户请求安装‘%s’，来自文件：‘%s’' % (packname, file))
#     # obj = setupTool.Install(file, packname)
#     # if obj and obj.valid:
#     #     result = '成功安装‘%s’，来自文件：‘%s’。安装的版本：%s，作者：%s\nAppointed2重启后生效' % (packname, file, obj.version, obj.autor)
#     #     # 通知用户重启，而不是每安装一次就重启
#     # else:
#     #     result = '安装‘%s’，来自文件：‘%s’ 失败。' % (packname, file)
#     # return result
#     # 需要关闭服务器，但是本程序不重新启动

def main_restart(app):
    """
    通知监控程序，重启服务
    :param app:
    :return:
    """
    app.topServer.user_restart(False)


def main_restart_enterMan(app):
    """
    通知监控程序重启服务，但是进入维护模式
    :param app:
    :return:
    """
    app.topServer.user_restart(True)



def main_close(app):
    """
    将Apoointed2 的服务关闭
    """
    app.topServer.user_close()



def main_close_notCallMonitor(app):
    """
    将Apoointed2 的服务关闭，并且不会通知监控程序
    """
    app.topServer.user_close(False)



def main_disable_package(app, packname):
    """将Apoointed2 的某个服务关闭：他的路由功能不再可用。
    """
    mgr = app.topServer.packagesMgr  # 这个是 Appointed2 的网站服务器的顶层服务器的模块管理工具
    mgr.disablePackage(packname)
    # 如果没有异常的话

