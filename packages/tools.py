# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['EnvironmentPath', 'ObjToBool', 'InstallRequiredModules', 'compareVersion', 'unloadAllRefModule']
__doc__ = 'Appointed2定义的工具函数方便模块对整个程序的运行状态进行获取'
import os
import sys
import subprocess
import sysconfig
from packages import macros, logger
from distutils.version import LooseVersion # 严格程序的版本
import chardet
import traceback


def EnvironmentPath(path_type='root', packageType=False):
    """返回服务管理器的路径信息(相对路径)
    path_type : 路径的标志
        root : 服务器的目录
        packages 表示模块的总目录
        <moduleName>:模块的完整名称（从运行的路径开始）
    packageType : 是否是包模式（path_type不为root）
    """
    path = path_type.lower()
    if path == 'root':
        return '.'
    elif path == 'packages':
        return '.' + os.path.sep + 'packages' if not packageType else 'packages'
    else:
        return os.sep.join(('.', 'packages', path_type)) if not packageType else 'packages.' + path_type


def ObjToBool(obj, true=('1', 'TRUE')):
    """将任何一个对象的转换为bool。对象最好是拥有__str__方法
    true:可以指定真值。忽略大小写(默认真正大写)
    """
    try:
        if not obj:
            return False
        return True if str(obj).upper() in true else False
    except BaseException as e:
        return False


# def RunMake(packageName, throws=False, **kwargs):
#     """
#     运行适用于Appointed2的Makefile文件
#     :param packageName: 模块的名称
#     :param throws: 是否抛出错误
#     :param kwargs: 传递给makefile的参数
#     :return: 返回出错或者输出的结果
#     """
#     try:
#         macro_make = ' '.join([('%s="%s"' % (k, v)) for k, v in kwargs.items()])
#         res = subprocess.check_output('make %s && make install' % macro_make,
#                                       shell=True,
#                                       cwd=macros.Macro('PACKAGEROOT', throws) + macros.sep + packageName)
#         logger.get_logger().info('Make编译信息:\n' + res.decode('utf-8'))
#     except subprocess.CalledProcessError as e:
#         if throws:
#             raise e
#         res = e.stderr.decode('utf-8') if e.stderr else ''
#         logger.get_logger().info('Make编译出错:\n' + res)
#     except Exception as e:
#         if throws:
#             raise e
#         res = str(e.args)
#         logger.get_logger().info('使用Make编译出错:\n' + res)
#     return res


def InstallRequiredModules(modulesNames, appointed2RequiredNames, throws=False):
    """
    安装Python或者是Appointed需求的模块
    :param modulesNames: Python模块的名称以及版本检查信息 例如 ss==2.0 PIL>=2.0。如果不指定版本将安装最新版
    :param throws: 是否抛出错误
    :param appointed2RequiredNames: Appointed2模块
    :return:
    """
    try:
        if len(modulesNames) > 0:
            # 设置python的安装信息
            res = subprocess.check_output('pip3 install %s' % modulesNames,
                                          shell=False,
                                          cwd=macros.Macro('PYTHON_BIN', throws))
            logger.get_logger().info('pip3安装信息:\n' + res.decode('utf-8'))
        # Appointed2安装
    except subprocess.CalledProcessError as e:
        if throws:
            raise e
        res = e.stderr.decode('utf-8') if e.stderr else ''
        logger.get_logger().info('安装需求模块出错:\n' + res)
    except Exception as e:
        if throws:
            raise e
        res = str(e.args)
        logger.get_logger().info('安装需求模块出错:\n' + res)
    return res


def IsAdminRequest(request):
    """
    判断这个请求是否具有管理员权限
    :param request:
    :return:
    """
    try:
        if request and not request.__user__ .admin == True:
            return True
    except Exception as e:
        pass
    return False


def compareVersion(v1,v2,opt):
    """
    严格比较版本号信息
    :param v1: 版本号1
    :param v2: 版本号2
    :param opt: 操作。定义了6中关系运算符
    :return: 返回布尔值
    """
    s1 = LooseVersion(v1)
    s2 = LooseVersion(v2)
    if opt == '==':
        return s1 == s2
    elif opt == '!=':
        return s1 != s2
    elif opt == '>':
        return s1 > s2
    elif opt == '>=':
        return s1 >= s2
    elif opt == '<':
        return s1 < s2
    elif opt == '<=':
        return s1 <= s2

