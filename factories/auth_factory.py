# async def auth_factory(app, handler):
#     async def auth(request):
#         # logger1 = logger.get_logger()
#         print('检查用户的请求: %s %s' % (request.method, request.path))
#         request.__user__ = None
#         cookie_str = request.cookies.get(COOKIE_NAME)
#         if cookie_str:
#             user = await cookie2user(cookie_str)
#             if user:
#                 logger1.info('从cookies中设置当前的用户: %s' % user.email)
#                 request.__user__ = user
#         return (await handler(request))
#     return auth