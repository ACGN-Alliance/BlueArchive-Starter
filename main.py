import time

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

    def enable_btn(self, status: bool):
        """
        恢复按钮
        :param status:
        :return:
        """
        if not status:
            self.sp.quit()
            self.PushButton_2.setEnabled(True)
            self.PushButton_2.clicked.disconnect()
            self.PushButton_2.clicked.connect(self.connect_adb)
            self.PushButton_3.setEnabled(False)

    def connect_adb(self):
        """
        连接adb
        :return:
        """

        self.ComboBox.setEnabled(False)
        mode = connect_mode[self.ComboBox.currentText()]
        self.PushButton.setEnabled(False)

        # print("当前目录: " + os.getcwd())

        if mode == "USB":
            self.sp = sp()
            self.sp.is_run.connect(self.enable_btn)
            self.sp.logger_sign.connect(self.test_logger)  # 日志输出
            self.sp.wait.connect(self.enableStart)
            self.sp.start()
            self.listener = self.ConnectListener()
            self.listener.disconnect.connect(self.enable_btn)
        else:
            self.PushButton.setEnabled(True)
            self.test_logger(-1)

    def test_logger(self, value):
        print("返回值：", value)

    def enableStart(self):
        def start():
            self.PushButton_2.setEnabled(False)
            self.PushButton_3.setEnabled(True)
            self.sp.resume()

        self.PushButton_2.setEnabled(True)
        self.PushButton_2.clicked.connect(start)
        self.label_2.setText("已连接")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
