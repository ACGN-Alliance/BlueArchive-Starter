class StopInterruptions(BaseException):
    pass


class CheckFailed(BaseException):
    pass


class ParsedScriptFailed(BaseException):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)
