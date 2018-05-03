from packages import logger
__logger = logger.get_logger()
async def logger_factory(app, handler):
    """
    一个自定义的工厂拦截器，用于显示调用信息
    :param app: 网页服务器实例
    :param handler: 路由处理器
    :return: 返回一个封装的可调用对象
    """
    async def logger_handler(request):
        # logger.get_logger().info('客户端请求: %s %s' % (request.method, request.path))
        __logger.info('客户端请求: %s %s' % (request.method, request.path))
        return await handler(request)  # 转到下一步response_factory
    return logger_handler