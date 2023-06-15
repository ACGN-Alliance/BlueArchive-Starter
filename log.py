from typing import Any

from qfluentwidgets import PlainTextEdit
import time


class LoggerDisplay:
    """
    日志显示
    """

    def __init__(self, plain_text_edit: PlainTextEdit, *args, debug: bool = False):
        self.pte = plain_text_edit
        self.debug_mode = debug

    def reset(self):
        self.pte.clear()

    def _log_msg(self, msg: Any, type_: str):
        color_dic = {
            "INFO": "blue",
            "ERROR": "red",
            "WARNING": "yellow",
            "DEBUG": "green",
            "CRITICAL": "darkred"
        }
        msg = str(msg)
        # time.sleep(0.3)  # 为了让日志显示更加舒适
        return f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] | <font style=\"color:{color_dic.get(type_)};\">{type_}</font> |: {msg}\n"

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
