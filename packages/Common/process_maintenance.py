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
from queue import Queue
import json

_logger = logger.get_logger('Maintenance')



class RemoteInstallRequest(setupTool.InstallRequest):
    """
    远程用户的请求安装处理
    """

    def __init__(self, packageFile, requestId):
        super(RemoteInstallRequest, self).__init__(packageFile, True)  # 制定了安装文件，并且立即显示日志到文件
        self.requestId = requestId

    def __dict__(self):
        if not getattr(self, 'packageStatus', None) or not getattr(self, 'packageInfoObj', None):
            return {'name': '未知', 'version': '未知', 'author': '未知'}
        else:
            return self.packageInfoObj.__dict__()



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
    :return: 返回一个已经构造的响应类型 是 WebResponse 的子类
    """
    # 阶段1：获取信息（获取所有的包的信息）
    p1 = setupTool.CheckPackageInfoHandler()
    p2 = setupTool.ExtractPackageHandler()
    # 阶段2：读取有关的数据
    p3 = setupTool.ProcessInstallHandler()
    p4 = setupTool.CleanExtractDirHandler()
    p1.setSuccessor(p2)
    # 发送安装包的数量
    await ws.send_str('IT:%d' % len(filenames))
    # 获取所有的信息
    installQueue = Queue()
    for filepath in filenames:
        keyname = 'InstallRequest-' + str(time.time()).replace('.', '-')
        request = RemoteInstallRequest(packageFile=filepath, requestId=keyname)
        p1.handle(request)
        # 加入执行安装的队列
        installQueue.put(request)
        # 输出相关的信息
        await ws.send_str('BI:%s' % keyname)
        await ws.send_str(json.dumps(request, default=lambda o: o.__dict__()))
    while not installQueue.empty():  # 只要还有任务
        request = installQueue.get()
        if not request.packageStatus in setupTool.ACCEPT_CONTINUE_INSTALLATION:
            # 完全不合法的安装包信息
            # 输出错误信息
            for msg in request.logs:
                await ws.send_str(msg)
            # 结果是错误的
            await ws.send_str('EI:%s,Result:%s' % (request.requestId, 'Failed'))
            continue
        # 继续安装
        p3.handle(request)
        p4.handle(request)
        # 最后输出日志
        for msg in request.logs:
            await ws.send_str(msg)
        await ws.send_str('EI:%s,Result:%s' % (request.requestId, 'Done' if request.installStatus else 'Failed'))
    # await ws.send_str(json.dumps(res, default=lambda o: o.__dict__()))
    await ws.close()
    return ws










