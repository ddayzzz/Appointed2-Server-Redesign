# coding=utf-8

__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = []
__doc__ = '用于安装Appointed2以及支持的模块并提供安装、卸载、安装子模块等接口，以及定义一些在安装过程中起作用的工具函数'
import json
import os
import tarfile
from packages import macros, logger, tools
from collections import Iterable
import config
import shutil
import traceback
import time
from enum import Enum


class PackageStatus(Enum):
    CurrentVersion=1
    NewerVersion=2
    OlderVersion=3
    NotExists=4
    Invalid=5
    Valid = 6

# 用于保存可以继续安装的集中包的情况
ACCEPT_CONTINUE_INSTALLATION = (PackageStatus.NewerVersion, PackageStatus.NotExists)


class PackageInfo():
    """
    这个是安装包的描述信息
    """

    def __init__(self, packageFile):
        self.status = PackageStatus.Invalid
        self._gzipObj = None
        self.installedDirs = None
        self.installedFiles = None
        # 这个在一开始就检查安装包的各个信息
        gzipObj = None
        try:
            # 读取基本信息，
            gzipObj = tarfile.open(packageFile, mode='r:gz')
            # Bufferlike 对象
            buf = gzipObj.extractfile('package.json')
            infoObj = json.load(buf)
            # 读取信息
            if infoObj:
                self.name = infoObj['name']
                self.version = infoObj['version']
                self.platform = infoObj['platform']
                self.arc = infoObj['arc']
                self.author = infoObj['author']
                self.dependencies = infoObj['dependencies']
                self.apt2Version = infoObj['Appointed2Version']
                self.compile = infoObj['compile']
                self._gzipObj = gzipObj
                self.packageFile = packageFile
                self.status = PackageStatus.Valid

        except Exception as e:
            if gzipObj:
                gzipObj.close()
            self._gzipObj = None
            raise e

    def extract(self, extract_path, keyFiles, keyDirs):
        """
        解压缩 gzip 格式
        :param packageFile: 压缩版包文件
        :param extract_path: 解压的路径.由于使用了extract 所以会移除所有的 . 和 ..。以及类似于 //root 会变成 root，放在了extract_path 目录
        :param keyFiles: 可迭代对象，关键目录（大写）
        :param keyDirs : 可迭代对象，关键文件（大写）， 例如 ['PACKAGE.JSON']
        :return: 修改对象的值：解压的目录列表（忽略掉所有的关键文件夹），文件列表（忽略掉所有的关键文件）
        """
        files = []
        dirs = []
        if self.status == PackageStatus.Valid:
            names = self._gzipObj.getmembers()  # 获取所有的名称（文件夹和文件，TarInfo 对象）
            for name in names:
                # 检查每一个名称
                if name.isdir():
                    self._gzipObj.extract(member=name, path=extract_path)
                    if name.name.upper() not in keyDirs:
                        dirs.append(name.name)
                else:
                    self._gzipObj.extract(member=name, path=extract_path)
                    if name.name.upper() not in keyFiles:
                        files.append(name.name)
        self.installedDirs = dirs
        self.installedFiles = files

    def __dict__(self, appendOtherInfo=False):
        res = {
            'name': self.name,
            'version': self.version,
            'platform': self.platform,
            'arc': self.arc,
            'author': self.author,
            'dependencies': self.dependencies,
            'Appointed2Version': self.apt2Version,
            'compile': self.compile
        }
        if appendOtherInfo:
            res.update({'installedFiles': self.installedFiles, 'installedDirs': self.installedDirs})
        return res

    def close(self):
        if self._gzipObj:
            self._gzipObj.close()
            self._gzipObj = None






class BaseHandler():

    keyDirs = macros.Macro('KEYDIRS').split(';')  # 注意是关键文件夹名称的列表
    # cached_setup_dir = macros.Macro('CACHEDROOT') +  + 'temp_packages'  # 解压缩的临时文件夹
    configMgr = config.getConfigManager()

    logger = logger.get_logger()


    def __init__(self):
        self.successor = None

    def setSuccessor(self, successor):
        self.successor = successor

    def getSuccessor(self):
        return self.successor

    def handle(self, request):
        raise NotImplementedError('子类必须实现 handle')

    @staticmethod
    def generateExtractDir():
        """
        生成安全的解压目录
        :return:
        """
        return macros.sep.join((macros.Macro('CACHEDROOT'), 'InstallExtractDir-' + str(time.time())))