def unloadAllRefModule(modules):
    """
    将指定的模块从系统（Python）中删除
    :param modules: 模块名(可以多个)
    :return:
    """
    for module in modules:
        del sys.modules[module]

def compileDynamicExtension(compilerType, cwd, srcs, out):
    """
    编译srcs源文件为动态链接库
    :param compilerType : 编译器类型 ： c，cpp分别表示 c，cpp 编译器
    :param cwd: 指定工作目录
    :param srcs: 源文件的可迭代的对象
    :param out: 输出的文件的文件名，不包含扩展名
    :return: 返回运行的结果 status, outfile（生成的完整文件名）, stdout输出，stderr输出(如果非0才会有)
    """
    try:
        cflags = ['-shared', '-fPIC']
        target = '%s%s' % (out, sysconfig.get_config_var('SHLIB_SUFFIX'))
        # 设置源文件
        cflags.extend(srcs)
        cflags.append('-o ' + target)
        if compilerType.upper() == 'C':
            compiler = sysconfig.get_config_var('CC')
            # cflags.append(sysconfig.get_config_var('BASECFLAGS'))  # 基本编译的指令
        else:
            compiler = sysconfig.get_config_var('CXX')
            # cflags.append(sysconfig.get_config_var('BASECPPFLAGS'))
        # 设置编译指令
        cflags.append('-I"%s"' % sysconfig.get_path('include'))  # include
        cflags.append(
            '-L"%s" %s' % (sysconfig.get_config_var('LIBDIR'), sysconfig.get_config_var('BLDLIBRARY')))  # library
        # 运行指令
        exec = [compiler]
        exec.extend(cflags)  # 生成最终的编译指令
        p = subprocess.Popen(args=' '.join(exec), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        out, err = p.communicate()
        out_dect = chardet.detect(out)
        err_dect = chardet.detect(err)
        # print(out_dect)
        # print(err_dect)
        retout = out.decode(out_dect['encoding']) if len(out) > 0 else ''
        reterr = err.decode(err_dect['encoding']) if len(err) > 0 else ''
        return p.returncode, target, retout, reterr
    except Exception as e:
        return -1, '', '', '编译失败出现异常：\n%s\n' % traceback.format_exc()

def installDependentModules(modules, cwd):
    """
    安装python 关联的安装包
    :param modules: 模块名称，可以带有判断检查 如 aiohttp==2.3
    :param cwd: 运行的目录，可以安装目录下的 whl 文件
    :return: 返回 状态代码，输出信息，错误信息
    """
    try:
        import setuptools
    except ImportError as e:
        # 表明不支持安装
        return -1, '', '不支持安装 Python 模块'  # 未安装的列表
    # 检测pip位置
    prefix = macros.Macro('PYTHON_PREFIX')
    ostype = macros.Macro('PLATFORM')
    if ostype == 'nt':
        pippath = macros.sep.join((prefix, 'Scripts', 'pip.exe'))
    else:
        pippath = macros.sep.join((prefix, 'bin', 'pip' + macros.Macro('PYTHON_VERSION')))
    if not os.path.exists(pippath):
        return -1, '不支持安装 Python 模块：无法找到 pip 程序：‘%s’' % pippath
    # 运行 pip 程序
    args = [pippath, 'install']
    args.extend(modules)
    # 运行程序
    try:
        p = subprocess.Popen(args=' '.join(args), stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        out, err = p.communicate()
        out_dect = chardet.detect(out)
        err_dect = chardet.detect(err)
        retout = out.decode(out_dect['encoding']) if len(out) > 0 else ''
        reterr = err.decode(err_dect['encoding']) if len(err) > 0 else ''
        return p.returncode, retout, reterr
    except Exception as e:
        return -1, '', '运行模块安装程序出现异常：\n%s\n' % traceback.format_exc()





