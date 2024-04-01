from affectivecloud.protocols.responses.base import Response


# 情感计算请求响应
class AffectiveServiceResponse(object):

    # 开始情感计算请求响应
    class Start(Response):

        def __init__(self, **kwargs) -> None:
            super(AffectiveServiceResponse.Start, self).__init__(**kwargs)
            if self.data:
                self.ac_services = self.data.get('cloud_service')

    # 订阅情感计算数据请求响应
    class Subscribe(Response):

        # 订阅情感计算数据请求响应类型
        class ResponseType(object):
            # 订阅状态
            Status = 0
            # 订阅数据
            Data = 1

        def __init__(self, **kwargs) -> None:
            super(AffectiveServiceResponse.Subscribe, self).__init__(**kwargs)
            self.subscribes = {}
            if self.data:
                for key, values in self.data.items():
                    keys = key.split('_')
                    if (keys[0], keys[-1]) == ('sub', 'fields'):
                        self.response_type = self.ResponseType.Status
                        self.subscribes['_'.join(keys[1:-1])] = values
                    else:
                        self.response_type = self.ResponseType.Data

    # 取消订阅请求响应
    class Unsubscribe(Response):

        def __init__(self, **kwargs) -> None:
            super(AffectiveServiceResponse.Unsubscribe, self).__init__(**kwargs)
            self.unsubscribes = {}
            if self.data:
                for key, values in self.data.items():
                    self.unsubscribes['_'.join(key.split('_')[1:-1])] = values

    # 阶段情感计算报表请求响应
    class Report(Response):

        def __init__(self, **kwargs) -> None:
            super(AffectiveServiceResponse.Report, self).__init__(**kwargs)
            if self.data:
                self.reports = self.data

    # 结束情感计算请求响应
    class Finish(Response):

        def __init__(self, **kwargs) -> None:
            super(AffectiveServiceResponse.Finish, self).__init__(**kwargs)
            if self.data:
                self.ac_services = self.data.get('cloud_service')
