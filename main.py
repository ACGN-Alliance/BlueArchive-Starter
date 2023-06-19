import time
from typing import Optional, List
import sys, os

from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6.QtCore import QThreadPool, pyqtSignal, QThread, pyqtSlot

from UI.newui import Ui_MainWindow
from qfluentwidgets import PushButton

from adb import ScriptExecutor as se
from adb.adb_utils import Adb
from adb.script import script
from log import LoggerDisplay

__version__ = "inner dev"

class ConnectListener(QThread):
    """
    adb连接监听
    """
    disconnect = pyqtSignal(bool)  # 连接断开时发出信号

    def __init__(self, logger: LoggerDisplay, serial: str):
        """
        初始化监听器

        :param logger:  LoggerDisplay对象
        :param serial: 设备序列号=>用于对应设备
        """
        super().__init__()
        self.logger = logger
        self.serial = serial

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            time.sleep(3)
            if not Adb.if_device_online(self.serial):
                self.disconnect.emit(True)
                self.logger.error("设备断开连接")
                break
        self.quit()


class App(QMainWindow, Ui_MainWindow):
    """
    主窗体

    """

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()  # TODO 多线程开发
        self.setupUi(self)
        self.resize(750, 900)

        # variables init
        self.se: Optional[se] = None
        self.listener = None
        self.deviceMapping = {}  # 设备序列号映射

        # widget init
        self.ConnectionChoiceComboBox.setCurrentText("请点击扫描获取设备列表")
        self.VersionLabel.setText(f"版本:{__version__}")
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)
        self.DisConnectBtn.setEnabled(False)
        self.PlainTextEdit.setReadOnly(True)

        if not os.path.exists("platform-tools"):
            QMessageBox.critical(self, "错误", "未找到adb工具,请将下载好的platform-tools文件夹放置在本程序同一目录下")
            sys.exit()

        self.btn_lst = [self.StartBtn, self.PauseBtn, self.DisConnectBtn, self.ConnectBtn]

        self.logger = LoggerDisplay(self.PlainTextEdit, debug=True)  # 创建日志显示器
        self.logger.reset()
        self.logger.start_info()

        # signal connect
        self.ConnectBtn.clicked.connect(self.connect_adb)
        self.StartBtn.clicked.connect(self.startBtnClickedHandler)
        self.PauseBtn.clicked.connect(self.pauseBtnClickedHandler)
        self.DisConnectBtn.clicked.connect(self.disconnectBtnClickedHandler)
        self.ScanBtn.clicked.connect(self.scanBtnClickedHandler)

    def btnOperation(self, btn_list: List[PushButton], switch: List[bool | None] | bool):
        """
        批量操作按钮
        :param btn_list: 按钮对象列表
        :param switch:
        :return:
        """
        if isinstance(switch, bool):
            for btn in btn_list:
                btn.setEnabled(switch)
        elif isinstance(switch, list):
            if len(btn_list) != len(switch):
                raise ValueError("btnList and switch must have the same length")
            for i in range(len(btn_list)):
                if switch[i] is not None:
                    btn_list[i].setEnabled(switch[i])
                else:
                    continue
        else:
            raise TypeError("switch must be bool or list")

    @pyqtSlot()
    def spPausedHandler(self):
        """
        恢复按钮
        :return:
        """
        if self.se is not None and not self.se.PSW.FINISHED:
            self.btnOperation(self.btn_lst, [True, False, True, False])
            self.logger.info("点击开始按钮开始执行脚本")
        else:
            self.btnOperation(self.btn_lst, [False, False, False, True])
            self.ConnectionChoiceComboBox.setEnabled(True)
            self.logger.warning("连接失效~请重新连接")

    @pyqtSlot()
    def spResumedHandler(self):
        """
        暂停按钮
        :return:
        """
        if self.se is not None and not self.se.PSW.FINISHED:
            self.btnOperation(self.btn_lst, [False, True, None, False])
            self.logger.info("正在运行~点击暂停按钮暂停脚本")
        else:
            self.btnOperation(self.btn_lst, [False, False, False, True])
            self.ConnectionChoiceComboBox.setEnabled(True)
            self.logger.warning("连接失效~请重新连接")

    @pyqtSlot()
    def listenerDisconnectedHandler(self):
        """
        连接断开
        :return:
        """
        self.btnOperation(self.btn_lst, [False, False, False, True])
        self.ConnectionChoiceComboBox.setEnabled(True)
        self.logger.error("连接异常断开~请重新连接")

    @pyqtSlot()
    def startBtnClickedHandler(self):
        """
        只有当sp处于暂停状态时点击才是有效的
        :return:
        """
        if self.se is not None and self.se.PSW.PAUSED:
            self.se.Resume()
            self.btnOperation(self.btn_lst, [False, True, None, False])
            self.label_2.setText("正在运行")
            self.logger.info("开始运行脚本~点击暂停按钮暂停脚本")

    @pyqtSlot()
    def pauseBtnClickedHandler(self):
        """
        只有当sp处于运行状态时点击才是有效的
        :return:
        """
        if self.se is not None and not self.se.PSW.PAUSED:
            self.se.Pause()

            self.btnOperation(self.btn_lst, [True, False, None, False])
            self.label_2.setText("执行暂停")
            self.logger.info("脚本运行已暂停, 点击开始按钮继续运行脚本")

    @pyqtSlot()
    def disconnectBtnClickedHandler(self):
        """
        断开连接
        :return:
        """
        if self.se is not None:
            self.se.Pause()

            self.btnOperation(self.btn_lst, [False, False, False, True])
            self.ConnectionChoiceComboBox.setEnabled(True)
            self.label_2.setText("未连接")
            self.logger.info("连接已断开~请重新连接")

    @pyqtSlot()
    def scanBtnClickedHandler(self):
        """
        扫描设备
        :return:
        """
        def device_info(device_: tuple):
            mode = device_[2].split(":")[0]
            name = device_[3].split(":")[1]
            return f"{name}:{mode}"

        self.ScanBtn.setEnabled(False)
        lst = Adb.get_device_list(all=True)

        if len(lst) == 0:
            self.ScanBtn.setEnabled(True)
            self.logger.error("未扫描到设备~请检查设备是否连接")
            return

        self.ConnectionChoiceComboBox.clear()

        is_first = True
        count = 0
        for device in lst:
            self.ConnectionChoiceComboBox.addItem(device_info(device))
            self.deviceMapping[device[3].split(":")[1]] = device[0]
            count += 1
            if is_first:
                self.ConnectionChoiceComboBox.setCurrentText(device_info(device))
                is_first = False

        self.logger.info(f"扫描完成, 共扫描到{count}台设备~")
        self.ScanBtn.setEnabled(True)

    @pyqtSlot()
    def spFinishedHandler(self):
        self.StartBtn.setEnabled(True)  # 结束运行后可以重新开始
        self.PauseBtn.setEnabled(False)
        self.label_2.setText("已连接")
        self.logger.info("脚本运行结束~")

        # get last thread`s serial number
        self.initSp(self.adb.device_id)

    @pyqtSlot()
    def spAbortedHandler(self):
        self.StartBtn.setEnabled(True)
        self.PauseBtn.setEnabled(False)
        self.logger.warning("脚本运行暂停~")
        # self.sp.Pause()  # 释放资源 (to be deprecated)
        # TODO 断点续运

    @pyqtSlot(int)
    def spInstructionExecutedHandler(self, threadID: int):
        # fetch thread object through threadID
        # ...

        self.logger.info(f"线程: {threadID} 正在执行操作")
        self.label_2.setText("正在运行")

    @pyqtSlot()
    def connect_adb(self):
        """
        连接adb
        :return:
        """

        def connect_fail(label_text: str, err_msg: str):
            self.ConnectBtn.setEnabled(True)
            self.ConnectionChoiceComboBox.setEnabled(True)
            self.label_2.setText(label_text)
            self.logger.error(err_msg)

        self.ConnectBtn.setEnabled(False)
        self.ConnectionChoiceComboBox.setEnabled(False)

        if not self.ConnectionChoiceComboBox.currentText():
            connect_fail("未连接", "设备列表为空, 请重新扫描")
            return

        serial = self.deviceMapping[self.ConnectionChoiceComboBox.currentText().split(":")[0]]
        mode = self.ConnectionChoiceComboBox.currentText().split(":")[1]
        self.adb = Adb(serial=serial)

        self.logger.info(f"连接成功~选择的模式是{mode}, 设备ID为: {serial}")
        # init script parser
        self.initSp(serial)

        # init connect listener
        self.listener = ConnectListener(logger=self.logger, serial=serial)
        #   connect connect listener signal
        self.listener.disconnect.connect(self.listenerDisconnectedHandler)
        #   start connect listener
        self.listener.start()
        self.label_2.setText("已连接")

    def initSp(self, serial):
        # init script parser
        self.se = None
        self.se = se(script=script, logger=self.logger, adb=self.adb, serial=serial)

        #   connect script parser signal
        self.se.resumed.connect(self.spResumedHandler)
        self.se.paused.connect(self.spPausedHandler)
        self.se.done.connect(self.spFinishedHandler)
        # self.sp.aborted.connect(self.spAbortedHandler)
        self.se.started.connect(lambda: self.PauseBtn.setEnabled(True))
        self.se.instructionExecuted.connect(self.spInstructionExecutedHandler)

        #   start script parser
        self.se.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())