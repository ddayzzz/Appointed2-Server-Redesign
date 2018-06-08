# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['CmdLineToGet_Public',
           'maintenance_index', 'maintenance_getStatus', 'maintenance_setRouterStatus',
           'main_close', 'main_disable_package', 'main_restart', 'main_restart_enterMan', 'main_close_notCallMonitor',
           'user_authenticate', 'user_signin', "user_api_register", "user_register", "user_api_siginout", "user_api_getadminensureid",
           "package_processUpload", 'package_processInstall', 'ut'
]
__doc__ = '提供基本的Appointed2工具函数'
__cmdLines__ = {  # 用于指定工具的命令行的参数(面向用户)

}

import json
from packages import regPackage as _reg
from packages import uploader, TemplateManager
# 添加其他的包
from . import process_parseCmdLine
from . import process_maintenance
from . import process_main
from . import process_usermgr

@_reg.get('/upload')
def ut():
    return {'__template__': 'uploader2.html'}

@_reg.get('/api/runCmd/{packageName}/{cmdName}')
async def CmdLineToGet_Public(app, packageName, cmdName, **kwargs):
    """通过指定命令名称和命令行运行对应的命令，如果成功，将会重定向到指定的网页。如果不成功，将会转到错误处理的界面
    cmdname：命令名称
    cmdline：命令行。注意：按照短命令（没有值），长命命令（没有值），短命令参数，长命令参数，选项的顺序
    redirectType：发生重定向的类型。默认为api：将会返回json格式的数据，normal：使用网页显示
    示例：
    localhost:9000/api/runCmd/WordBook/word?cmdLine="word --force=yd bear apple"
    localhost:9000/api/Runcmd?cmdname=word&cmdline="word --force=yd bear apple"&redirectType=normal
    localhost:9000/api/Runcmd?cmdname=word&cmdline="word --help --force=yd bear apple"&redirectType=normal
    """
    cmdLine = kwargs.get('cmdLine', None)
    red = kwargs.get('redirectType', 'api')
    packMgr = app.topServer.packagesMgr
    return process_parseCmdLine.parseCmdLine(packageName, cmdName, cmdLine, red, packMgr)


@_reg.get('/admin', adminLevel=True)
def maintenance_index(app):

    # 确定是否已经进入了维护模式
    enterMan = app.topServer.isMaintenance
    # data = {'__template__': 'Common/maintenance_index.html',
    #         'maintenance': enterMan,
    #         'installedPackages': process_maintenance.getInstalledPackages(app)}
    # data.update(uploader.generateUploader(title='上传安装包',
    #                                       description='请上传一个 Appointed2 子模块安装包，通常是是一个 gzip 文件',
    #                                       multiple=True, '*(tar)', '/api/package/upload', success='{process_install(returndata);}'))
    data = TemplateManager.RenderingTemplateInfo('Common/maintenance_index.html')
    data.add_upload(title='上传安装包',
                    description='请上传一个 Appointed2 子模块安装包，通常是是一个 gzip 文件，后缀为 tar.gz',
                    multiple=True,
                    accept='*(tar.gz)',
                    uploadurl='/api/package/upload',
                    success='{process_install(returndata);}',
                    filter='application/x-gzip',
                    templateAnchor='upload_package')
    data.add_renderKws(maintenance=enterMan, installedPackages=process_maintenance.getInstalledPackages(app))
    return data

@_reg.get('/api/maintenance/getStatus')
def maintenance_getStatus(app):
    """
    获取服务运行的状态信息。已经安装的信息
    :param app: 默认的底层服务信息
    :return:
    """
    return {'runningTimeInfo': app.runtimeInfo}


@_reg.get('/api/maintenance/setRouterStatus/{packageName}/{routerFlagName}', adminLevel=True)
def maintenance_setRouterStatus(app, packageName, routerFlagName, **query):
    """
    设置路由的状态，默认的请阔可以设置路由的一些信息。但目前只设置启用状态
    :param app: 底层服务器
    :param query: payload，目前支持 enable
    :return:
    """
    return process_maintenance.setRouterInfo(app, packageName, routerFlagName, **query)

# main
@_reg.get('/api/main_disable/{packname}', adminLevel=True)
def main_disable_package(app, packname):
    """
    关闭整个模块
    :param app: 底层服务器名
    :param packname: 模块名
    :return:
    """
    process_main.main_disable_package(app, packname)


@_reg.get('/api/main_close/notCallMonitor', adminLevel=True)
def main_close_notCallMonitor(app):
    """
    关闭服务器但是不通知监控
    :param app: 底层服务器
    :return:
    """
    process_main.main_close_notCallMonitor(app)

@_reg.get('/api/main_close', adminLevel=True)
def main_close(app):
    """
    将Apoointed2 的服务关闭
    """
    process_main.main_close(app)

@_reg.get('/api/main_restart', adminLevel=True)
def main_restart(app):
    """
    通知监控程序，重启服务
    :param app:
    :return:
    """
    process_main.main_restart(app)


@_reg.get('/api/main_restart/enterMaintenance', adminLevel=True)
def main_restart_enterMan(app):
    """
    通知监控程序重启服务，但是进入维护模式
    :param app:
    :return:
    """
    process_main.main_restart_enterMan(app)


# 用户管理
@_reg.get('/signin')
def user_signin(redirect='/', message=None):
    return {'__template__': 'Common/signin.html', 'redirect': redirect, 'message': message}


@_reg.post('/api/user/authenticate')
async def user_authenticate(app, email, passwd):
    db_pool = app.topServer.dbPool
    if not db_pool:
        raise ValueError('没有可用的数据库连接池')
    return (await process_usermgr.authenticate(db_pool, email, passwd))


@_reg.post('/api/user/register')
async def user_api_register(app, email, name, passwd, admin_ensureid):
    db_pool = app.topServer.dbPool
    if not db_pool:
        raise ValueError('没有可用的数据库连接池')
    usr_response = await process_usermgr.create(db_pool, name=name, email=email, password_hash=passwd, admin_ensureid=admin_ensureid)
    return usr_response  # 返回一个登陆状态的cookies响应


@_reg.get('/register')
def user_register(redirect='/'):
    return {'__template__': 'Common/register.html', 'redirect': redirect}


@_reg.get('/api/user/signout')
def user_api_siginout(request):
    r = process_usermgr.signout(request)
    return r


@_reg.get('/api/user/getadminensureid')
def user_api_getadminensureid():
    return '0bc5b86f7e041d4debc9439928848376e67eb134'  # naive的sha1加密值


# 上传部分
@_reg.post('/api/package/upload', adminLevel=True)
async def package_processUpload(request):
    return await process_maintenance.package_processUpload(request)

# @_reg.post('/api/package/createInstallRequests', adminLevel=True)
# def package_createInstallRequests(uploadResult):
#     """
#     创建安装的请求对象
#     :param uploadResult: 上传的结果，这个对应于 uploader 返回的结果
#     :return:
#     """
#     if len(uploadResult) <= 1:
#         raise ValueError('没有上传指定的文件')
#     return process_maintenance.package_createInstallRequest(uploadResult[0], uploadResult[1:])


@_reg.get('/ws/package/processInstall', adminLevel=True)
async def package_processInstall(wsResponse, app, uploadResult):
    uploadResultObj = json.loads(uploadResult)
    files = uploadResultObj['uploadResult']
    return await  process_maintenance.package_processInstall(files[1:], app.topServer.loop, wsResponse)



