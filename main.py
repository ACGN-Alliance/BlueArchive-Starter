import time
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThreadPool, pyqtSignal, QThread, pyqtSlot
import sys

from UI.newui import Ui_MainWindow
from adb import ScriptParse as sp
from adb.adb_utils import Adb
from adb.script import script
from log import LoggerDisplay

connect_mode = {
    "USB调试": "USB",
    "蓝叠模拟器(开发中)": "BlueStacks"
}


class ConnectListener(QThread):
    """
    adb连接监听
    """
    disconnect = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            time.sleep(3)
            if not sp.device_on():
                self.disconnect.emit(True)
                break
        self.quit()


class App(QMainWindow, Ui_MainWindow):
    sign = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()  # TODO 多线程开发
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())

        # variables init
        self.sp: Optional[sp] = None
        self.listener = None

        # widget init
        self.ConnectionTypeComboBox.addItems([mode for mode in connect_mode.keys()])
        self.ConnectionTypeComboBox.setCurrentText("USB调试")
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)
        self.DisConnectBtn.setEnabled(False)
        self.PlainTextEdit.setReadOnly(True)
        self.logger = LoggerDisplay(self.PlainTextEdit)
        self.logger.reset()
        self.logger.info("欢迎使用碧蓝档案初始号工具~作者: MRSlouzk, 群号: 769521861")

        # signal connect
        self.ConnectBtn.clicked.connect(self.connect_adb)
        self.StartBtn.clicked.connect(self.startBtnClickedHandler)
        self.PauseBtn.clicked.connect(self.pauseBtnClickedHandler)
        self.DisConnectBtn.clicked.connect(self.disconnectBtnClickedHandler)

    @pyqtSlot()
    def spPausedHandler(self):
        """
        恢复按钮
        :return:
        """
        if self.sp is not None and not self.sp.PSW.FINISHED:
            self.StartBtn.setEnabled(True)
            self.PauseBtn.setEnabled(False)
            self.DisConnectBtn.setEnabled(True)
            self.ConnectBtn.setEnabled(False)
            self.logger.info("连接成功~点击开始按钮开始执行脚本")
        else:
            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(False)
            self.DisConnectBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(True)
            self.ConnectionTypeComboBox.setEnabled(True)
            self.logger.warning("连接失效~请重新连接")

    @pyqtSlot()
    def spResumedHandler(self):
        """
        暂停按钮
        :return:
        """
        if self.sp is not None and not self.sp.PSW.FINISHED:
            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(True)
            self.ConnectBtn.setEnabled(False)
            self.logger.info("正在运行~点击暂停按钮暂停脚本")
        else:
            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(False)
            self.DisConnectBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(True)
            self.ConnectionTypeComboBox.setEnabled(True)
            self.logger.warning("连接失效~请重新连接")

    @pyqtSlot()
    def listenerDisconnectedHandler(self):
        """
        连接断开
        :return:
        """
        self.DisConnectBtn.setEnabled(False)
        self.ConnectBtn.setEnabled(True)
        self.ConnectionTypeComboBox.setEnabled(True)
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)
        self.logger.error("连接异常断开~请重新连接")

    @pyqtSlot()
    def startBtnClickedHandler(self):
        """
        只有当sp处于暂停状态时点击才是有效的
        :return:
        """
        if self.sp is not None and self.sp.PSW.PAUSED:
            self.sp.Resume()

            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(True)
            self.ConnectBtn.setEnabled(False)
            self.label_2.setText("正在运行")
            self.logger.info("开始运行脚本~点击暂停按钮暂停脚本")

    @pyqtSlot()
    def pauseBtnClickedHandler(self):
        """
        只有当sp处于运行状态时点击才是有效的
        :return:
        """
        if self.sp is not None and not self.sp.PSW.PAUSED:
            self.sp.Pause()

            self.StartBtn.setEnabled(True)
            self.PauseBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(False)
            self.label_2.setText("执行暂停")
            self.logger.info("脚本运行已暂停, 点击开始按钮继续运行脚本")

    @pyqtSlot()
    def disconnectBtnClickedHandler(self):
        """
        断开连接
        :return:
        """
        if self.sp is not None:
            self.sp.Pause()

            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(False)
            self.DisConnectBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(True)
            self.ConnectionTypeComboBox.setEnabled(True)
            self.label_2.setText("未连接")
            self.logger.info("连接已断开~请重新连接")

    @pyqtSlot()
    def spFinishedHandler(self):
        self.StartBtn.setEnabled(True)  # 结束运行后可以重新开始
        self.PauseBtn.setEnabled(False)
        self.label_2.setText("已连接")
        self.logger.info("脚本运行结束~")

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

        self.ConnectBtn.setEnabled(False)
        self.ConnectionTypeComboBox.setEnabled(False)

        if not Adb.have_device():
            self.ConnectBtn.setEnabled(True)
            self.ConnectionTypeComboBox.setEnabled(True)
            self.label_2.setText("未连接")
            self.logger.error("连接失败, 请检查设备是否存在")
            return

        if (mode := connect_mode[self.ConnectionTypeComboBox.currentText()]) == "USB":
            self.logger.info(f"连接成功~选择的模式是USB")
            # init script parser
            self.sp = sp(script=script)

            #   connect script parser signal
            self.sp.resumed.connect(self.spResumedHandler)
            # self.sp.logger_sign.connect(self.test_logger)  # 日志输出

            self.sp.paused.connect(self.spPausedHandler)
            self.sp.finished.connect(self.spFinishedHandler)
            self.sp.started.connect(lambda: self.PauseBtn.setEnabled(True))
            self.sp.instructionExecuted.connect(self.spInstructionExecutedHandler)

            #   start script parser
            self.sp.start()

            # init connect listener
            self.listener = ConnectListener()
            #   connect connect listener signal
            self.listener.disconnect.connect(self.listenerDisconnectedHandler)
            #   start connect listener
            self.listener.start()
            self.label_2.setText("已连接")
        else:
            self.ConnectBtn.setEnabled(True)
            self.ConnectionTypeComboBox.setEnabled(True)
            self.label_2.setText("未实现")
            self.logger.warning("该功能尚在开发中, 敬请期待")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
