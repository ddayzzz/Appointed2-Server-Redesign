from packages import logger
from packages.Common.process_usermgr import COOKIE_NAME, cookie2user


__logger = logger.get_logger("Server")

async def auth_factory(app, handler):
    async def auth(request):
        # __logger.info('检查用户的请求: %s %s' % (request.method, request.path))
        request.__user__ = None
        cookie_str = request.cookies.get(COOKIE_NAME)
        user = ''
        if cookie_str:
            if 'deleted' not in cookie_str:
                user = await cookie2user(app.topServer.dbPool, cookie_str)
            if user:
                __logger.info('从cookies中设置当前的用户: %s' % user.email)
                request.__user__ = user
        return (await handler(request))
    return auth