from affectivecloud.protocols.responses.base import Response


# 基础服务请求响应
class BaseServiceResponse(object):

    # 初始化基础服务请求响应
    class Init(Response):

        def __init__(self, **kwargs) -> None:
            super(BaseServiceResponse.Init, self).__init__(**kwargs)
            if self.data:
                self.base_services = self.data.get('bio_data_type')

    # 订阅基础数据请求响应
    class Subscribe(Response):

        # 订阅基础数据请求响应类型
        class ResponseType(object):
            # 订阅状态
            Status = 0
            # 订阅数据
            Data = 1

        def __init__(self, **kwargs) -> None:
            super(BaseServiceResponse.Subscribe, self).__init__(**kwargs)
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
            super(BaseServiceResponse.Unsubscribe, self).__init__(**kwargs)
            self.unsubscribes = {}
            if self.data:
                for key, values in self.data.items():
                    self.unsubscribes['_'.join(key.split('_')[1:-1])] = values

    # 阶段基础数据报表请求响应
    class Report(Response):

        def __init__(self, **kwargs) -> None:
            super(BaseServiceResponse.Report, self).__init__(**kwargs)
            if self.data:
                self.reports = self.data

    # 提交附加数据请求响应
    class SubmitAdditionalInformationToStore(Response):

        def __init__(self, **kwargs) -> None:
            super(BaseServiceResponse.SubmitAdditionalInformationToStore, self).__init__(**kwargs)
            if self.data:
                self.commits = self.data
