# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['sep', 'macro', 'Macro', 'SetMacro']
__doc__ = 'Appointed2定义的宏'
import os
from os import sep


macro = {
    'PYTHON_BIN':None,
    'PYTHON_VERSION':None,
    'PYTHON_PREFIX':None,
    'PLATFORM':None,
    'ARC': None,
    'HOST': None,
    'ADDRESS': None,
    'PORT':None,
    'MONITOR_PID':None,
    'PACKAGEROOT':'packages',
    'PACKAGEROOT_IMPORT':'packages',
    'KEYDIRS': 'cached;configs;packages;statics;templates;factories;libs;logs',
    'CWD':'.',
    'CACHEDROOT':'cached',
    'CONFIGROOT':'configs',
    'LOGROOT':'logs',
    'VERSION':'0.0.0.1'
}


def Macro(org, throws=False):
    """
    获取宏的实际值
    :param org: 变量名
    :return: 返回实际值，如果不存在于宏列表返回第一个参数
    """
    if isinstance(org, str):
        # 字符型
        o_c = macro.get(org, None)
        o_c = o_c if o_c else org
        if not o_c and throws:
            raise KeyError('没有找到宏名称：%s' % org)
        return o_c
    else:
        return org


def SetMacro(key, value):
    """
    设置宏：一般用于初始化服务器的时候
    :param key: 键
    :param value: 值
    :return:
    """
    macro[key] = value