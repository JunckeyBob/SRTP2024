from collections import defaultdict
import json
import sys
import asyncio
import gzip
from typing import Any, Awaitable, Dict, Union, List

import websockets

from affectivecloud.algorithm import BaseServices, BaseServiceType, AffectiveServiceType
from affectivecloud.protocols import (
    OperationType, ServiceType, Services,
    SessionRequest, BaseServiceRequest, AffectiveServiceRequest,
    SessionResponse, BaseServiceResponse, AffectiveServiceResponse,
)


if sys.version_info < (3, 7):
    asyncio.get_running_loop = asyncio._get_running_loop


# WebSocket 客户端基础类
class Client(object):

    def __init__(self, url: str, recv_callback: Awaitable) -> None:
        """初始化客户端

        Args:
            url (str): 服务器 URL
            recv_callback (Awaitable): 接收数据回调函数
        """
        self.url = url
        self.recv_callback = recv_callback
        self.ws = None
        self.loop = asyncio.get_event_loop()

    async def connect(self) -> None:
        """连接服务器
        """
        self.ws = await websockets.connect(self.url)
        if not self.ws.closed:
            asyncio.ensure_future(self.__recv())

    async def send(self, data: Union[str, bytes]) -> None:
        """发送数据

        Args:
            data (Union[str, bytes]): 数据
        """
        await self.ws.send(data)

    async def __recv(self) -> None:
        """接收数据
        """
        while not self.ws.closed:
            data = await self.ws.recv()
            await self.recv_callback(data)
        print('Recv closed')

    def close(self) -> None:
        """关闭连接
        """
        self.ws.close()
        print('Closed')


