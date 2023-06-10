from .adb_utils import Adb
from .script import script_dict
from PyQt6.QtCore import QThread, pyqtSignal

class ScriptParse(QThread):
    logger_sign = pyqtSignal(int)
    is_run = pyqtSignal(bool)
    wait = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.script = script_dict

    def _parse(self, scripts: dict, *args, reset=False) -> tuple:
        print(scripts)
        return ()

    def pause(self):
        """
        暂停线程
        :return:
        """
        self.wait()

    def resume(self):
        """
        恢复线程
        :return:
        """
        self.start()

    def stop(self):
        """
        停止线程
        :return:
        """
        self.quit()

    def run(self, *args, reset=False):
        lst = Adb.get_device_list()
        print("设备列表: " + str(lst))
        if len(lst) == 0:
            self.is_run.emit(False)
            self.logger_sign.emit(0)
        else:
            # self.wait.emit(self.currentThread())
            self.pause()  # 暂停线程
            self._parse(self.script, reset=reset)
        self.stop()