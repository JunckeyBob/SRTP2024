import json
from typing import List

from affectivecloud.protocols import Services


# 情感计算请求
class AffectiveServiceRequest(object):

    class _request(object):

        # 会话服务类型：情感计算
        services = Services.Type.AFFECTIVE_SERVICE

    # 开始情感计算
    class Start(_request):

        def __init__(self, services: List[str]) -> None:
            """初始化感计算服务启动协议

            Args:
                services (List[str]): 情感计算服务类型列表
            """
            self.ac_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.AffectiveService.START,
                "kwargs": {
                    "cloud_services": self.ac_services,
                },
            })

    # 订阅情感计算服务数据
    class Subscribe(_request):

        def __init__(self, services: List[str]) -> None:
            """初始化感计算服务订阅协议

            Args:
                services (List[str]): 情感计算服务类型列表
            """
            self.ac_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.AffectiveService.SUBSCRIBE,
                "args": self.ac_services,
            })

    # 取消订阅情感计算服务数据
    class Unsubscribe(_request):

        def __init__(self, services: List[str]) -> None:
            """初始化感计算服务取消订阅协议

            Args:
                services (List[str]): 情感计算服务类型列表
            """
            self.ac_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.AffectiveService.UNSUBSCRIBE,
                "args": self.ac_services,
            })

    # 获取阶段情感计算报表
    class Report(_request):

        def __init__(self, services: List[str], ignore_report_body: bool = False) -> None:
            """初始化感计算服务报表协议

            Args:
                services (List[str]): 情感计算服务类型列表
                ignore_report_body (bool): 是否忽略报表体
            """
            self.ac_services = services
            self.ignore_report_body = ignore_report_body

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.AffectiveService.REPORT,
                "kwargs": {
                    "cloud_services": self.ac_services,
                    "ignore_report_body": self.ignore_report_body,
                },
            })

    # 停止情感计算
    class Finish(_request):

        def __init__(self, services: List[str]) -> None:
            """初始化感计算服务结束协议

            Args:
                services (List[str]): 情感计算服务类型列表
            """
            self.ac_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.AffectiveService.FINISH,
                "kwargs": {
                    "cloud_services": self.ac_services,
                },
            })
