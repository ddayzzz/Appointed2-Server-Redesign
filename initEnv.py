# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['InitEnv']
__doc__ = 'Appointed2服务器初始化的环境配置工作 - 将服务器调整到最优的状态并检查程序的环境'
"""在这里出现的错误将会显示在控制台/Shell中。程序不会启动
"""
import sys
import platform
from os import sep
from packages import macros
import os
import sysconfig


def _versionCheck(throws=True):
    """
    Python 实现版本检查
    :return: 出错或者是返回布尔值
    """
    res = False
    try:
        impl_info = sys.implementation
        if impl_info.name != 'cpython':
            # 实现版本不是CPython 还是出错吧
            raise RuntimeError("Python 环境不是CPython实现的")
        if impl_info.version.major >= 3 and impl_info.version.minor >= 5:
            # 由于我这个服务器使用了async/await语句 所以需要PYTHON 3.5或者更高的版本
            res = True
        else:
            raise RuntimeError("需要使用CPython3.5 或者给更高版本")
    except Exception as e:
        if throws:
            raise e
    return res


def _setMacro():
    """
    初始化程序定义的宏命令
    :return:
    """
    # major
    major = sys.version_info.major
    minor = sys.version_info.minor
    _python_prefix = sys.prefix  # Python的前缀路径
    # 获取操作系统体系结构
    _architecture = platform.machine()
    # python模块的名称
    lib_path = _python_prefix + sep  # 附加的库目录。
    # include 路径
    include_path = _python_prefix + sep + "include"
    # 设置可执行的目录Scripts
    bin_path = _python_prefix + sep
    if os.name == 'nt':
        lib_path = lib_path + 'libs'
        # lib的名称nt有lib后缀(cl编译器可能用到)
        lib_name = ("python%d%d" % (major, minor)) + '.lib'
        # 设置可执行的目录Scripts
        bin_path += 'Scripts'
    else:
        pyv = "python%d.%d" % (major, minor)
        lib_path = lib_path + "lib"
        # lib的名称posix有m
        lib_name = pyv + 'm'
        # posix 下include 还有版本
        include_path = include_path + sep + pyv + 'm'
        bin_path += 'bin'
    # 设置路径成功
    macros.SetMacro('ARC', _architecture)
    macros.SetMacro('PYTHON_INCLUDE', include_path)
    macros.SetMacro('PYTHON_LIBNAME', lib_name)
    macros.SetMacro('PYTHON_LIBPATH', lib_path)
    macros.SetMacro('PYTHON_BIN', bin_path)
    macros.SetMacro('PYTHON_VERSION', "%d.%d" % (major, minor))
    macros.SetMacro('PYTHON_PREFIX', _python_prefix)
    macros.SetMacro('PLATFORM', os.name)

def _setMacro2():
    """
    设置一些宏常量
    :return:
    """
    path_lib = sysconfig.get_path('stdlib')  # 默认的库目录
    path_inc = sysconfig.get_path('include')
    var_arc = 'AMD64' if sys.maxsize > 2**32 else 'i386'
    var_bin = sys.executable
    var_version  = '%d.%d' % (sys.version_info.major, sys.version_info.minor)
    var_prefix = sysconfig.get_config_var('base')  # python 的安装的目标目录
    var_platform = os.name  # 有 java, posix 和 nt。参见 https://docs.python.org/3.6/library/os.html
    macros.SetMacro('ARC', var_arc)  # 可能还有 i686 i586 win32 ?
    macros.SetMacro('PYTHON_BIN', var_bin)
    macros.SetMacro('PYTHON_VERSION', var_version)
    macros.SetMacro('PYTHON_PREFIX', var_prefix)
    macros.SetMacro('PLATFORM', var_platform)


def InitEnv(throws):
    """
    初始化服务器环境
    :param throws:  是否抛出错误
    :return:
    """
    _versionCheck(throws)
    _setMacro2()
    # print(macros.macro)