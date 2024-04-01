import asyncio
import sys
import os
import logging
import platform
from tkinter import (
    RIDGE, SUNKEN, END, DISABLED, NORMAL,
    Tk, Label, Text, Button, StringVar, IntVar, Checkbutton, _setit,
    OptionMenu, Frame, Scrollbar, messagebox,
    Event
)
from tkinter.font import Font
from typing import Awaitable, List, Optional, Callable

from bleak.backends.client import BaseBleakClient

from enterble import DeviceScanner, FlowtimeCollector
from affectivecloud.algorithm import BaseServices, AffectiveServices
from affectivecloud.protocols import Services
from affectivecloud import ACClient


if sys.version_info < (3, 7):
    asyncio.get_running_loop = asyncio._get_running_loop

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(asctime)s - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def bleak_log(level=logging.INFO):
    import importlib.metadata
    logger.info('Bleak version: {}'.format(importlib.metadata.version('bleak')))
    logging.getLogger('bleak').setLevel(level=level)


# 设备扫描器
class Scanner:

    @classmethod
    async def scan(cls, model_nbr_uuid: str, callback: Awaitable, name: str = None, timeout=15):
        """扫描设备

        Args:
            name (str): 设备名称
            model_nbr_uuid (str): 设备广播 UUID
            callback (Awaitable): 设备发现回调函数
            timeout (int, optional): 超时设置. Defaults to 5 seconds.
        """
        devices = await DeviceScanner.discover(
            name=name,
            model_nbr_uuid=model_nbr_uuid,
            timeout=timeout,
        )
        if not devices:
            logger.error(Exception('No device found, please try again later.'))

        results = []
        for device in devices:
            try:
                services = await device.get_services()
                for _id, service in services.characteristics.items():
                    logger.info(f'{device} - {_id} - {service}')
                MAC = await device.get_mac_address()
                logger.info(
                    f'{device} - {MAC}'
                )
                results.append((MAC, device.device.address))
                await device.disconnect()
            except Exception as e:
                logger.error(f'{device} - {device.identify} - {e}')

        callback(results)