# 情感云 WebSocket 客户端
class ACClient(Client):

    # 数据接收模式
    class RecvMode:
        # 回调模式
        CALLBACK = 0
        # 异步队列模式
        QUEUE = 1

    def __init__(
        self, url: str,
        app_key: str,
        secret: str,
        client_id: str,
        upload_cycle: int = 3,
        recv_mode: RecvMode = RecvMode.CALLBACK,
        recv_callbacks: Dict[ServiceType, Dict[OperationType, Awaitable]] = None,
    ) -> None:
        """初始化情感云 WebSocket 接口客户端

        Args:
            url (str): 接口 URL
            app_key (str): 情感云 App Key
            secret (str): 情感云 App Secret
            client_id (str): 客户端 ID
            upload_cycle (int, optional): 上传周期. Defaults to 3.
            recv_mode (RecvMode, optional): 数据接收模式. Defaults to RecvMode.CALLBACK.
            recv_callbacks (Dict[ServiceType, Dict[OperationType, Awaitable]], optional): 数据接收回调函数表. Defaults to None.

        Raises:
            ValueError: _description_
        """
        super().__init__(url, self._recv)
        self.url = url
        self.app_key = app_key
        self.secret = secret
        self.client_id = client_id
        self.upload_cycle = upload_cycle
        self.recv_mode = recv_mode
        self.recv_callbacks = recv_callbacks
        self.recv_queue = None
        self.raw_data_bucket = defaultdict(list)
        self.__lock = asyncio.Lock()
        if self.recv_mode == self.RecvMode.QUEUE:
            self.recv_queue = asyncio.Queue()
        elif self.recv_mode == self.RecvMode.CALLBACK:
            if self.recv_callbacks is None:
                raise ValueError("recv_callbacks can not be None")

    async def _responses_table(self) -> Dict[ServiceType, Dict[OperationType, Any]]:
        """响应解析类表

        Returns:
            Dict[ServiceType, Dict[OperationType, Any]]: 响应解析类表
        """
        return {
            Services.Type.SESSION: {
                Services.Operation.Session.CREATE: SessionResponse.Create,
                Services.Operation.Session.RESTORE: SessionResponse.Restore,
                Services.Operation.Session.CLOSE: SessionResponse.Close,
            },
            Services.Type.BASE_SERVICE: {
                Services.Operation.BaseService.INIT: BaseServiceResponse.Init,
                Services.Operation.BaseService.SUBSCRIBE: BaseServiceResponse.Subscribe,
                Services.Operation.BaseService.UNSUBSCRIBE: BaseServiceResponse.Unsubscribe,
                Services.Operation.BaseService.UPLOAD: BaseServiceResponse.Subscribe,
                Services.Operation.BaseService.REPORT: BaseServiceResponse.Report,
                Services.Operation.BaseService.SUBMIT: BaseServiceResponse.SubmitAdditionalInformationToStore,
            },
            Services.Type.AFFECTIVE_SERVICE: {
                Services.Operation.AffectiveService.START: AffectiveServiceResponse.Start,
                Services.Operation.AffectiveService.SUBSCRIBE: AffectiveServiceResponse.Subscribe,
                Services.Operation.AffectiveService.UNSUBSCRIBE: AffectiveServiceResponse.Unsubscribe,
                Services.Operation.AffectiveService.REPORT: AffectiveServiceResponse.Report,
                Services.Operation.AffectiveService.FINISH: AffectiveServiceResponse.Finish,
            }
        }

    async def _recv(self, data) -> None:
        """接收数据

        Args:
            data (str): 数据
        """
        content = gzip.decompress(data)
        content = json.loads(content)
        req = content.get("request", {})
        service = req.get("services")
        op = req.get("op")
        if service is None or op is None:
            print(f"Invalid content: {content}")
            raise ValueError("Invalid data")

        resp_cls = (await self._responses_table()).get(service, {}).get(op)
        if resp_cls is None:
            print(f"Response class not found: {content}")
            raise ValueError(f"Response class not found [{service}:{op}]")

        resp = resp_cls(**content)

        if self.recv_mode == self.RecvMode.CALLBACK:
            callback = self.recv_callbacks.get(service, {}).get(op)
            if callback:
                await callback(resp)
        elif self.recv_mode == self.RecvMode.QUEUE:
            self.recv_queue.put_nowait((service, op, resp))
        else:
            raise ValueError("Invalid recv_mode")

    async def _send(self, request: object) -> None:
        """发送数据

        Args:
            request (object): 请求对象
        """
        data = gzip.compress(str(request).encode())
        return await super().send(data)

    # Session
    async def create_session(self) -> None:
        """创建会话
        """
        await self._send(SessionRequest.Create(
            app_key=self.app_key,
            secret=self.secret,
            client_id=self.client_id,
            upload_cycle=self.upload_cycle,
        ))

    async def restore_session(self, session_id: str) -> None:
        """恢复会话
        """
        if session_id:
            await self._send(SessionRequest.Restore(
                app_key=self.app_key,
                secret=self.secret,
                client_id=self.client_id,
                session_id=session_id,
                upload_cycle=self.upload_cycle,
            ))
        else:
            raise ValueError("session_id is None")

    async def close_session(self) -> None:
        """关闭会话
        """
        await self._send(SessionRequest.Close())

    # Base Service
    async def init_base_services(
        self, services: List[BaseServiceType], storage_settings: Dict = None, algorithm_params: Dict = None
    ) -> None:
        """初始化基础服务

        Args:
            services (List[BaseServiceType]): 服务类型列表
            storage_settings (Dict, optional): 存储设置. Defaults to None.
            algorithm_params (Dict, optional): 算法参数. Defaults to None.
        """
        await self._send(BaseServiceRequest.Init(
            services=services, storage_settings=storage_settings, algorithm_params=algorithm_params,
        ))

    async def subscribe_base_services(self, services: List[BaseServiceType]) -> None:
        """订阅基础服务

        Args:
            services (List[BaseServiceType]): 服务类型列表
        """
        await self._send(BaseServiceRequest.Subscribe(services=services))

    async def unsubscribe_base_services(self, services: List[BaseServiceType]) -> None:
        """取消订阅基础服务

        Args:
            services (List[BaseServiceType]): 服务类型列表
        """
        await self._send(BaseServiceRequest.Unsubscribe(services=services))

    async def upload_raw_data_from_device(self, data: Dict[BaseServiceType, List[Any]]) -> None:
        """上传设备原始数据

        Args:
            data (Dict[BaseServiceType, List[Any]]): 设备原始数据
        """
        async with self.__lock:
            for service, values in data.items():
                bucket = self.raw_data_bucket.get(service, [])
                package = None
                if service == BaseServices.EEG:
                    if len(bucket) < self.upload_cycle * Services.DataUploadCycleLength.EEG:
                        self.raw_data_bucket[service].extend(values)
                        continue
                    else:
                        package = bucket[:self.upload_cycle * Services.DataUploadCycleLength.EEG]
                        self.raw_data_bucket[service] = bucket[self.upload_cycle * Services.DataUploadCycleLength.EEG:]
                elif service == BaseServices.HR:
                    if len(bucket) < self.upload_cycle * Services.DataUploadCycleLength.HR:
                        self.raw_data_bucket[service].extend(values)
                        continue
                    else:
                        package = bucket[:self.upload_cycle * Services.DataUploadCycleLength.HR]
                        self.raw_data_bucket[service] = bucket[self.upload_cycle * Services.DataUploadCycleLength.HR:]
                else:
                    continue
                await self._send(BaseServiceRequest.Upload(services_data={service: package}))

    async def get_base_service_report(
        self, services: List[BaseServiceType], ignore_report_body: bool = False
    ) -> None:
        """获取基础服务报告

        Args:
            services (List[BaseServiceType]): 服务类型列表
            ignore_report_body (bool, optional): 是否忽略报告体. Defaults to False.
        """
        await self._send(BaseServiceRequest.Report(
            services=services, ignore_report_body=ignore_report_body
        ))

    async def submit_additional_information_to_store(self, data: Dict) -> None:
        """提交附加信息到存储

        Args:
            data (Dict): 附加信息
        """
        await self._send(BaseServiceRequest.SubmitAdditionalInformationToStore(data=data))

    # Affective Service
    async def start_affective_services(self, services: List[AffectiveServiceType]) -> None:
        """启动情感计算服务

        Args:
            services (List[AffectiveServiceType]): 服务类型列表
        """
        await self._send(AffectiveServiceRequest.Start(services=services))

    async def subscribe_affective_services(self, services: List[AffectiveServiceType]) -> None:
        """订阅情感计算服务

        Args:
            services (List[AffectiveServiceType]): 服务类型列表
        """
        await self._send(AffectiveServiceRequest.Subscribe(services=services))

    async def unsubscribe_affective_services(self, services: List[AffectiveServiceType]) -> None:
        """取消订阅情感计算服务

        Args:
            services (List[AffectiveServiceType]): 服务类型列表
        """
        await self._send(AffectiveServiceRequest.Unsubscribe(services=services))

    async def get_affective_report(
        self, services: List[AffectiveServiceType], ignore_report_body: bool = False
    ) -> None:
        """获取情感计算服务报告

        Args:
            services (List[AffectiveServiceType]): 服务类型列表
            ignore_report_body (bool, optional): 是否忽略报告体. Defaults to False.
        """
        await self._send(AffectiveServiceRequest.Report(
            services=services, ignore_report_body=ignore_report_body
        ))

    async def finish_affective_service(self, services: List[AffectiveServiceType]) -> None:
        """结束情感计算服务

        Args:
            services (List[AffectiveServiceType]): 服务类型列表
        """
        await self._send(AffectiveServiceRequest.Finish(services=services))
