# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = []
__doc__ = '这个是基本的服务其，控制模块的载入以及划分'


class BaseServer:

    def __init__(self, name):
        self.name = name

    def close(self):
        raise NotImplementedError('没有实现服务器关闭流程')

    def run(self):
        raise NotImplementedError('没有实现运行的流程')

    def user_close(self):
        pass

    def user_restart(self):
        pass