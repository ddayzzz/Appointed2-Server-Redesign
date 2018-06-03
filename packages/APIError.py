# coding=utf-8
__doc__ = '这个是定义API级别的异常'
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = [
    'ProcessHTTPNotFound', 'ProcessAPIError', 'ProcessAPIErrorWithObject', 'APIError'
]
from packages import logger
from aiohttp import web_exceptions as basicExceptions
import json


__logger = logger.get_logger("Server")

def ProcessHTTPNotFound(app, messages=tuple(), traceback=str(), template=None, format='normal', **kwargs):
    """
    处理404错误的函数
    :param app: 网页服务器的实例
    :param messages: 消息
    :param traceback: 跟踪栈
    :param template: 模板
    :param format: 输出的格式。如果是api调用那么返回的是json。如果是普通网页，返回网页格式
    :param kwargs: 其他可以发送给网页的参数
    :return: 不返回任何结果。但是可能会抛出错误
    """
    try:
        data = {'messages': messages, 'traceback': traceback, 'template': template, 'status': 404}
        # 需要注意，避免键重复，如果有重复就不会替换
        for k, v in kwargs.items():
            data.setdefault(k, v)  # 如果k不存在，就添加键-值：k-v
        if format == 'normal':
            response = basicExceptions.HTTPNotFound(
                body=app.template.get_template('error_handler.html').render(data=data).encode('utf-8'))
            response.content_type = 'text/html;charset=utf-8'
        else:
            response = basicExceptions.HTTPNotFound(body=json.dumps(data, ensure_ascii=False).encode('utf-8'))
            response.content_type = 'application/json;charset=utf-8'
        return response
    except Exception as e:
        __logger.error('处理HTTPNotFound出现错误:%s' % str(e.args))
        raise e


def ProcessAPIError(app, messages=tuple(), traceback=str(), template=None, format='normal', **kwargs):
    """
    处理API错误的函数
    :param app: 网页服务器的实例
    :param messages: 消息
    :param traceback: 跟踪栈
    :param template: 模板
    :param format: 输出的格式。如果是api调用那么返回的是json。如果是普通网页，返回网页格式
    :param kwargs: 其他可以发送给网页的参数
    :return: 不返回任何结果。但是可能会抛出错误
    """
    try:
        data = {'messages': messages, 'traceback': traceback, 'template': template, 'status': 500}
        # 需要注意，避免键重复，如果有重复就不会替换
        for k, v in kwargs.items():
            data.setdefault(k, v)  # 如果k不存在，就添加键-值：k-v
        if format == 'normal':
            response = basicExceptions.HTTPInternalServerError(
                body=app.template.get_template('error_handler.html').render(data=data).encode('utf-8'))
            response.content_type = 'text/html;charset=utf-8'
        else:
            response = basicExceptions.HTTPInternalServerError(
                body=json.dumps(data, ensure_ascii=False).encode('utf-8'))
            response.content_type = 'application/json;charset=utf-8'
        return response
    except Exception as e:
        __logger.error('处理APIError的过程中又出现错误:%s' % str(e.args))
        raise e


def ProcessAPIErrorWithObject(app, expObj, format='normal'):
    """
    处理被抛出的错误对象是API错误格式
    :param app: 网页服务的实例
    :param expObj: 错误的对象，基类是APIError
    :param format: 格式normal响应为网页；api响应为json格式的数据
    :return: 返回响应的对象
    """
    return ProcessAPIError(app=app, format=format, messages=expObj.messages, template=expObj.template,
                            traceback=expObj.traceback, otherInfo=expObj.otherInfo)


class APIError(Exception):
    """
    定义了由用户的错误调用引起的错误对象
    """
    def __init__(self, *args, **kwargs):
        """
        构造函数
        :param args: 一个可迭代的对象，目前是多个消息
        :param kwargs: 自定义的参数，可以设置自定义的页面、键参数指定的消息、跟踪信息，使用的自定义模板
        """
        # 添加默认的消息
        msgs = [x for x in args]
        # 处理kwargs。可以是messages，traceback，template
        # HelpLink等
        if kwargs.get('messages', None):
            msgs.extend(kwargs['messages'])
        self.messages = msgs
        self.traceback = kwargs.get('traceback', str())
        self.template = kwargs.get('template', None)
        # 完整的信息
        self.otherInfo = kwargs

    def __repr__(self):
        return '<APIError>' + str(self.messages)

    def __str__(self):
        return self.__repr__()

    def __dict__(self):
        """
        输出为字典
        :return:
        """
        res = {'messages':self.messages, 'traceback':self.traceback, 'template':self.template, 'otherInfo': self.otherInfo}
        return res
