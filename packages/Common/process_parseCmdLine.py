# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ["parseCmdLine"]
__doc__ = '提供基本的Appointed2工具函数'
__cmdLines__ = {  # 用于指定工具的命令行的参数(面向用户)

}
import getopt
import shlex


def _ParseCmd(cmdline):
    """将命令行格式的cmdline信息解析为参数数组格式
    如果没有解析成功，返回None
    """
    cmdlines = shlex.split(cmdline)#_parser.Parse(cmdline)
    if cmdlines and isinstance(cmdlines, list):
        return cmdlines
    return None


def _GetCmdMap(cmdInfo):
    """返回get名称->(相应的短名,相应的长名)
    如果解析失败，将会抛出异常
    """
    try:
        ret = dict()
        shorts = cmdInfo['short']  # 分解命令。
        realshort = list()
        for shortname in shorts:  # 设置短名称
            if shortname == ':':
                continue
            elif shortname.isalpha():
                realshort.append(shortname)
        # 解析长名称。默认get的参数就是长名称
        longs = cmdInfo['long']
        if len(longs) == len(realshort):
            for i in range(0, len(longs)):
                trueLong = longs[i].replace('=', '')  # 去掉命令格式的内容
                ret[trueLong] = ('--' + trueLong, '-' + realshort[i])
            return ret  # 返回结果
    except Exception as e:
        raise e


def _ConvertCmdLineToGet(cmdline, cmdInfo):
    """将命令行转换为Get指令
    可能会抛出异常。如果解析的命令不存在于定义的内容，跳转过程前不会发生错误。但不保证实际的处理过程中，是否会发生错误
    """
    cmds = _ParseCmd(cmdline)
    if cmds and len(cmds) > 1:
        try:
            getStr = list()
            # 需要检查是否不带有参数
            if not cmdInfo.get('short'):
                return ''
            options, noOptArgs = getopt.getopt(cmds[1:], cmdInfo['short'], cmdInfo['long'])  # 定义参数解析的对象
            required_key = cmdInfo['default']  # 必须的参数对应的get的键名称
            getToTuple = _GetCmdMap(cmdInfo)
            # 处理元组信息
            for name, value in options:
                matched = False
                for getname, names in getToTuple.items():
                    if name in names:
                        matched = True
                        if value == '':
                            getStr.append('%s=True' % getname)
                        else:
                            getStr.append('%s=%s' % (getname, value))
                # 检查matched的值。有可能是以外的参数 。目前不管吧
            # 处理需求的信息
            if required_key:
                joinstr = required_key + '%s'
                getStr.append('&'.join([(joinstr % i) for i in noOptArgs]))
            # 生成get信息
            return '&'.join(getStr)
        except Exception as e:
            raise e
    else:
        return ''


def _GetInfo(cmdline, packageName, cmdname, packagesMgr):
    """
    命令行解析
    :param cmdline:  命令行
    :param packageName:子模块的名称
    :param cmdname: 命令的名称
    :param packagesMgr: 模块管理器实例
    :return:
    """
    try:
        mod = packagesMgr.findByName(packageName)
        if not mod and getattr(mod, 'commandLines'):
            raise RuntimeError("模块：‘%s’ 不存在或者没有命令行" % packageName)
        # 已经载入了正确的命令信息
        cmdObj = mod.commandLines.get(cmdname, None)
        if not cmdObj:
            raise RuntimeError("模块：‘%s’ 不存在没有命令行：‘%s’" % (packageName, cmdname))
        return _ConvertCmdLineToGet(cmdline, cmdObj)
    except Exception as e:
        raise e



def parseCmdLine(packageName, cmdname, cmdline, rettype, packageMgr):
    """
    解析命令行格式的调用
    :param packageName: 模块名
    :param cmdname: 命令名称
    :param cmdline: 命令行
    :param rettype: 返回类型 Normal 或者 api
    :param packageMgr: 模块管理对象
    :return:
    """
    try:
        if cmdname:
            cmdname = cmdname.strip('" \'')
        if cmdline:
            cmdline = cmdline.strip('\'"')
        if cmdline and cmdname:
            getinfo = _GetInfo(cmdline, packageName, cmdname, packageMgr)
            if rettype == 'api':
                return "redirect:/api/%s%s%s" % (cmdname, '?' if len(getinfo) > 0 else '', getinfo)
            else:
                return "redirect:/%s%s%s" % (cmdname, '?' if len(getinfo) > 0 else '', getinfo)
        else:
            raise RuntimeError('没有指定命令名称或者需要解析的命令行')
    except Exception as e:
        raise e