class BaseSetupRequest():
    _logFcnMap = {'info': BaseHandler.logger.info,
                  'debug': BaseHandler.logger.debug,
                  'warn': BaseHandler.logger.warn,
                  'error': lambda msg:BaseHandler.logger.error(msg, exc_info=True, stack_info=True),
                  'nerror': BaseHandler.logger.error}

    def __init__(self, immediatelyDisplayLogs=False):
        """
        基本的安装请求
        :param immediatelyDisplayLogs: 是否立即显示日志信息
        """
        self._logs = list()
        self._immLogs = immediatelyDisplayLogs

    def put(self, msg, msgType="info"):
        """
        将日志输出已经保存
        :param msg:消息
        :param msgType: 输出的日志的类型 debug，info，warn，error, nerror(不显示堆栈、错误等信息）
        :return:
        """
        if isinstance(msg, str):
            if self._immLogs:
                BaseSetupRequest._logFcnMap.get(msgType, BaseHandler.logger.info)(msg)
            self._logs.append(msg)
        elif isinstance(msg,Iterable):
            # 可迭代的对象
            if self._immLogs:
                for _, ms in enumerate(msg):
                    BaseSetupRequest._logFcnMap.get(msgType, BaseHandler.logger.info)(ms)
                self._logs.extend(msg)

    def extend(self, request):
        if not isinstance(request, BaseSetupRequest):
            raise ValueError("只支持对 BaseSetupRequest 的子类进行日志扩充")
        self._logs.extend(request._logs)

    @property
    def logs(self):
        return self._logs






class InstallRequest(BaseSetupRequest):

    def __init__(self, packagesFile, immDisplayLogs=False):
        super(InstallRequest, self).__init__(immediatelyDisplayLogs=immDisplayLogs)
        self.packageFile = packagesFile
        self.installStatus = False  # 是否完成安装



class ExtractPackageHandler(BaseHandler):
    """
    这个是读取某个压缩包的内容
    """
    def __init__(self):
        super(ExtractPackageHandler, self).__init__()


    def handle(self, request):
        """
        解压缩安装包信息
        :param request: 请求，需要使用属性 packageInfoObj, packageStatus
        :return:
        """
        # 这个是安装过程的需要
        zf = request.packageInfoObj
        try:
            if not request.packageInfoObj:
                request.put('没有指定的安装包信息', msgType='error')
                return
            if not request.packageStatus in ACCEPT_CONTINUE_INSTALLATION:
                # 不能继续安装的情况：信息不完整
                request.put('不能继续解压安装包过程：未满足安装条件')
                return
            ext_path = BaseHandler.generateExtractDir()
            kd = [d.upper() for d in macros.Macro('KEYDIRS').split(';')]
            kf = ('PACKAGE.JSON', )
            # 直接解压
            zf.extract(ext_path, kf, kd)
        except Exception as e:
            request.put('解压缩安装包失败：%s' % zf.packageFile, msgType='error')
            if request.packageInfoObj:
                request.packageInfoObj.close()  # 关闭已经打开的安装包
        else:
            if request.packageInfoObj:
                request.packageInfoObj.close()  # 关闭已经打开的安装包
            request.extractRoot = ext_path  # 这个设置的是解压的路径的根目录
            request.put('成功解压安装包：%s' % zf.packageFile)
            if super().getSuccessor():
                super().getSuccessor().handle(request)


