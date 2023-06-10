from PyQt6.QtWidgets import QApplication, QMainWindow
from UI.newui import Ui_MainWindow
from PyQt6.QtCore import QThreadPool
import sys

connect_mode = {
    "USB调试": "USB",
    "蓝叠模拟器(开发中)": "BlueStacks"
}

class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.pool = None
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.set_components()
        self.set_trigger()

    def set_components(self):
        self.ComboBox.addItems(["USB调试", "蓝叠模拟器(开发中)"])
        self.ComboBox.setCurrentText("USB调试")

    def set_trigger(self):
        self.PushButton.clicked.connect(self.connect_adb)

    def connect_adb(self):
        self.pool = QThreadPool()
        self.thread = self.pool.thread()
        self.thread.setObjectName("ADB")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
