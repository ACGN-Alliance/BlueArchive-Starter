import os

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QThreadPool, QObject, pyqtSignal, QThread
import sys

from UI.newui import Ui_MainWindow
from adb import ScriptParse as sp

connect_mode = {
    "USB调试": "USB",
    "蓝叠模拟器(开发中)": "BlueStacks"
}


class App(QMainWindow, Ui_MainWindow):
    sign = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.pool = QThreadPool()  # TODO 多线程开发
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.set_components()
        self.set_trigger()

    def set_components(self):
        self.ComboBox.addItems([mode for mode in connect_mode.keys()])
        self.ComboBox.setCurrentText("USB调试")

        self.PushButton_2.setEnabled(False)
        self.PushButton_3.setEnabled(False)

    def set_trigger(self):
        self.PushButton.clicked.connect(self.connect_adb)

    def connect_adb(self):
        def enable_btn(status: bool):
            self.PushButton.setEnabled(not status)

        mode = connect_mode[self.ComboBox.currentText()]
        self.PushButton.setEnabled(False)

        # print("当前目录: " + os.getcwd())

        if mode == "USB":
            self.sp = sp()
            self.sp.is_run.connect(enable_btn)
            self.sp.logger_sign.connect(self.test_logger)  # 日志输出
            self.sp.wait.connect(self.enableStart)
            self.sp.setObjectName("adb")
            self.sp.start()
        else:
            self.PushButton.setEnabled(True)
            self.test_logger(-1)

    def test_logger(self, value):
        print("返回值：", value)

    def enableStart(self):
        # TODO 实时侦测ADB连接状态
        self.PushButton_2.setEnabled(True)
        self.PushButton_2.connect(self.sp.resume)
        self.label_2.setText("已连接")
        self.sp.pause()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