class CheckPackageInfoHandler(BaseHandler):

    def __init__(self):
        super(CheckPackageInfoHandler, self).__init__()


    @staticmethod
    def _CheckInstalledInfo(packageInfoObj):
        """
        检查是否满足安装的标准
        :param packageInfoObj: 安装的信息
        :return: 返回 PackageStatus，（Staus, 消息）
        """
        a_arc = macros.Macro('ARC').upper()
        a_platform = macros.Macro('PLATFORM').upper()
        a_apt2Version = macros.Macro('VERSION')

        version = packageInfoObj.version  # 模块的版本
        platform = packageInfoObj.platform.upper()  # 支持的平台信息
        # dependencies = infoJsonObj['dependencies']  # 这个模块需要的python 模块
        arc = packageInfoObj.arc.upper()  # 获取体系结构信息
        ap2version = packageInfoObj.apt2Version  # 需要的版本
        name = packageInfoObj.name  # 模块名称
        # 是否满足安装平台
        if platform != 'ALL' and platform != a_platform:
            return (PackageStatus.Invalid, '不支持的平台：“%s”' % platform)
        # 是否满足安装平台的系统版本
        if arc != 'ALL' and arc != a_arc:
            return (PackageStatus.Invalid, '不支持的处理器体系结构：“%s”' % arc)
        # Appointed2 版本
        apt2cmp_first = ap2version.find(',')
        apt2cmp = ap2version[:apt2cmp_first]
        apt2targetver = ap2version[apt2cmp_first + 1:]
        pred = tools.compareVersion(a_apt2Version, apt2targetver, apt2cmp)  # 检查是否满足条件
        if not pred:
            return (
            PackageStatus.Invalid, "安装目标 Appointed2 版本：‘%s’ 不满足 %s ‘%s’" % (a_apt2Version, apt2cmp, apt2targetver))
        # 检查是否有已经存在的版本
        installed = BaseHandler.configMgr
        previousObj = installed.getInstalledPackages().get(name, None)  # 是否具有某个安装的信息，返回他的 infos
        if previousObj:
            cv = previousObj['version']
            opts = ('>', '<', '==')
            vs = (PackageStatus.NewerVersion, PackageStatus.OlderVersion, PackageStatus.CurrentVersion)
            for i, opt in enumerate(opts):
                res = tools.compareVersion(version, cv, opt)
                if res:
                    return (
                        vs[i], "安装的版本‘%s’ %s 已经安装的版本‘%s’" % (version, opts[i], cv))
        else:
            return (
                PackageStatus.NotExists, "安装的版本‘%s’" % version)

    def handle(self, request):
        """
        处理检查的任务
        :param request: 这个是安装的起始步骤
        :return:
        """
        packageInfoObj = None
        request.packageStatus = PackageStatus.Invalid
        try:
            packageInfoObj = PackageInfo(request.packageFile)
            if packageInfoObj.status != PackageStatus.Valid: #
                request.put('安装包无效：‘%s’' % packageInfoObj.packageFile, msgType='nerror')
                packageInfoObj.close()
                return
            status, msg = CheckPackageInfoHandler._CheckInstalledInfo(packageInfoObj)
            # 输出检查的信息
            request.put(msg)
            # 设置相关信息
            request.packageStatus = status
            request.packageInfoObj = packageInfoObj
            # 检查相关的信息
            if status == PackageStatus.CurrentVersion:
                request.put('安装失败：试图安装相同版本的模块‘%s’，版本：%s' % (packageInfoObj.name, packageInfoObj.version), msgType='nerror')
                packageInfoObj.close()
                return
            if status == PackageStatus.OlderVersion:
                request.put('安装失败：试图安装旧版本的模块‘%s’。冲突的版本：%s' % (packageInfoObj.name, packageInfoObj.version), msgType='nerror')
                packageInfoObj.close()
                return
            if status == PackageStatus.NewerVersion:
                request.put('安装程序将会安装新版的模块‘%s’，新版本：‘%s’' % (packageInfoObj.name, packageInfoObj.version), msgType='nerror')
                # 需要卸载
                request.put('正在卸载旧版本的模块')
                p1 = UninstallGetInfoHandler()
                p2 = UninstallDeleteFilesAndDirs()
                req = UninstallRequest(packageInfoObj.name, immDisplayLogs=False)
                p1.setSuccessor(p2)
                p1.handle(req)  # 处理卸载请求
                request.extend(req)
                request.put('卸载旧版本的模块成功')
        except Exception as e:
            request.put('检查信息失败', msgType='error')
            if packageInfoObj:
                packageInfoObj.close()
        else:
            if super().getSuccessor():
                super().getSuccessor().handle(request)


