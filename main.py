import time
from typing import Any, Optional

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThreadPool, pyqtSignal, QThread, pyqtSlot
import sys

from UI.newui import Ui_MainWindow
from adb import ScriptParse as sp
from adb.script import script

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

        # signal connect
        self.ConnectBtn.clicked.connect(self.connect_adb)
        self.StartBtn.clicked.connect(self.startBtnClickedHandler)
        self.PauseBtn.clicked.connect(self.pauseBtnClickedHandler)

    @pyqtSlot()
    def spPausedHandler(self):
        """
        恢复按钮
        :return:
        """
        if self.sp is not None and not self.sp.PSW.FINISHED:
            self.StartBtn.setEnabled(True)
            self.PauseBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(False)
        else:
            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(True)

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
        else:
            self.StartBtn.setEnabled(False)
            self.PauseBtn.setEnabled(False)
            self.ConnectBtn.setEnabled(True)

    @pyqtSlot()
    def listenerDisconnectedHandler(self):
        """
        连接断开
        :return:
        """
        self.ConnectBtn.setEnabled(True)
        self.ConnectionTypeComboBox.setEnabled(True)
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)
        self.test_logger(-1)

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
            print("正在运行")

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
            print("执行暂停")

    @pyqtSlot()
    def spFinishedHandler(self):
        self.ConnectBtn.setEnabled(True)
        self.ConnectionTypeComboBox.setEnabled(True)
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)
        self.label_2.setText("执行完毕")

    @pyqtSlot(int)
    def spInstructionExecutedHandler(self, threadID: int):
        # fetch thread object through threadID
        # ...

        print("thread:", threadID, "executed an instruction")
        self.label_2.setText("正在运行")

    @pyqtSlot()
    def connect_adb(self):
        """
        连接adb
        :return:
        """

        self.ConnectBtn.setEnabled(False)
        self.ConnectionTypeComboBox.setEnabled(False)

        if (mode := connect_mode[self.ConnectionTypeComboBox.currentText()]) == "USB":
            # init script parser
            self.sp = sp(script=script)

            #   connect script parser signal
            self.sp.resumed.connect(self.spResumedHandler)
            # self.sp.logger_sign.connect(self.test_logger)  # 日志输出

            self.sp.paused.connect(self.spPausedHandler)
            self.sp.finished.connect(self.spFinishedHandler)
            self.sp.started.connect(lambda: self.PauseBtn.setEnabled(True))

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
            self.test_logger(-1)

    @pyqtSlot(int)
    def test_logger(self, value: int):
        print("返回值：", value)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
