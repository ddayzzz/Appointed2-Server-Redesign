# coding=utf-8
__doc__ = '服务器配置管理器，可以获取相关的服务器设置'
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['getConfigManager']
import json
import os
_configMgr = None

class ConfigManager():


    def __init__(self):
        # 构造其他的设置
        self.cfgs = dict()
        self.changed = False
        self.__global_config_file = os.sep.join(('.', 'configs', 'server.json'))
        # 读取配置信息
        with open(self.__global_config_file, 'r') as fp:
            self.cfgs = json.load(fp)


    def __getitem__(self, item):
        try:
            return self.cfgs[item]
        except KeyError as e:
            raise e

    def __setitem__(self, key, value):
        try:
            self.cfgs[key] = value
            self.changed = True
        except KeyError as e:
            raise e

    def get(self, key, defaultvalue=None):
        return self.cfgs.get(key, defaultvalue)

    def getInstalledPackages(self):
        """
        获取已经安装的包内容
        :return: 返回一个 dict表示 packagename->信息关联
        """
        _installed = self.cfgs.get('installed', None)
        if not _installed:
            return dict()  # 不存在信息
        return _installed

    def addInstalledPackageInfo(self, name, data):
        """
        将安装的模块的信息写入到配置文件，但是不会保存
        :param name: 模块名称
        :param data: 数据信息
        :return:
        """
        _installed = self.cfgs.get('installed', None)
        if not _installed:
            self.cfgs['installed'] = dict()
        self.cfgs['installed'][name] = data
        self.changed = True

    def removeInstalledPackageInfo(self, name):
        infos = self.getInstalledPackages()
        info = infos.get(name, None)
        if info:
            del self.cfgs['installed'][name]
        self.changed = True

    def save(self):
        if not self.changed:
            return
        with open(self.__global_config_file, 'w') as fp:
            json.dump(self.cfgs, fp, indent=4)



def getConfigManager():
    """
    返回唯一的设置实例
    :return:
    """
    global  _configMgr
    if _configMgr == None:
        _configMgr = ConfigManager()
    return _configMgr