class Demo:

    def __init__(self) -> None:
        self.loop = asyncio.get_event_loop()
        # 初始化设备扫描器
        self.scanner = Scanner()

        # 初始化 Flowtime 数据采集器
        self.collector: FlowtimeCollector = None
        self.show_collector_data: bool = False

        # 初始化 情感云 客户端
        self.client = ACClient(
            url="wss://server.affectivecloud.cn/ws/algorithm/v2/",
            app_key=os.environ.get("APP_KEY"),
            secret=os.environ.get("APP_SECRET"),
            client_id=os.environ.get("CLIENT_ID"),
            recv_callbacks={
                Services.Type.SESSION: {
                    Services.Operation.Session.CREATE: self.session_create,
                    Services.Operation.Session.RESTORE: self.session_restore,
                    Services.Operation.Session.CLOSE: self.session_close,
                },
                Services.Type.BASE_SERVICE: {
                    Services.Operation.BaseService.INIT: self.base_service_init,
                    Services.Operation.BaseService.SUBSCRIBE: self.base_service_subscribe,
                    Services.Operation.BaseService.REPORT: self.base_service_report,
                },
                Services.Type.AFFECTIVE_SERVICE: {
                    Services.Operation.AffectiveService.START: self.affective_service_start,
                    Services.Operation.AffectiveService.SUBSCRIBE: self.affective_service_subscribe,
                    Services.Operation.AffectiveService.REPORT: self.affective_service_report,
                    Services.Operation.AffectiveService.FINISH: self.affective_service_finish,
                },
            },
            # ping_interval=1,
            # ping_timeout=1,
            # timeout=1,
            # close_timeout=None,
            # reconnect=True,
            # reconnect_interval=5,
        )
        self.session_id = None
        self.upload_switch = False

        # 初始化 GUI
        self.tk = Tk()
        self.screen_w, self.screen_h = 1024, 768
        w, h = self.tk.maxsize()
        x, y = (w - self.screen_w)//2, (h - self.screen_h)//2
        self.tk.geometry("{}x{}+{}+{}".format(self.screen_w, self.screen_h, x, y))
        self.tk.title("Demo")

        log_frame = Frame(self.tk, borderwidth=1, relief=RIDGE)
        log_frame.grid(row=0, column=0)
        log_frame.place(x=5, y=5, width=self.screen_w - 10, height=self.screen_h - 290)

        label = Label(log_frame, text="日志")
        label.grid(row=0, column=0)
        label.place(x=5, y=5, width=self.screen_w - 20, height=20)

        font = Font(log_frame, size=12, )
        self.text = Text(log_frame, font=font, bg="black", fg="lightgreen")
        self.text.grid(row=1, column=0)
        self.text.place(x=5, y=30, width=self.screen_w - 45, height=768-290-20)
        scroll = Scrollbar(log_frame, orient="vertical", command=self.text.yview)
        self.text.config(yscrollcommand=scroll.set)
        self.text.see(END)
        scroll.grid(row=1, column=1, sticky="ns")
        scroll.place(x=self.screen_w - 40, y=30, width=20, height=self.screen_h-290-20)

        # 控制器
        controller_frame = Frame(self.tk, borderwidth=1, relief=RIDGE)
        controller_frame.grid(row=1, column=0)
        controller_frame.place(x=5, y=self.screen_h-275, width=self.screen_w - 10, height=255)

        # 硬件
        hardware_frame = Frame(controller_frame, borderwidth=1, relief=SUNKEN)
        hardware_frame.grid(row=1, column=0)
        hardware_frame.place(x=5, y=5, width=self.screen_w - 10, height=35)

        hardware_label = Label(hardware_frame, text="硬件控制")
        hardware_label.grid(row=0, column=0)

        self.scan_device_btn = Button(hardware_frame, text="扫描设备")
        self.scan_device_btn.grid(row=0, column=1)
        self.scan_device_btn.bind("<Button-1>", self.scan_device)

        self.device_selected = StringVar(hardware_frame)
        self.device_list = OptionMenu(
            hardware_frame, self.device_selected, "请先扫描设备", command=self.select_device
        )
        self.device_list.grid(row=0, column=2)

        self.connect_device_btn = Button(hardware_frame, text="连接设备")
        self.connect_device_btn.grid(row=0, column=3)
        self.connect_device_btn.bind("<Button-1>", self.connect_device)
        self.connect_device_btn.config(state=DISABLED)

        self.disconnect_device_btn = Button(hardware_frame, text="断开设备")
        self.disconnect_device_btn.grid(row=0, column=4)
        self.disconnect_device_btn.bind("<Button-1>", self.disconnect_device)
        self.disconnect_device_btn.config(state=DISABLED)

        self.show_collector_data_btn = Button(hardware_frame, text="显示硬件数据")
        self.show_collector_data_btn.grid(row=0, column=5)
        self.show_collector_data_btn.bind("<Button-1>", self.show_collector_data_btn_click)
        self.show_collector_data_btn.config(state=DISABLED)

        # 情感云 会话
        session_frame = Frame(controller_frame, borderwidth=1, relief=SUNKEN)
        session_frame.grid(row=2, column=0)
        session_frame.place(x=5, y=45, width=self.screen_w - 10, height=35)

        session_label = Label(session_frame, text="会话控制")
        session_label.grid(row=0, column=0)

        self.create_connect_btn = Button(session_frame, text="创建连接")
        self.create_connect_btn.grid(row=0, column=1)
        self.create_connect_btn.bind("<Button-1>", self.create_connect)

        self.create_session_btn = Button(session_frame, text="创建会话")
        self.create_session_btn.grid(row=0, column=2)
        self.create_session_btn.bind("<Button-1>", self.create_session)
        self.create_session_btn.config(state=DISABLED)

        self.restore_session_btn = Button(session_frame, text="恢复会话")
        self.restore_session_btn.grid(row=0, column=3)
        self.restore_session_btn.bind("<Button-1>", self.restore_session)
        self.restore_session_btn.config(state=DISABLED)

        self.close_session_btn = Button(session_frame, text="关闭会话")
        self.close_session_btn.grid(row=0, column=4)
        self.close_session_btn.bind("<Button-1>", self.close_session)
        self.close_session_btn.config(state=DISABLED)

        # 情感云 基础服务
        base_service_frame = Frame(controller_frame, borderwidth=1, relief=SUNKEN)
        base_service_frame.grid(row=3, column=0)
        base_service_frame.place(x=5, y=85, width=self.screen_w - 10, height=80)

        base_service_label = Label(base_service_frame, text="基础服务控制")
        base_service_label.grid(row=0, column=0)

        self.base_services = {
            service: IntVar(base_service_frame)
            for service in (BaseServices.EEG, BaseServices.HR)
        }
        self.base_services_check_btn = {}
        for i, service in enumerate(self.base_services.keys()):
            check_btn = Checkbutton(
                base_service_frame, text=service.upper(),
                variable=self.base_services[service],
                command=self.base_service_check,
            )
            self.base_services[service].get()
            check_btn.grid(row=1, column=i)
            check_btn.select()
            self.base_services_check_btn[service] = check_btn

        self.init_base_service_btn = Button(base_service_frame, text="初始化基础服务")
        self.init_base_service_btn.grid(row=2, column=0)
        self.init_base_service_btn.bind("<Button-1>", self.init_base_service)
        self.init_base_service_btn.config(state=DISABLED)

        self.subscribe_base_service_btn = Button(base_service_frame, text="订阅基础服务")
        self.subscribe_base_service_btn.grid(row=2, column=1)
        self.subscribe_base_service_btn.bind("<Button-1>", self.subscribe_base_service)
        self.subscribe_base_service_btn.config(state=DISABLED)

        self.upload_base_service_btn = Button(base_service_frame, text="开始上传数据")
        self.upload_base_service_btn.grid(row=2, column=2)
        self.upload_base_service_btn.bind("<Button-1>", self.upload_base_service)
        self.upload_base_service_btn.config(state=DISABLED)

        self.stop_upload_base_service_btn = Button(base_service_frame, text="停止上传数据")
        self.stop_upload_base_service_btn.grid(row=2, column=3)
        self.stop_upload_base_service_btn.bind("<Button-1>", self.stop_upload_base_service)
        self.stop_upload_base_service_btn.config(state=DISABLED)

        self.get_base_service_report_btn = Button(base_service_frame, text="获取基础服务报告")
        self.get_base_service_report_btn.grid(row=2, column=4)
        self.get_base_service_report_btn.bind("<Button-1>", self.get_base_service_report)
        self.get_base_service_report_btn.config(state=DISABLED)

        # 情感云 情感计算服务
        affective_service_frame = Frame(controller_frame, borderwidth=1, relief=SUNKEN)
        affective_service_frame.grid(row=4, column=0)
        affective_service_frame.place(x=5, y=170, width=self.screen_w - 10, height=80)

        affective_service_label = Label(affective_service_frame, text="情感计算服务控制")
        affective_service_label.grid(row=0, column=0)

        self.affective_services = {
            service: IntVar(affective_service_frame)
            for service in (
                AffectiveServices.ATTENTION,
                AffectiveServices.RELAXATION,
                AffectiveServices.PRESSURE,
                AffectiveServices.COHERENCE,
            )
        }
        self.affective_services_check_btn = {}
        for i, service in enumerate(self.affective_services.keys()):
            check_btn = Checkbutton(
                affective_service_frame, text=service.upper(),
                variable=self.affective_services[service],
                command=self.affective_service_check,
            )
            check_btn.grid(row=1, column=i)
            check_btn.select()
            self.affective_services_check_btn[service] = check_btn

        self.start_affective_service_btn = Button(affective_service_frame, text="开启情感计算服务")
        self.start_affective_service_btn.grid(row=2, column=0)
        self.start_affective_service_btn.bind("<Button-1>", self.start_affective_service)
        self.start_affective_service_btn.config(state=DISABLED)

        self.subscribe_affective_service_btn = Button(affective_service_frame, text="订阅情感计算服务")
        self.subscribe_affective_service_btn.grid(row=2, column=1)
        self.subscribe_affective_service_btn.bind("<Button-1>", self.subscribe_affective_service)
        self.subscribe_affective_service_btn.config(state=DISABLED)

        self.get_affective_service_report_btn = Button(affective_service_frame, text="获取情感计算服务报告")
        self.get_affective_service_report_btn.grid(row=2, column=2)
        self.get_affective_service_report_btn.bind("<Button-1>", self.get_affective_service_report)
        self.get_affective_service_report_btn.config(state=DISABLED)

        self.finish_affective_service_btn = Button(affective_service_frame, text="结束情感计算服务")
        self.finish_affective_service_btn.grid(row=2, column=3)
        self.finish_affective_service_btn.bind("<Button-1>", self.finish_affective_service)
        self.finish_affective_service_btn.config(state=DISABLED)

    async def run(self):
        """运行程序
        """
        self.tk.resizable(False, False)

        while True:
            self.tk.update()
            await asyncio.sleep(1/60)

    def write_log(self, text: str) -> None:
        """写入日志到界面日志控制台

        Args:
            text: 日志内容
        """
        self.text.insert(END, text + '\n')
        self.text.see(END)

    def widget_disabled(self, widget) -> bool:
        """检查控件是否可用

        Args:
            widget: 控件

        Returns:
            bool: 控件是否可用
        """
        return widget.cget('state') == DISABLED

    # --------------------------------------------------
    # 硬件
    # 硬件操作
    def scan_device(self, event: Event) -> None:
        """扫描设备
        """
        if self.widget_disabled(event.widget):
            return
        print("Scan device")
        self.write_log("Device scanning...")
        asyncio.ensure_future(Scanner.scan(
            # name="Flowtime Headband",  # 不知道设备名, 可以不指定
            model_nbr_uuid="0000ff10-1212-abcd-1523-785feabcd123",
            timeout=5,
            callback=self._scan_device_callback
        ))
        self.scan_device_btn.config(state=DISABLED)
        self.connect_device_btn.config(state=DISABLED)
        self.disconnect_device_btn.config(state=DISABLED)

    def select_device(self, event: Event) -> None:
        """选择设备
        """
        print("select device")

    def connect_device(self, event: Event) -> None:
        """连接设备
        """
        if self.widget_disabled(event.widget):
            return
        print("connect device")
        self.write_log("Device connecting...")
        self.collector = FlowtimeCollector(
            # name="Flowtime Headband",  # 不知道设备名, 可以不指定
            model_nbr_uuid="0000ff10-1212-abcd-1523-785feabcd123",
            device_identify=self.device_selected.get(),
            device_disconnected_callback=self.device_disconnected,
            soc_data_callback=self.soc_callback,
            wear_status_callback=self.wear_status_callback,
            eeg_data_callback=self.eeg_data_collector,
            hr_data_callback=self.hr_data_collector,
        )
        asyncio.ensure_future(self.collector.start())
        asyncio.ensure_future(self.collector.wait_for_stop())
        self.scan_device_btn.config(state=DISABLED)
        self.connect_device_btn.config(state=DISABLED)
        self.show_collector_data_btn.config(state=NORMAL)

    def disconnect_device(self, event: Event) -> None:
        """断开设备
        """
        if self.widget_disabled(event.widget):
            return
        print("disconnect device")
        self.write_log("Device disconnecting...")
        asyncio.ensure_future(self.collector.stop())
        self.scan_device_btn.config(state=NORMAL)
        self.connect_device_btn.config(state=NORMAL)
        self.disconnect_device_btn.config(state=DISABLED)
        self.show_collector_data_btn.config(state=DISABLED)

    def show_collector_data_btn_click(self, event: Event) -> None:
        """显示/隐藏采集器数据
        """
        if self.widget_disabled(event.widget):
            return
        self.show_collector_data = not self.show_collector_data
        if self.show_collector_data:
            self.show_collector_data_btn.config(text="关闭数据显示")
            self.write_log("硬件数据显示开启")
        else:
            self.show_collector_data_btn.config(text="打开数据显示")
            self.write_log("硬件数据显示关闭")

    # 硬件操作回调接口
    def _scan_device_callback(self, devices) -> None:
        """扫描设备回调接口
        """
        print(devices)
        for i, device in enumerate(devices):
            select_option = device[0] if platform.system() != "Darwin" else device[1]
            self.device_list['menu'].add_command(
                label=select_option,
                command=_setit(self.device_selected, select_option, self.select_device),
            )
            self.device_selected.set(select_option)
            self.write_log("Device found({}): [MAC: {}] [UUID: {}]".format(
                i, device[0], device[1])
            )
        print("Scan device done")
        self.write_log("Device scanned done.")
        self.scan_device_btn.config(state=NORMAL)
        if len(devices) > 0:
            self.connect_device_btn.config(state=NORMAL)
        else:
            self.write_log("Device not found. please try again later.")

    async def device_disconnected(self, device: Optional[Callable[["BaseBleakClient"], None]]) -> None:
        """设备断开回调接口
        """
        print("Device disconnected")
        self.write_log("Device disconnected.")
        self.scan_device_btn.config(state=NORMAL)
        self.connect_device_btn.config(state=NORMAL)
        self.disconnect_device_btn.config(state=DISABLED)
        self.show_collector_data_btn.config(state=DISABLED)

    async def soc_callback(self, soc: float) -> None:
        """SOC回调接口
        """
        self.disconnect_device_btn.config(state=NORMAL)
        self.write_log("SOC: {}".format(soc))

    async def wear_status_callback(self, wear_status: bool) -> None:
        """穿戴状态回调接口
        """
        self.write_log("Wear status: {}".format(wear_status))
        self.device_selected

    async def eeg_data_collector(self, data: List[int]) -> None:
        """EEG数据采集回调接口
        """
        # logger.info(f'EEG: {data}')
        if self.upload_switch and self.client.ws and not self.client.ws.closed:
            asyncio.ensure_future(self.client.upload_raw_data_from_device({
                BaseServices.EEG: list(data),
            }))

        # if self.show_collector_data:
        #     self.write_log("EEG: {}".format(data))

    async def hr_data_collector(self, data: int):
        """HR数据采集回调接口
        """
        logger.info(f'HR: {data}')
        if self.upload_switch and self.client.ws and not self.client.ws.closed:
            asyncio.ensure_future(self.client.upload_raw_data_from_device({
                BaseServices.HR: [data],
            }))

        # if self.show_collector_data:
        #     self.write_log("HR: {}".format(data))

    # --------------------------------------------------
    # 情感云操作
    # 会话
    def create_connect(self, event: Event) -> None:
        """创建情感云连接
        """
        if self.widget_disabled(event.widget):
            return
        if self.collector is None or self.collector._stop:
            self.write_log("Device disconnect.")
            msg = messagebox.askyesno("提示", "设备未连接, 是否继续连接情感云服务器?")
            if not msg:
                return
        asyncio.ensure_future(self.client.connect())
        self.write_log("Connected to ac server.")
        self.create_connect_btn.config(state=DISABLED)
        self.create_session_btn.config(state=NORMAL)
        if self.session_id:
            self.restore_session_btn.config(state=NORMAL)
        else:
            self.restore_session_btn.config(state=DISABLED)
        self.close_session_btn.config(state=DISABLED)

    def create_session(self, event: Event) -> None:
        """创建情感云会话
        """
        if self.widget_disabled(event.widget):
            return
        asyncio.ensure_future(self.client.create_session())
        print("create session")
        self.write_log("Create ac session.")
        self.create_connect_btn.config(state=DISABLED)
        self.create_session_btn.config(state=DISABLED)
        self.restore_session_btn.config(state=DISABLED)
        self.close_session_btn.config(state=NORMAL)

    def restore_session(self, event: Event) -> None:
        """恢复情感云会话
        """
        if self.widget_disabled(event.widget):
            return
        print("restore session")
        asyncio.ensure_future(self.client.restore_session(self.session_id))
        self.write_log("Restore ac session.")
        self.create_connect_btn.config(state=DISABLED)
        self.create_session_btn.config(state=DISABLED)
        self.restore_session_btn.config(state=DISABLED)
        self.close_session_btn.config(state=NORMAL)

    def close_session(self, event: Event) -> None:
        """关闭情感云会话
        """
        if self.widget_disabled(event.widget):
            return
        print("close session")
        self.upload_switch = False
        asyncio.ensure_future(self.client.close_session())
        self.write_log("Close session.")
        self.create_connect_btn.config(state=NORMAL)
        self.create_session_btn.config(state=NORMAL)
        self.session_id = None
        self.restore_session_btn.config(state=DISABLED)
        self.close_session_btn.config(state=DISABLED)

        self.init_base_service_btn.config(state=DISABLED)
        self.subscribe_base_service_btn.config(state=DISABLED)
        self.upload_base_service_btn.config(state=DISABLED)
        self.stop_upload_base_service_btn.config(state=DISABLED)
        self.get_base_service_report_btn.config(state=DISABLED)

        self.start_affective_service_btn.config(state=DISABLED)
        self.subscribe_affective_service_btn.config(state=DISABLED)
        self.get_affective_service_report_btn.config(state=DISABLED)
        self.finish_affective_service_btn.config(state=DISABLED)

    # 基础服务
    def base_service_check(self) -> None:
        """基础服务选中
        """
        print("base service check")

    def init_base_service(self, event: Event) -> None:
        """初始化基础服务
        """
        if self.widget_disabled(event.widget):
            return
        print("init base service")
        asyncio.ensure_future(self.client.init_base_services(services=[
            service for service in self.base_services if self.base_services[service].get() == 1
        ]))
        self.write_log("Init base services.")
        self.init_base_service_btn.config(state=DISABLED)
        self.subscribe_base_service_btn.config(state=NORMAL)
        self.upload_base_service_btn.config(state=NORMAL)

        self.start_affective_service_btn.config(state=NORMAL)

    def subscribe_base_service(self, event: Event) -> None:
        """订阅基础服务
        """
        if self.widget_disabled(event.widget):
            return
        print("subscribe base service")
        asyncio.ensure_future(self.client.subscribe_base_services(services=[
            service for service in self.base_services if self.base_services[service].get() == 1
        ]))
        self.write_log("Subscribe base services.")
        self.subscribe_base_service_btn.config(state=DISABLED)

    def upload_base_service(self, event: Event) -> None:
        """上传基础服务生物数据
        """
        if self.widget_disabled(event.widget):
            return
        print("upload base service")
        self.upload_switch = True
        self.write_log("Upload base services.")
        self.upload_base_service_btn.config(state=DISABLED)
        self.stop_upload_base_service_btn.config(state=NORMAL)
        self.get_base_service_report_btn.config(state=NORMAL)
        self.get_affective_service_report_btn.config(state=NORMAL)

    def stop_upload_base_service(self, event: Event) -> None:
        """停止上传基础服务生物数据
        """
        if self.widget_disabled(event.widget):
            return
        print("stop upload base service")
        self.upload_switch = False
        self.write_log("Stop upload base services.")
        self.upload_base_service_btn.config(state=NORMAL)
        self.stop_upload_base_service_btn.config(state=DISABLED)
        self.get_base_service_report_btn.config(state=DISABLED)
        self.get_affective_service_report_btn.config(state=DISABLED)

    def get_base_service_report(self, event: Event) -> None:
        """获取基础服务数据报告
        """
        if self.widget_disabled(event.widget):
            return
        print("get base service report")
        asyncio.ensure_future(self.client.get_base_service_report(services=[
            service for service in self.base_services if self.base_services[service].get() == 1
        ]))
        self.write_log("Get base service report.")
        self.get_base_service_report_btn.config(state=DISABLED)

    # 情感云服务
    def affective_service_check(self) -> None:
        """情感云服务选中
        """
        print("affective service check")

    def start_affective_service(self, event: Event) -> None:
        """开始情感计算服务
        """
        if self.widget_disabled(event.widget):
            return
        print("start affective service")
        asyncio.ensure_future(self.client.start_affective_services(services=[
            service for service in self.affective_services if self.affective_services[service].get() == 1
        ]))
        self.write_log("Start affective services.")
        self.start_affective_service_btn.config(state=DISABLED)
        self.subscribe_affective_service_btn.config(state=NORMAL)
        self.get_affective_service_report_btn.config(state=NORMAL)
        self.finish_affective_service_btn.config(state=NORMAL)

    def subscribe_affective_service(self, event: Event) -> None:
        """订阅情感计算服务
        """
        if self.widget_disabled(event.widget):
            return
        print("subscribe affective service")
        asyncio.ensure_future(self.client.subscribe_affective_services(services=[
            service for service in self.affective_services if self.affective_services[service].get() == 1
        ]))
        self.write_log("Subscribe affective services.")
        self.subscribe_affective_service_btn.config(state=DISABLED)

    def get_affective_service_report(self, event: Event) -> None:
        """获取情感计算服务数据报告
        """
        if self.widget_disabled(event.widget):
            return
        print("get affective service report")
        asyncio.ensure_future(self.client.get_affective_report(services=[
            service for service in self.affective_services if self.affective_services[service].get() == 1
        ]))
        self.write_log("Get affective services report.")
        self.get_affective_service_report_btn.config(state=DISABLED)

    def finish_affective_service(self, event: Event) -> None:
        """结束情感计算服务
        """
        if self.widget_disabled(event.widget):
            return
        print("finish affective service")
        asyncio.ensure_future(self.client.finish_affective_service(services=[
            service for service in self.affective_services if self.affective_services[service].get() == 1
        ]))
        self.write_log("Finish affective services.")
        self.start_affective_service_btn.config(state=NORMAL)

    # --------------------------------------------------
    # 情感云返回数据回调接口
    # 会话
    async def session_create(self, data: str) -> None:
        """会话创建回调
        """
        print(f"< {data}")
        if data.code == 0:
            self.session_id = data.session_id
            self.write_log(f"Session create success. Session id: {self.session_id}")
            self.init_base_service_btn.config(state=NORMAL)
        else:
            self.session_id = None
        self.write_log(f"< {data}")

    async def session_restore(self, data: str) -> None:
        """会话恢复回调
        """
        print(f"< {data}")
        if data.code == 0:
            self.session_id = data.session_id
            self.write_log(f"Session restore success. Session id: {self.session_id}")
            self.init_base_service_btn.config(state=NORMAL)
        else:
            self.session_id = None
        self.write_log(f"< {data}")

    async def session_close(self, data: str) -> None:
        """会话关闭回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")

    # 基础服务
    async def base_service_init(self, data: str) -> None:
        """基础服务初始化回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")

    async def base_service_subscribe(self, data: str) -> None:
        """基础服务订阅回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")

    async def base_service_report(self, data: str) -> None:
        """基础服务数据报告回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")
        self.get_base_service_report_btn.config(state=NORMAL)

    # 情感服务
    async def affective_service_start(self, data: str) -> None:
        """情感服务开始回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")

    async def affective_service_subscribe(self, data: str) -> None:
        """情感服务订阅回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")

    async def affective_service_report(self, data: str) -> None:
        """情感服务数据报告回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")
        self.get_affective_service_report_btn.config(state=NORMAL)

    async def affective_service_finish(self, data: str) -> None:
        """情感服务结束回调
        """
        print(f"< {data}")
        self.write_log(f"< {data}")


if __name__ == '__main__':
    bleak_log(logging.INFO)
    os.environ['APP_KEY'] = '31cd1a8c-26c6-11ee-a8e0-c2e57b17aa9a'
    os.environ['APP_SECRET'] = 'f7b84b59f8131ede0efb6eba51b0cab7'
    os.environ['CLIENT_ID'] = '8d99dc2ded8696dbbf87b5af45597cb5'
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Demo().run())