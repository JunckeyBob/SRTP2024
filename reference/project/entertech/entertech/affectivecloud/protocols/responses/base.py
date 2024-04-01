import logging

logger = logging.getLogger(__name__)


# 请求协议头
class RequestHead(object):

    # 请求会话协议类型
    services: str = None

    # 请求协议操作类型
    op: str = None

    def __init__(self, **kwargs):
        super(RequestHead, self).__init__()
        for k, v in kwargs.items():
            if k not in ('services', 'op'):
                raise Exception('Protocol Error: invalid parameters({}).'.format(k))
            setattr(self, k, v)

    def __str__(self):
        return '[{}:{}]'.format(self.services, self.op)


# 响应基础类型
class Response(object):

    # 响应码
    code: int = None

    # 请求协议头
    request: RequestHead = None

    # 响应数据
    data = None

    # 响应消息
    msg: str = None

    def __init__(self, **kwargs):
        super(Response, self).__init__()
        for k, v in kwargs.items():
            if k == 'request':
                setattr(self, k, RequestHead(**v))
                continue
            if k not in ('code', 'request', 'data', 'msg'):
                raise Exception('Protocol Error: invalid parameters({}).'.format(k))
            setattr(self, k, v)
        if self.code != 200:
            logger.warning(self)

    def __str__(self):
        return '[code: {}] [msg: {}] {} >>> {}'.format(self.code, self.msg, self.request, self.data)
