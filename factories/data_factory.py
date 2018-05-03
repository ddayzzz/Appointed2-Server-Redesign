from packages import logger
__logger = logger.get_logger()
async def data_factory(app, handler):
    """
    对请求来源进行分类
    :param app: 网页服务器实例
    :param handler: 路由处理器
    :return: 返回一个封装的可调用对象
    """
    async def parse_data(request):

        if request.method == 'POST':
            # 检查HTTP头的Content-Type
            if request.content_type.startswith('application/json'):
                request.__data__ = await request.json()  # 格式化为JSON
                __logger.info('接受JSON格式数据: %s' % str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__ = await request.post()  # 这个是表格的
                __logger.info('接受的表格: %s' % str(request.__data__))

        return (await handler(request))
    return parse_data