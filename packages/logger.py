__doc__ = '日志处理系统'
import logging


_console_logger = None

def init_logger(filename, outputToscreen=True):
    """
    初始化一个日志记录器
    :param filename: 日志保存的文件名
    :param outputToscreen: 是否显示到控制台
    :return: 返回一个记录器
    """
    # 默认的日志记录器
    logging.basicConfig(level=logging.INFO, filename=filename, filemode='w', datefmt='%a, %d %b %Y %H:%M:%S',
                        format='%(name)s: %(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
    # 是否同时显示在控制台界面
    if outputToscreen:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)
    return logging.getLogger('')


def get_logger(name=''):
    """
    获取一个记录器
    :param name: 名称。这个名称会显示在日志记录中。如果不存在将会创建一个新的日志记录器
    :return: 返回name对应的记录器
    """
    return logging.getLogger(name)

