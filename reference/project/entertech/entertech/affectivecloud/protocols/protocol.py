import json


# 服务类型
ServiceType: type = str

# 操作类型
OperationType: type = str


# 会话服务
class Services(object):

    # 服务类型
    class Type(object):
        # 会话服务
        SESSION: ServiceType = "session"
        # 基础服务
        BASE_SERVICE: ServiceType = "biodata"
        # 情感计算服务
        AFFECTIVE_SERVICE: ServiceType = "affective"

    # 操作类型
    class Operation:
        # 会话操作类型
        class Session:
            # 创建会话
            CREATE: OperationType = "create"
            # 恢复会话
            RESTORE: OperationType = "restore"
            # 关闭会话
            CLOSE: OperationType = "close"

        # 基础服务操作类型
        class BaseService:
            # 初始化
            INIT: OperationType = "init"
            # 订阅
            SUBSCRIBE: OperationType = "subscribe"
            # 取消订阅
            UNSUBSCRIBE: OperationType = "unsubscribe"
            # 上传数据
            UPLOAD: OperationType = "upload"
            # 获取报告数据
            REPORT: OperationType = "report"
            # 提交附加信息
            SUBMIT: OperationType = "submit"

        # 情感计算服务操作类型
        class AffectiveService:
            # 开始
            START: OperationType = "start"
            # 订阅
            SUBSCRIBE: OperationType = "subscribe"
            # 取消订阅
            UNSUBSCRIBE: OperationType = "unsubscribe"
            # 获取报告数据
            REPORT: OperationType = "report"
            # 结束
            FINISH: OperationType = "finish"

    # 上传周期数据长度基数（upload_cycle = 1）
    class DataUploadCycleLength:
        EEG: int = 1000
        HR: int = 3


# 协议基础类
class ProtocolBase(object):
    def dumps(self):
        return json.dumps(self.dict())

    def dict(self):
        return self.__dict__

    def __str__(self):
        return self.dumps()


# 协议体基础类
class ProtocolDictBody(ProtocolBase):
    def __init__(self, **kwargs):
        super(ProtocolDictBody, self).__init__()
        for k, v in kwargs.items():
            setattr(self, k, v)

    def dumps(self):
        return json.dumps(self.dict())

    def dict(self):
        return self.__dict__

    def __str__(self):
        return self.dumps()
