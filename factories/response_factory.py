from aiohttp import web
import json
from packages import logger, APIError
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
            if isinstance(r, int) and r >= 100 and r < 600:  # 这个是保留的响应代码。这个不处理
                pass  # return web.Response(status=r)
            if isinstance(r, tuple) and len(r) == 2:
                t, m = r
                if isinstance(t, int) and t >= 100 and t < 600:
                    return web.Response(t, str(m))
            # default:
            resp = web.Response(body=str(r).encode('utf-8'))
            resp.content_type = 'text/plain;charset=utf-8'
            return resp
        except APIError.APIError as apiEx:
            logger.get_logger().error('处理请求出现了错误：%s' % apiEx.messages)
            if request.path.startswith('/api'):
                return APIError.ProcessAPIErrorWithObject(app, apiEx, 'api')
            else:
                return APIError.ProcessAPIErrorWithObject(app, apiEx, 'normal')
        except Exception as e:
            logger.get_logger().error('处理请求出现了错误：%s' % str(e.args))
            if request.path.startswith('/api'):
                return APIError.ProcessAPIError(app, messages=e.args, traceback=traceback.format_exc(), format='api')
            else:
                return APIError.ProcessAPIError(app, messages=e.args, traceback=traceback.format_exc(),
                                                  format='normal')
    return response  # 处理完成 现在都是Response的对象 接下来就有路由关联的函数处理，也就是ResponseHandler