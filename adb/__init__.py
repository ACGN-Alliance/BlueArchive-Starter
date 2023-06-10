import time

from .adb_utils import Adb
from .script import script_dict
from PyQt6.QtCore import QThread, pyqtSignal


def _have_device():
    return len(Adb.get_device_list()) != 0


class ScriptParse(QThread):
    logger_sign = pyqtSignal(int)
    is_run = pyqtSignal(bool)
    wait = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.script = script_dict
        self.is_clicked: bool = False

    def __del__(self):
        self.quit()

    def _parse(self, scripts: dict, *args, reset=False) -> tuple:
        print(scripts)
        return ()

    def execute(self, cmd: tuple):
        pass

    @staticmethod
    def device_on():
        return Adb.have_device()

    def resume(self):
        self.is_clicked = True

    def run(self, *args, reset=False):
        lst = Adb.get_device_list()
        print("设备列表: " + str(lst))
        if len(lst) == 0:
            self.is_run.emit(False)
            self.logger_sign.emit(0)
        else:
            self.is_clicked = False
            self.wait.emit()  # 暂停线程
            while True:
                time.sleep(1)
                if not self.device_on():
                    self.is_run.emit(False)
                if self.is_clicked:
                    self.is_clicked = False
                    break

            self._parse(self.script, reset=reset)
        self.is_run.emit(False)