class ProcessInstallHandler(BaseHandler):

    def __init__(self):
        super(ProcessInstallHandler, self).__init__()


    @staticmethod
    def _processInfoFile(infoFile, packageInfoObj):
        """
        这个函数用来辅助处理模块的信息
        :param infoFile: 信息文件
        :param packageInfoObj: 信息文件的对象
        :return:
        """
        packname = packageInfoObj.name
        packversion = packageInfoObj.version
        targetFile = macros.sep.join((macros.Macro('CONFIGROOT'), '%s-%s.json' % (packname, packversion)))
        # json 写入到config目录的文件下
        with open(targetFile, 'w') as fp:
            i = packageInfoObj.__dict__(appendOtherInfo=True)
            json.dump(i, fp, indent=4)
        # 删除原始的信息
        os.remove(infoFile)
        return ['成功更新模块配置文件：%s' % targetFile]

    @staticmethod
    def _copyFilesAndDirs(temp_dir, target_dir):
        """
        处理安装
        :param temp_dir: 临时解压的文件夹
        :param target_dir: 目标移动的文件夹（通常是安装的目录）
        :return:
        """
        output = []
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        # 移动文件夹
        for dirname in os.listdir(temp_dir):
            completeDirname = macros.sep.join((temp_dir, dirname))  # 表示完整的文件夹名称
            if os.path.isdir(completeDirname):  # 如果是一个文件夹，这个文件夹的名称是Appointed2 自带的名称
                # 进入这个文件夹
                apt2dir = target_dir + macros.sep + dirname
                if not os.path.exists(apt2dir):
                    os.makedirs(apt2dir)
                # 需要将其中的文件全部复制到对应的目录中
                for name in os.listdir(completeDirname):
                    target_name = macros.sep.join((completeDirname, name))
                    tar_apt2 = macros.sep.join((apt2dir, name))
                    if os.path.isdir(target_name):
                        # copytree
                        output.append('复制文件夹 ‘{src}’ 到 ‘{target}’'.format(src=target_name, target=tar_apt2))
                        if os.path.exists(tar_apt2):
                            shutil.rmtree(tar_apt2)
                        shutil.copytree(target_name, tar_apt2)

                    else:
                        output.append('复制文件 ‘{src}’ 到 ‘{target}’'.format(src=target_name, target=tar_apt2))
                        if os.path.exists(tar_apt2):
                            os.remove(tar_apt2)
                        shutil.copyfile(target_name, tar_apt2)
            else:
                # 是一个文件，拷贝到 target目录下
                tar_file = macros.sep.join((target_dir, dirname))
                org_file = macros.sep.join((temp_dir, dirname))
                if os.path.exists(tar_file):
                    os.remove(tar_file)
                output.append('复制文件 ‘{src}’ 到 ‘{target}’'.format(src=org_file, target=tar_file))
                shutil.copyfile(org_file, tar_file)
        return output

    @staticmethod
    def _compileFiles(request):
        """
        编译相关的源文件
        :param request: 请求对象
        :return: 返回 状态(1没有编译，0 所有编译成功，-1 编译有错误)，新增文件列表
        """
        a_platform = macros.Macro('PLATFORM')
        infoObj = request.packageInfoObj
        cwd = request.extractRoot
        compile_obj = infoObj.compile
        status = 1
        files = []
        if not compile_obj:
            return 1, files
        # 查询编译的条件
        for compile_name, compile_info in compile_obj.items():
            platform = compile_info.get('platform', '')
            if platform.upper() == 'ALL' or platform.upper() == a_platform.upper():
                # 需要编译
                status, outfile, output, err = tools.compileDynamicExtension(compilerType=compile_info['compiler'],
                                                                    srcs=compile_info['srcs'],
                                                                    out=compile_info['out'],
                                                                    cwd=cwd)
                # 判断条件
                if status != 0:
                    request.put("编译对象‘%s’失败，返回值：%d。\n输出的信息：\n%s\n错误/警告输出：\n%s\n" % (compile_name,
                                                                                status, output, err))
                    return -1, files
                else:
                    request.put("编译对象‘%s’成功，返回值：%d。\n输出的信息：\n%s\n错误/警告输出：\n%s\n" % (compile_name,
                                                                                       status, output, err))
                    # 更新文件列表
                    files.append(outfile)
                    status = 0
        # 写入文件列表
        return status, files

    @staticmethod
    def _installDependcies(request):
        """
        编译相关的源文件
        
        :param request: 请求对象
        :return: 返回 状态(1没有安装，0 所有安装成功，-1 安装有错误)，安装的模块列表
        """
        infoObj = request.packageInfoObj
        cwd = request.extractRoot
        dep_obj = infoObj.dependencies
        status = 1
        mods = []
        if not dep_obj:
            return 1, mods
        # 查询所有的模块
        for modulename in dep_obj:
            request.put('正在安装 Python 模块：%s' % modulename)
            status, output, err = tools.installDependentModules((modulename, ), cwd=cwd)
            if status != 0:
                request.put("安装 Python 模块 ‘%s’ 失败，返回值：%d。\n输出的信息：\n%s\n错误/警告输出：\n%s\n" % (modulename,
                                                                                          status, output, err))
                return -1, mods
            else:
                request.put("成功安装 Python 模块 ‘%s’，返回值：%d。\n输出的信息：\n%s\n错误/警告输出：\n%s\n" % (modulename,
                                                                                          status, output, err))
                mods.append(modulename)
                status = 0
        # 写入文件列表
        return status, mods

    @staticmethod
    def _updateConfig(packageInfoObj):
        """
        更新已经安装的模块的信息
        :param packageInfoObj: 信息对象
        :return:
        """
        cfgmgr = BaseHandler.configMgr
        configObj = packageInfoObj.__dict__(appendOtherInfo=False)
        configObj['enable'] = True
        configObj['main_package'] = False
        configObj['configFile'] = macros.sep.join((macros.Macro('CONFIGROOT'), '%s-%s.json' % (packageInfoObj.name,
                                                                                               packageInfoObj.version)))
        cfgmgr.addInstalledPackageInfo(packageInfoObj.name, configObj)
        cfgmgr.save()
        return ['成功更新配置文件']

    def handle(self, request):
        """
        处理
        :param request: 需要参数  packageStatus infoFile infoObject installFiles installDirs extractRoot
        :return:
        """
        try:
            if not request.packageStatus in ACCEPT_CONTINUE_INSTALLATION:
                # 不能继续安装的情况：信息不完整
                request.put('不能继续解压安装包过程：未满足安装条件')
                return
            # 安装相关的模块
            ms, mmnames = ProcessInstallHandler._installDependcies(request)
            if ms == -1:
                request.put("安装一个或多个 Python 模块失败。", msgType='nerror')
                return
            elif ms == 0:
                request.put("成功安装一个或多个 Python 模块。")
            # 编译相关的文件
            cs, cfiles = ProcessInstallHandler._compileFiles(request)
            if cs == -1:
                request.put("编译一个或多个动态链接库失败。", msgType='nerror')
                return
            elif cs == 0:
                request.put("成功编译一个或多个动态链接库。")
                # 写入文件对象
                request.installFiles.extend(cfiles)
            # 不存在其他的内容
            originalInfo = macros.sep.join((request.extractRoot, 'package.json'))
            # 处理写入的模块信息
            request.put(ProcessInstallHandler._processInfoFile(originalInfo, request.packageInfoObj))
            # 复制已经解压缩的文件
            request.put(ProcessInstallHandler._copyFilesAndDirs(request.extractRoot, '.'))
            # 更新程序配置
            request.put(ProcessInstallHandler._updateConfig(request.packageInfoObj))

        except Exception as e:
            request.put('处理安装失败：\n%s\n' % traceback.format_exc())
        else:
            request.installStatus = True  # 完成安装
            request.put(
                "成功安装模块：‘{name}’，版本：‘{version}’，作者：‘{author}’，目标平台：‘{platform}’。".format(
                    name=request.packageInfoObj.name,
                    version=request.packageInfoObj.version,
                    author=request.packageInfoObj.author,
                    platform=request.packageInfoObj.platform
                ))

            if super().getSuccessor():
                super().getSuccessor().handle(request)


