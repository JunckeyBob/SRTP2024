import hashlib
import time
import json
from typing import Tuple

from affectivecloud.protocols import Services


# 会话请求
class SessionRequest(object):

    @classmethod
    def _sign(cls, app_key: str, secret: str, client_id: str) -> Tuple[str, str]:
        """生成签名

        Args:
            app_key (str): 应用标识
            secret (str): 应用密钥
            client_id (str): 客户端标识

        Returns:
            Tuple[str, str]: 时间戳和签名
        """
        _timestamp = str(int(time.time()))
        params = 'app_key={}&app_secret={}&timestamp={}&user_id={}'.format(
            app_key, secret, _timestamp, client_id or client_id
        )
        _md5 = hashlib.md5()
        _md5.update(params.encode())
        return _timestamp, _md5.hexdigest().upper()

    class _request(object):

        # 会话服务类型：会话服务
        services = Services.Type.SESSION

    # 创建会话
    class Create(_request):

        def __init__(self, app_key: str, secret: str, client_id: str, upload_cycle: int = 3) -> None:
            """初始化创建会话协议

            Args:
                app_key (str): 应用标识
                secret (str): 应用密钥
                client_id (str): 客户端标识
                upload_cycle (int, optional): 上传周期. Defaults to 3.
            """
            self.app_key = app_key
            self.secret = secret
            self.client_id = client_id
            self.upload_cycle = upload_cycle

        def __str__(self) -> str:
            timestamp, sign = SessionRequest._sign(
                self.app_key, self.secret, self.client_id
            )
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.Session.CREATE,
                "kwargs": {
                    "app_key": self.app_key,
                    "sign": sign,
                    "user_id": self.client_id,
                    "timestamp": timestamp,
                    "upload_cycle": self.upload_cycle,
                },
            })

    # 恢复会话
    class Restore(_request):

        def __init__(self, app_key: str, secret: str, client_id: str, session_id: str, upload_cycle: int = 3) -> None:
            """初始化恢复会话协议

            Args:
                app_key (str): 应用标识
                secret (str): 应用密钥
                client_id (str): 客户端标识
                session_id (str): 会话标识
                upload_cycle (int, optional): 上传周期. Defaults to 3.
            """
            self.app_key = app_key
            self.secret = secret
            self.client_id = client_id
            self.session_id = session_id
            self.upload_cycle = upload_cycle

        def __str__(self) -> str:
            timestamp, sign = SessionRequest._sign(
                self.app_key, self.secret, self.client_id
            )
            return json.dumps({
                "services": self.services,
                "op": Services.Operation.Session.RESTORE,
                "kwargs": {
                    "app_key": self.app_key,
                    "sign": sign,
                    "user_id": self.client_id,
                    "timestamp": timestamp,
                    "session_id": self.session_id,
                    "upload_cycle": self.upload_cycle,
                },
            })

    # 结束会话
    class Close(_request):

        def __str__(self) -> str:
            return json.dumps({"services": self.services, "op": Services.Operation.Session.CLOSE})
