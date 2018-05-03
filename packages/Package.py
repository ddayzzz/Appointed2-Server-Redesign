__doc__ = '这个定义的个中的模块包的类型'
from packages import macros
import os
import inspect
from packages import Router
import config
import traceback
import asyncio
from packages import logger, tools


class Package(object):
    """
    这个表示Appointed2 定义的子模块对象
    """
    def __init__(self, packageName, modObj=None, **kwargs):
        """
        模块的信息 __是受保护的内容
        valid:是否有效
        doc:注释信息
        version:模块的信息
        author:作者
        rotuers:可调用对象->{方法，路由，解释，级别，系统}
        commandLines:支持的命令行参数版本
        moduleObject:模块的实例
        main_package:是否是主模块
        :param packageName: 模块的名称
        :return:
        """
        try:
            package_root_modtype = macros.Macro('PACKAGEROOT_IMPORT')
            self.routers = dict()
            self.commandLines = dict()
            self.name = packageName
            self.main_package = False
            if self.name == 'Common' or self.name == 'main':
                self.main_package = True
            if not modObj:
                # 载入packages下的模块
                targetdir = macros.Macro('PACKAGEROOT') + os.sep + packageName
                if not os.path.exists(targetdir) or not os.path.isdir(targetdir):
                    self.valid = False
                    return
                modObj = getattr(__import__(package_root_modtype, globals(), locals(), [packageName]),
                                 packageName)  # 导入模块
            if not modObj:
                self.valid = False
                return
            self.valid = True
            self.fullName = '.'.join((package_root_modtype, packageName))
            # 读取doc、version、author以及各个路由器的信息（只在公共接口中__all__）以及路由的命令行格式（如果有）
            if getattr(modObj, '__all__', None):
                # 合法的模块
                for api in getattr(modObj, '__all__', None):
                    fn = getattr(modObj, api)
                    if callable(fn):
                        # 是一个可调用对象
                        method = getattr(fn, '__method__', None)
                        path = getattr(fn, '__route__', None)
                        if method and path:
                            # 添加路由
                            # self.routers[fn] = {'method': method, 'route': path, 'doc':inspect.getdoc(fn),
                            #                     'level':'api' if path.startswith('/api') else 'user',
                            #                     'system':self.main_package
                            #                     }  # 可调用对象->{方法，路由，解释，级别，系统}
                            # 读取命令行参数
                            router_key = method + ' ' + path
                            if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn): # 检查是否是异步函数
                                fn = asyncio.coroutine(fn)
                            self.routers[router_key] = Router.Router(method=method, route=path, doc=inspect.getdoc(fn),
                                                              level='api' if path.startswith('/api') else 'user',
                                                              system=self.main_package, func=fn)  # 定义成Router 类
            if getattr(modObj, '__cmdLines__', None):
                self.commandLines = modObj.__cmdLines__  # 直接绑定为命令行
            self.version = getattr(modObj, '__version__', '')
            self.author = getattr(modObj, '__author__', '')
            self.doc = getattr(modObj, '__doc__', '')
            self.moduleObject = modObj
            # 构建对象
            logger.get_logger().info('模块对象‘%s’载入成功' % self.name)
        except Exception as e:
            # 处理错误
            logger.get_logger().error('初始化模块对象出现问题：%s\n堆栈信息：%s\n' % (str(e.args), traceback.format_exc()))
            self.valid = False
            raise e

    def disableAllFunctuons(self):
        """
        删除这个模块中所有关联的路由功能（不可用）
        :return:
        """
        for router_key, router_obj in self.routers.items():
            fn = router_obj.func
            logger.get_logger().warning('正在卸载路由：‘%s’ 关联的方法。' % router_obj)
            router_obj.func = None
            del fn
        # import objgraph
        # objgraph.show_refs([self.moduleObject.CStarDictIndex], filename='cached\\module.png')
        del self.moduleObject
        self.moduleObject = None
        # 删除已经载入的模块
        # modules = [module for module in sys.modules.keys() if module.startswith(self.fullName)]
        # i = 0
        # for module in modules:
        #     print(module, sys.getrefcount(sys.modules[module]))
        #     #
        #     # import objgraph
        #     # objgraph.show_refs([sys.modules[module]], filename='cached\\ref_%d.png' % i)
        #     i = i + 1
        #for module in modules:
        # modules = ['packages.WordBook.dictionaries.langdao','packages.WordBook.dictionaries.oxford','packages.WordBook.dictionaries.youdao','packages.WordBook.OnlineDictionary','packages.WordBook.cpystardict','packages.WordBook.DictionaryModel','packages.WordBook.OfflineDictionaryModel','packages.WordBook.CStarDictIndex']
        #    print(module, sys.getrefcount(sys.modules[module]))  # 引用不能大于3 http://outofmemory.cn/code-snippet/1871/python-xiezai-module
        # tools.unloadAllRefModule(modules)
        # print(sys.modules)


class PackagesManager(object):

    def __init__(self):
        # self.allRouters = dict()
        self.loadedPackages = dict()
        # 从设置中读取已经安装的包
        packMgr = config.getConfigManager()
        installednames = packMgr.get('installed', None)
        if installednames:
            for name, infos in installednames.items():
                # 是否启用
                isenable = infos.get('enable', False)
                issys = infos.get('system', False)
                if isenable and not issys:
                    self.loadedPackages[name] = None  # 还没有加载的情况


    def loadPackages(self):
        """
        加载模块
        :return: 不返回
        """
        try:
            for name in self.loadedPackages.keys():
                if not self.loadedPackages[name]:
                    # 这个模块的名称并没有被加载
                    pack = Package(name)  # 加载模块的信息
                    if not pack.valid:
                        continue
                    # self.allRouters.update(pack.routers)  # 扩展字典
                    self.loadedPackages[name] = pack
        except Exception as e:
            raise e

    def addPackage(self, packageObj):
        _logger = logger.get_logger()
        if isinstance(packageObj, Package):
            name = packageObj.name
            if not self.loadedPackages.get(name, None):
                self.loadedPackages[name] = packageObj
                _logger.info('手动添加模块：‘%s’ 成功' % name)
            else:
                _logger.info('无法手动添加模块：‘%s’，已经存在相同名称的模块。' % name)
        else:
            _logger.info('无法手动添加模块：非法的类型。')


    def disablePackage(self, packname):

        packObj = self.loadedPackages.get(packname, None)
        if not packObj:
            raise ValueError('无法找到名为：‘%s’ 的模块' % packname)
        if packObj.main_package:
            raise ValueError('模块‘%s’为系统模块，不允许进行关闭操作！' % packname)
        # 关闭所有的路由
        _logger = logger.get_logger()
        for router_name, router_obj in packObj.routers.items():
            _logger.warning('正在关闭模块‘%s’ 的路由：%s' %(packname, router_obj))
            router_obj.enable = False
        # 仅仅关闭模块的功能
        packObj.disableAllFunctuons()

    def findByName(self, packname):
        """
        查找一个模块对象，按照名称查询。如果不存在返回None
        :param packname:
        :return:
        """
        return self.loadedPackages.get(packname, None)