from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QStyle
from UI.newui import Ui_MainWindow
import sys
from enum import Enum
from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    MAIN_WINDOW = "main_window"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"app/resource/qss/{theme.value.lower()}/{self.value}.qss"

class App(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setFixedSize(self.width(), self.height())
        self.set_components()
        self.set_trigger()

    def set_components(self):
        self.ComboBox.addItems(["USB调试", "蓝叠模拟器(开发中)"])

        self.ComboBox.setCurrentText("USB调试")

    def set_trigger(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())
