__doc__ = '日志处理系统'
import logging


def init_logger(outer, filename, outputToscreen=True, standardOutput=False):
    """
    初始化一个日志记录器
    :param outer : 日志写入者
    :param filename: 日志保存的目录
    :param outputToscreen: 是否显示到控制台
    :param standardOutput: 如果允许显示到控制台，是否是将控制台的输出显示为普通大的输出（也就是使用标准的输出）
    :return: 返回一个记录器
    """
    # 默认的日志记录器
    logging.basicConfig(level=logging.INFO, filename=filename, filemode='w', datefmt='%a, %d %b %Y %H:%M:%S',
                        format='{out}: %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'.format(out=outer))
    # 是否同时显示在控制台界面
    if outputToscreen:
        if not standardOutput:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('{out}: %(name)-12s: %(levelname)-8s %(message)s'.format(out=outer))
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)  # 在主记录器添加另一个处理器
        else:
            console = logging.StreamHandler()
            console.setLevel(logging.INFO)
            formatter = logging.Formatter('%(message)s')
            console.setFormatter(formatter)
            logging.getLogger('').addHandler(console)  # 在主记录器添加另一个处理器
    return logging.getLogger('')


def get_logger(name=''):
    """
    获取一个记录器
    :param name: 名称，目前使用的都是主记录器，名称为‘’
    :return: 返回name对应的记录器
    """
    return logging.getLogger(name)


