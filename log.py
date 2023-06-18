from typing import Any
import time

from qfluentwidgets import PlainTextEdit


class LoggerDisplay:
    """
    日志显示
    """
    color_dic = {
        "INFO": "blue",
        "ERROR": "red",
        "WARNING": "yellow",
        "DEBUG": "green",
        "CRITICAL": "darkred"
    }

    def __init__(self, plain_text_edit: PlainTextEdit, *args, debug: bool = False):
        self.pte = plain_text_edit
        self.debug_mode = debug

    def reset(self):
        """
        清空日志
        :return:
        """
        self.pte.clear()

    def _log_msg(self, msg: Any, type_: str):
        msg = str(msg)
        log = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] | <font style=\"color:{self.color_dic.get(type_)};\">{type_}</font> |: {msg}\n"
        self.log_file(log)

        return log

    def log_file(self, msg):
        if self.debug_mode:
            msg += "\n"
            with open("ba-starter.log", "w") as f:
                f.write(msg)

    def start_info(self):
        log = f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] | <font style=\"color:blue;\">INFO</font> |: 欢迎使用碧蓝档案初始号工具~作者: <a href=\"https://github.com/ACGN-Alliance\">ACGN-Alliance(Org)</a>, 群号: 769521861\n"
        self.pte.appendHtml(log)

    def info(self, msg: Any):
        self.pte.appendHtml(self._log_msg(msg, "INFO"))

    def error(self, msg: Any):
        self.pte.appendHtml(self._log_msg(msg, "ERROR"))

    def warning(self, msg: Any):
        self.pte.appendHtml(self._log_msg(msg, "WARNING"))

    def debug(self, msg: Any):
        if self.debug_mode:
            self.pte.appendHtml(self._log_msg(msg, "DEBUG"))

    def critical(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "CRITICAL"))
