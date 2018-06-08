from aiohttp import web
import json
from packages import logger, exceptionHandle, TemplateManager
import traceback
__logger = logger.get_logger("Server")
# 响应的抽象工厂
async def response_factory(app, handler):
    """
    用于处理处理器返回的数据，同时对结果、或者错误进行最终的处理
    :param app: 网页服务器实例
    :param handler: 路由处理器
    :return: 返回一个封装的可调用对象
    """
    async def response(request):
        try:
            __logger.info('等待响应...')

            r = await handler(request)  # 等待logger的处理完成
            if isinstance(r, web.Response):
                return r  # 直接返回响应
            if isinstance(r, TemplateManager.RenderingTemplateInfo):
                r.set_user(request.__user__)
                resp = web.Response(
                    body=r.render(app))  # 从emplate的目录读取文件
                resp.content_type = 'text/html;charset=utf-8'
                return resp
            if isinstance(r, web.StreamResponse):
                # 字节流。客户端默认下载的是字节流(header是application/octet-stream)。需要修改请求的类型
                accept_type = request.headers.get('accept')
                if accept_type:
                    last_com = accept_type.find(',')
                    if last_com > 0:
                        r.content_type = accept_type[:last_com]
                # for d in dir(request):
                #     print("%s:%s" % (str(d), str(getattr(request, d))))
                return r
            if isinstance(r, bytes):
                resp = web.Response(body=r)
                resp.content_type = 'application/octet-stream'
                return resp
            if isinstance(r, str):
                if r.startswith('redirect:'):
                    return web.HTTPFound(r[9:])
                resp = web.Response(body=r.encode('utf-8'))
                resp.content_type = 'text/html;charset=utf-8'
                return resp
            if isinstance(r, dict):
                template = r.get('__template__')
                if template is None:
                    dictData = {'status': '200', 'data': r}
                    resp = web.Response(
                        body=json.dumps(dictData, ensure_ascii=False, default=lambda o: o.__dict__()).encode('utf-8'))
                    resp.content_type = 'application/json;charset=utf-8'
                    return resp
                else:
                    r['__user__'] = request.__user__
                    resp = web.Response(body=app.template.get_template(template).render(**r).encode('utf-8'))  # 从emplate的目录读取文件
                    resp.content_type = 'text/html;charset=utf-8'
                    return resp
            if isinstance(r, int) and r >= 100 and r < 600:  # 这个是保留的响应代码。有的可能需要
                return exceptionHandle.generateErrorResponse(app.template, 'json', r, None)  # 返回一个状态，我也不知道些什么
            if isinstance(r, tuple) and len(r) == 2:
                t, m = r
                if isinstance(t, int) and t >= 100 and t < 600:
                    return exceptionHandle.generateErrorResponse(app.template, 'json', r, None, messages=m)  # 返回一个状态，指定了消息
            # default:
            resp = web.Response(body=str(r).encode('utf-8'))
            resp.content_type = 'text/plain;charset=utf-8'
            return resp
            # 由于 websocket 可能返回特殊的响应，如果这种情况，系统会自动处理
        except web.HTTPNotFound as ne:
            msg = '%s 没有定义' % request.path
            __logger.error(msg)
            return exceptionHandle.generateErrorResponse(app.template,
                                                         'api' if request.path.startswith('/api') else 'normal', 404,
                                                         None, messages=(msg,),
                                                         traceback=traceback.format_exc())
        except web.HTTPBadRequest as ne:
            msg = '错误的请求：%s' % request.path
            __logger.error(msg)
            return exceptionHandle.generateErrorResponse(app.template,
                                                         'api' if request.path.startswith('/api') else 'normal', ne.status,
                                                         None, messages=(msg,),
                                                         traceback=traceback.format_exc())
        except Exception as e:
            __logger.error('处理请求出现了错误：%s' % str(e.args), exc_info=True, stack_info=True)
            usermsg = ['处理请求出现了错误：']
            usermsg.extend(e.args)
            return exceptionHandle.generateErrorResponse(app.template,
                                                         'api' if request.path.startswith('/api') else 'normal', e,
                                                         None, messages=usermsg,
                                                         traceback=traceback.format_exc())
    return response  # 处理完成 现在都是Response的对象 接下来就有路由关联的函数处理，也就是ResponseHandler