from typing import List, Dict, Any
import json

from affectivecloud.algorithm import BaseServiceType
from affectivecloud.protocols import Services


# 基础计算请求
class BaseServiceRequest(object):

    class _request(object):

        # 会话服务类型：基础服务
        services = Services.Type.BASE_SERVICE

    # 初始化基础计算
    class Init(_request):

        def __init__(self, services: List[str], storage_settings: dict = None, algorithm_params: dict = None) -> None:
            """初始化基础计算服务初始化协议

            Args:
                services (List[str]): 基础计算服务类型列表
                storage_settings (dict): 存储设置
                algorithm_params (dict): 算法参数
            """
            self.base_services = services
            self.storage_settings = storage_settings
            self.algorithm_params = algorithm_params

        def __str__(self) -> str:
            body = {
                "services": self.services,
                "op": Services.Operation.BaseService.INIT,
                "kwargs": {
                    "bio_data_type": self.base_services,
                },
            }
            if self.storage_settings:
                body["kwargs"]["storage_settings"] = self.storage_settings
            if self.algorithm_params:
                body["kwargs"]["algorithm_params"] = self.algorithm_params
            return json.dumps(body)

    # 订阅基础数据
    class Subscribe(_request):

        def __init__(self, services: List[str]) -> None:
            """初始化基础计算服务订阅协议

            Args:
                services (List[str]): 基础计算服务类型列表
            """
            self.base_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.BaseService.SUBSCRIBE,
                "args": self.base_services,
            })

    class Unsubscribe(_request):

        def __init__(self, services: List[str]) -> None:
            self.base_services = services

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.BaseService.UNSUBSCRIBE,
                "args": self.base_services,
            })

    # 上传生物信号数据
    class Upload(_request):

        def __init__(self, services_data: Dict[BaseServiceType, List[Any]]) -> None:
            """初始化基础计算服务数据上传协议

            Args:
                services_data (Dict[BaseServiceType, List[Any]]): 基础数据
            """
            self.services_data = services_data

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.BaseService.UPLOAD,
                "kwargs": self.services_data,
            })

    # 获取基础数据阶段报表
    class Report(_request):

        def __init__(self, services: List[str], ignore_report_body: bool = False) -> None:
            """初始化基础计算服务报表协议

            Args:
                services (List[str]): 基础计算服务类型列表
                ignore_report_body (bool): 是否忽略报表数据
            """
            self.base_services = services
            self.ignore_report_body = ignore_report_body

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.BaseService.REPORT,
                "kwargs": {
                    "bio_data_type": self.base_services,
                    "ignore_report_body": self.ignore_report_body,
                },
            })

    # 提交附加数据（存储到原始数据中）
    class SubmitAdditionalInformationToStore(_request):

        def __init__(self, data: Dict[str, Any]) -> None:
            """初始化基础计算服务提交附加数据协议

            Args:
                data (Dict[str, Any]): 附加数据
            """
            self.data = data

        def __str__(self) -> str:
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.BaseService.SUBMIT,
                "kwargs": {
                    "bio_data_type": self.base_services,
                    "data": self.data,
                },
            })