class CleanExtractDirHandler(BaseHandler):

    def __init__(self):
        super(CleanExtractDirHandler, self).__init__()

    def handle(self, request):
        temp = getattr(request, 'extractRoot', None)
        if temp and os.path.exists(temp):
            # 清除临时文件
            try:
                shutil.rmtree(temp)
            except Exception as e:
                request.put('删除临时目录失败：%s' % temp, msgType='nerror')
            else:
                request.put('删除临时目录：%s' % temp)
        if super().getSuccessor():
            super().getSuccessor().handle(request)


# 卸载部分
class UninstallRequest(BaseSetupRequest):

    def __init__(self, packageName, immDisplayLogs):
        super(UninstallRequest, self).__init__(immediatelyDisplayLogs=immDisplayLogs)
        self.packageName = packageName
        self.uninstallStatus = False  # 是否成功卸载


class UninstallGetInfoHandler(BaseHandler):
    """
    这个类处理卸载部分
    """
    def __init__(self):
        super(UninstallGetInfoHandler, self).__init__()

    def handle(self, request):
        """
        检查相关的信息
        :param request:
        :return:
        """
        try:
            name = request.packageName
            cfgMgr = BaseHandler.configMgr
            infos = cfgMgr.getInstalledPackages().get(name, None)
            if not infos:
                request.put('无法找到模块：‘%s’ 的安装信息' % name, msgType='nerror')
                return
            # 打开模块的文件描述
            packInfo = infos['configFile']
            if not os.path.exists(packInfo):
                request.put('无法找到模块：‘%s’ 的配置信息：‘%s’' % (name, packInfo), msgType='nerror')
                return
            # 读取描述信息
            packObj = None
            with open(packInfo, 'r') as fp:
                packObj = json.load(fp)
            if not packObj:
                request.put('无法读取模块：‘%s’ 的配置信息：‘%s’' % (name, packInfo), msgType='nerror')
                return
            # 设置一些基本的信息
            request.packInfo = packInfo
            request.packObj = packObj
        except Exception as e:
            request.put('处理卸载失败', msgType='error')
        else:
            if super().getSuccessor():
                super().getSuccessor().handle(request)
        # def _ProcessUninstall(packageroot, packname):


