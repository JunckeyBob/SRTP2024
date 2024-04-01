from affectivecloud.protocols.responses.base import Response


# 会话请求响应
class SessionResponse(object):

    # 创建会话请求响应
    class Create(Response):

        def __init__(self, **kwargs) -> None:
            super(SessionResponse.Create, self).__init__(**kwargs)
            if self.data:
                self.session_id = self.data.get('session_id')

    # 恢复会话请求响应
    class Restore(Response):

        def __init__(self, **kwargs) -> None:
            super(SessionResponse.Restore, self).__init__(**kwargs)
            if self.data:
                self.session_id = self.data.get('session_id')

    # 关闭会话响应
    class Close(Response):
        pass
