# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['create', 'authenticate', 'signout', 'cookie2user', 'user2cookie'
]
__doc__ = '提供基本Appointed2用户管理'

from packages.Common import Models
import re
import hashlib
from aiohttp import web
import json
import time
from packages import logger, dbManager

COOKIE_NAME = 'appointed2_manager_session'
_COOKIE_KEY = 'welcome'


_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')


_logger = logger.get_logger()


async def create(dbpool, name, password_hash, email, admin_ensureid):
    try:
        if not name or not name.strip():
            raise ValueError('无法创建用户：名称无效')
        if not email or not _RE_EMAIL.match(email):
            raise ValueError('无法创建用户：Email无效')
        if not password_hash or not _RE_SHA1.match(password_hash):
            raise ValueError('无法创建用户：密码格式无效')
        users = await Models.User.findAll(dbpool, 'email=?', [email])
        if len(users) > 0:
            raise ValueError('注册失败', 'Email', '“' + email +'”已经被使用')
        uid = Models.next_id()
        # 检查是否是允许注册为管理员
        isadmin = False
        if admin_ensureid != '':
            if admin_ensureid != 'naive':
                raise ValueError('无法创建管理员权限用户：确认身份失败')
            else:
                isadmin = True
        sha1_passwd = '%s:%s' % (uid, password_hash)
        user = Models.User(id=uid, username=name.strip(), email=email,
                           passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),
                           image='http://www.gravatar.com/avatar/%s?d=mm&s=120' % hashlib.md5(
                        email.encode('utf-8')).hexdigest(),
                           admin=isadmin)
        await user.save(dbpool)
        # make session cookie:
        r = web.Response()
        r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
        user.passwd = '*******'
        r.content_type = 'application/json'
        r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
        return r
        # isadmin = tools.ObjToBool(isadmin)
        # usr = userModel.User(email=email, passwd=password_hash, admin=isadmin, name=name, image=image)
        # await dbManager.insert(usr)
        # return usr
    except Exception as e:
        raise e


async def _findAll(dbpool):
    try:
        return (await dbManager.findAll(Models.User, dbpool))
    except Exception as e:
        raise e


async def authenticate(dbpool, email, passwd):
    if not email:
        raise ValueError('Email', '非法的邮箱')
    if not passwd:
        raise ValueError('密码', '密码错误')
    users = await Models.User.findAll(dbpool, 'email=?', [email])
    if len(users) == 0:
        raise ValueError('Email', 'Email关联的账户不存在')
    user = users[0]
    # check passwd:
    sha1 = hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))
    sha1.update(b':')
    sha1.update(passwd.encode('utf-8'))
    if user.passwd != sha1.hexdigest():
        raise ValueError('密码', '密码错误')
    # authenticate ok, set cookie:
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 86400), max_age=86400, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r


def signout(request):
    referer = request.headers.get('Referer')
    r = web.HTTPFound(referer or '/manager')  # 设置跳转页面
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logger.get_logger().info("用户退出登陆")
    return r

# 计算加密cookie:
def user2cookie(user, max_age):
    # build cookie string by: id-expires-sha1
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)


# 解密cookie:
async def cookie2user(dbpool, cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    L = cookie_str.split('-')
    if len(L) != 3:
        return None
    uid, expires, sha1 = L
    if int(expires) < time.time():
        return None
    user = await Models.User.find(dbpool, uid)
    if user is None:
        return None
    s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
    if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
        _logger.info('无效的SHA1信息')
        return None
    user.passwd = '******'
    return user