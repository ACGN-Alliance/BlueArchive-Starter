from qfluentwidgets import PlainTextEdit
import time

class LoggerDisplay:
    """
    日志显示
    """
    def __init__(self, plain_text_edit: PlainTextEdit):
        self.pte = plain_text_edit

    def reset(self):
        self.pte.clear()

    def _log_msg(self, msg: str, type_: str):
        color_dic = {
            "INFO": "blue",
            "ERROR": "red",
            "WARNING": "yellow",
            "DEBUG": "green",
            "CRITICAL": "darkred"
        }
        return f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] | <font style=\"color:{color_dic.get(type_)};\">{type_}</font> |: {msg}\n"

    def info(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "INFO"))

    def error(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "ERROR"))

    def warning(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "WARNING"))

    def debug(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "DEBUG"))

    def critical(self, msg: str):
        self.pte.appendHtml(self._log_msg(msg, "CRITICAL"))