class UninstallDeleteFilesAndDirs(BaseHandler):

    def __init__(self):
        super(UninstallDeleteFilesAndDirs, self).__init__()

    @staticmethod
    def _delFilesAndDirs(dirs, files):
        """
        处理卸载，删除相关的文件和文件夹
        :param dirs: 目标删除的文件夹
        :param files: 删除的文件
        :return:
        """
        output = []
        for file in files:
            if os.path.exists(file):
                os.remove(file)
                output.append('删除普通文件：‘%s’' % file)  # 注意，已经更换为了相对于运行目录的路径
        for dirn in dirs:
            if os.path.exists(dirn):
                shutil.rmtree(dirn)
                output.append('删除普通目录：‘%s’' % dirn)  # 注意，已经更换为了相对于运行目录的路径
        return output

    @staticmethod
    def _delFromConfig(infoFile, packname):
        cfg = BaseHandler.configMgr
        cfg.removeInstalledPackageInfo(packname)
        cfg.save()
        # 删除程序的配置文件
        os.remove(infoFile)
        return ['成功从配置文件中删除模块：‘%s’的信息' % packname, '成功删除模块 ‘%s’ 的安装信息文件 ‘%s’' % (packname, infoFile)]

    def handle(self, request):
        """
        删除模块的所有的文件
        :param request: 需要 packageName, logs, packObj, packInfo
        :return:
        """
        try:
            request.put(UninstallDeleteFilesAndDirs._delFromConfig(request.packInfo, request.packageName))
            # 然后删除文件
            request.put(UninstallDeleteFilesAndDirs._delFilesAndDirs(request.packObj['installedDirs'],
                                                                             request.packObj['installedFiles']))
        except Exception as e:
            request.put('处理卸载失败：', msgType='error')
        else:
            request.uninstallStatus = True
            # 成功
            request.put(
                "成功卸载模块：‘{name}’，版本：‘{version}’，作者：‘{author}’，目标平台：‘{platform}’。重新启动服务即可生效。".format(
                    name=request.packObj['name'],
                    version=request.packObj['version'],
                    author=request.packObj['author'],
                    platform=request.packObj['platform']
                ))
            if super().getSuccessor():
                super().getSuccessor().handle(request)


def installPackage(request):
    """
    安装模块
    :param request: 一个构造的请求
    :return:
    """
    p1 = CheckPackageInfoHandler()
    p2 = ExtractPackageHandler()
    p3 = ProcessInstallHandler()
    p4 = CleanExtractDirHandler()
    p1.setSuccessor(p2)
    p2.setSuccessor(p3)

    p1.handle(request)


    if request.installStatus:
        request.put("成功安装模块")
    else:
        request.put("安装模块失败", msgType='nerror')
    p4.handle(request)

def uninstallPackage(request):
    p1 = UninstallGetInfoHandler()
    p2 = UninstallDeleteFilesAndDirs()
    p1.setSuccessor(p2)

    p1.handle(request)
    if request.uninstallStatus:
        request.put("成功卸载模块")
    else:
        request.put("卸载模块失败")



