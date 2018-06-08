# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = [''
]
__doc__ = '维护模式功能 - 维护模式'
import config
from packages import logger, uploader
from packages import setupTool
import time
import aiohttp
import json

_logger = logger.get_logger('Maintenance')



class RemoteInstallRequest(setupTool.InstallRequest):
    """
    远程用户的请求安装处理
    """

    def __init__(self, packageFile):
        super(RemoteInstallRequest, self).__init__(packageFile, True)  # 制定了安装文件，并且立即显示日志到文件

    def __dict__(self):
        if not getattr(self, 'infoObject', None):
            return {}
        return self.infoObject



def getInstalledPackages(app):
    if app.topServer.isMaintenance:
        # 进入了维护模式，直接加载 config 的已经安装的模块，可以确保只有 main 和 Common 被载入。所以读取config
        installed = config.getConfigManager().getInstalledPackages()
        return installed
    packmgr = app.topServer.packagesMgr
    if not packmgr:
        return '维护服务不可用'
    data = packmgr.loadedPackages
    return data


def getMacros():
    pass

def setRouterInfo(app, packname, routerStr, **kwargs):
    """
    修改指定路由的信息
    :param app: 顶层
    :param packname: 路由隶属的模块名称
    :param routerStr: 路由的标志
    :param kwargs: 设置的属性-值
    :return:
    """
    packMgr = app.topServer.packagesMgr
    # 获取模块对象
    packObj = packMgr.findByName(packname)
    if not packObj:
        _logger.error('没有找到指定的模块名称：‘%s’' % packname)
    # 设置参数
    res, robj= packObj.setRouter(routerStr, **kwargs)
    # 查看是否需要通知运行信息
    if kwargs.get('enable', None) != None:
        # 修改运行的信息
        app.runtimeInfo.changeEnableStatus(routerStr, robj.enable)
    return {'result': res}


async def package_processUpload(request):
    """
    处理上传
    :param request: 用户请求
    :return:
    """
    files = await uploader.store_upload_resources(request, 'packageFiles')
    res = {'uploadResult': files}
    return res


async def package_processInstall(filenames, loop, ws):
    """
    创建安装包到安装请求的映射
    :param filenames: 文件名
    :param loop:异步事件循环
    :param ws:websocket 对象
    :return: 返回字典：请求id->请求对象
    """
    p1 = setupTool.PackageFileHandler()
    p2 = setupTool.CheckPackageInfoHandler()
    # 阶段2
    p3 = setupTool.ProcessInstallHandler()
    p4 = setupTool.CleanExtractDirHandler()
    p1.setSuccessor(p2)

    await ws.send_str('IT:%d' % len(filenames))
    for filepath in filenames:
        keyname = 'InstallRequest-' + str(time.time()).replace('.', '-')
        await ws.send_str('BI:%s' % keyname)
        # 继续添加
        rr = RemoteInstallRequest(packageFile=filepath)
        # 为了读取基本的信息
        p1.handle(rr)
        # 输出基本的信息
        await ws.send_str(json.dumps(rr, default=lambda o: o.__dict__()))
        # 继续安装
        p3.handle(rr)
        p4.handle(rr)
        # 最后输出日志
        for msg in rr.logs:
            await ws.send_str(msg)
        await ws.send_str('EI:%s,Result:%s' % (keyname, 'Done' if rr.installStatus else 'Failed'))
    # await ws.send_str(json.dumps(res, default=lambda o: o.__dict__()))
    await ws.close()
    return ws










