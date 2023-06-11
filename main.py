import time
from typing import Any

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThreadPool, QObject, pyqtSignal, QThread, pyqtSlot
import sys

from UI.newui import Ui_MainWindow
from adb import ScriptParse as sp

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

        # widget init
        self.ConnectionTypeComboBox.addItems([mode for mode in connect_mode.keys()])
        self.ConnectionTypeComboBox.setCurrentText("USB调试")
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(False)

        # signal connect
        self.ConnectBtn.clicked.connect(self.connect_adb)

    @pyqtSlot(bool)
    def enableStartBtn(self, status: bool):
        """
        恢复按钮
        :param status:
        :return:
        """
        if not status:
            self.sp.quit()
            self.StartBtn.setEnabled(True)
            self.StartBtn.clicked.disconnect()
            self.StartBtn.clicked.connect(self.connect_adb)
            self.PauseBtn.setEnabled(False)

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
            self.sp = sp()
            #   connect script parser signal
            self.sp.is_run.connect(self.enableStartBtn)
            self.sp.logger_sign.connect(self.test_logger)  # 日志输出
            self.sp.wait.connect(self.readyForStart)
            #   start script parser
            self.sp.start()

            # init connect listener
            self.listener = ConnectListener()
            #   connect connect listener signal
            self.listener.disconnect.connect(self.enableStartBtn)
            #   start connect listener
            self.listener.start()
        else:
            self.ConnectBtn.setEnabled(True)
            self.test_logger(-1)

    @pyqtSlot(int)
    def test_logger(self, value: int):
        print("返回值：", value)

    @pyqtSlot()
    def readyForStart(self):

        self.StartBtn.setEnabled(True)
        self.StartBtn.clicked.connect(self.start)
        self.label_2.setText("已连接")

    def start(self):
        self.StartBtn.setEnabled(False)
        self.PauseBtn.setEnabled(True)
        self.sp.resume()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
