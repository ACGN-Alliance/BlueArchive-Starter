import io
from typing import Optional
from weakref import WeakValueDictionary

from ocr import compare_img
from .Interruptions import *
from .adb_utils import Adb
from .script import script_dict, Script
from log import LoggerDisplay

from PyQt6.QtCore import QThread, pyqtSignal

from .script_parser import CompiledExpr


class ScriptExecutorPSW:
    """
    a class that record the state of ScriptParse(程序状态字寄存器)
    """

    def __init__(self):
        self.PAUSED = False
        self.FINISHED = False
        self.ENABLE_INTERRUPT = True
        self.REQUIRE_SLEEP = -1


class ScriptExecutor(QThread):
    paused = pyqtSignal()
    resumed = pyqtSignal()

    # not implemented,emit ID of the sp, so that the main thread can know which sp is during interrupt period
    interrupt = pyqtSignal(int)
    instructionExecuted = pyqtSignal(int)

    done = pyqtSignal(int)
    aborted = pyqtSignal(int)

    def device_on(self) -> bool:
        return self.adb.device_id == self.serial

    def __init__(self,
                 scriptFile: str,
                 adb: Adb,
                 serial: str,
                 logger: LoggerDisplay,
                 *args,
                 id_: int = 0,
                 instruction_pointer: int = -1,
                 ):
        super().__init__()

        # thread ID
        self.ID = id_
        # record the exception that cause the thread to stop
        self.interruption = None
        # script file path
        self.scriptFile = scriptFile
        # a pointer that point to the next instruction, VISIBLE to the user
        self.IP = instruction_pointer
        # a Register that save the current instruction, INVISIBLE to the user
        self.IR = None
        # a Register that save the current state of ScriptParse,VISIBLE to the user
        self.PSW = ScriptExecutorPSW()
        # logger
        self.logger = logger
        # device serial
        self.serial = serial
        # adb
        self.adb = adb

        self._globals = {"__builtins__": None}
        self._locals = {"__builtins__": None}

    # =============== PRIVATE METHODS ===============
    def _initScript(self):
        self.exception = None

        try:
            self.script = Script(self.scriptFile)
        except Exception as e:
            raise ParsedScriptFailed(e.args[0])

        self.IP = max(self.script.BeginAddress, self.IP)

    def _parser(self, instruction: dict):
        """
        脚本解析
        :param instruction:
        :return:
        """
        name = instruction.get("name", None)
        action = instruction.get("action", None)
        args = {k: v for k, v in instruction.items() if k not in ("name", "action")}

        if action == "exit":
            return -1
        elif action == "adb":
            out = self.adb.get_command_output(args["args"])
        elif action == "ocr":
            pass
        else:
            raise NotImplementedError

    def _fetchInstruction(self):
        """
        fetch the next instruction
        """
        self.IR = self.script[self.IP]

        if self.IR is None:
            raise StopInterruptions

        self.IP += 1

    def _executeInstruction(self):
        """
        execute the current instruction
        """
        # simulate executing...
        # TODO 换成真正的执行，函数已经写好了

        self.logger.info(f"正在执行:{self.IR}")

        match self.IR["type"]:
            case "exit":
                raise StopInterruptions

        self.instructionExecuted.emit(self.ID)
        return True

    def _interruptPeriod(self):
        """
        interrupt period:
        followed the fetchInstruction and the executeInstruction period,
        there is a period that can check state and be allowed to process and answer the external events and requests
        """

        # process interrupt operations that can be ignored

        if self.PSW.ENABLE_INTERRUPT:
            # disable interrupt 关中断
            self.PSW.ENABLE_INTERRUPT = False

            # process pause interruption instruction
            if self.PSW.PAUSED:
                self._onPaused()
                # process interrupt 中断处理
                while self.PSW.PAUSED:
                    self.msleep(100)
                    self._interruptPeriod()
                self._onResumed()

            # enable interrupt 开中断
            self.PSW.ENABLE_INTERRUPT = True

        # process interrupt operations that can not be ignored
        # check state
        if not self.device_on():
            self.interruption = StopInterruptions()

        self.interrupt.emit(self.ID)

        # process exceptions,
        match self.interruption:
            case StopInterruptions():
                return False
            case ParsedScriptFailed():
                self.logger.error(self.interruption.args)
                return False

        return True
        # check state

    def _onPaused(self):
        """
        issued when needed a pause,box the pause event
        """
        self.PSW.PAUSED = True
        self.paused.emit()
        self.logger.debug("任务暂停")

    def _onResumed(self):
        """
        issued when needed a resume,box the resume event
        """
        self.PSW.PAUSED = False
        self.resumed.emit()
        self.logger.debug("任务恢复")

    def _evaInContext(self, expr: CompiledExpr):
        """
        evaluate the expression in current context
        :param expr:
        :return:
        """
        return eval(expr.compiled_expr, self._globals, self._locals)

    def _exec(self, stmt: str):
        """
        execute the statement
        :param stmt:
        :return:
        """
        exec(stmt, self._globals, self._locals)

    def _instructionUniverseBlock(self):
        # 处理block
        if block := self.IR["block"]:
            # 处理block中的arg子句
            if "var" in block:
                for arg_stmt in block["var"]:
                    if arg_stmt["del"]:
                        self._globals.pop(arg_stmt["ID"])
                    else:
                        self._globals[arg_stmt["ID"]] = self._evaInContext(arg_stmt["value"])

            if "check" in block:
                # 处理block中的check子句
                for check_stmt in block["check"]:
                    # hard | soft
                    check_mode = check_stmt["check_mode"]
                    if not self._evaInContext(check_stmt["test_expr"]):
                        if check_mode == "hard":
                            raise CheckFailed
                        elif check_mode == "soft":
                            # TODO soft check 输出警告
                            pass
                        else:
                            raise NotImplementedError

            if "stay" in block:
                # 处理block中的stay子句
                for stay_stmt in block["stay"]:
                    if not self._evaInContext(stay_stmt["test_expr"]):
                        # 循环执行包含该条stay的指令
                        self.jumpTo(self.IP - 1)
                        self.requireSleep(stay_stmt["time"])

    def _varInstruction(self):
        # 处理var
        if self.IR["del"]:
            self._locals.pop(self.IR["ID"])
        else:
            self._locals[self.IR["ID"]] = self._evaInContext(self.IR["value"])

    def _adbInstruction(self):
        cmd = self.IR["cmd"]
        # 执行cmd形如:["shell","input","keyevent","4"],并获得一个返回值
        popen = self.adb.command(cmd)
        popen.wait()
        _RET = popen.stdout.read()
        self._locals["_RET"] = _RET

        self._instructionUniverseBlock()

    def _ocrInstruction(self):
        screenshot = io.BytesIO(self.adb.get_shell_output(self.serial, "screencap", "-p"))
        x, y, w, h = self.IR["pos"]
        confidence = self.IR["confidence"]
        origin = self.IR["path"]
        _RET = compare_img(x, y, w, h, origin, screenshot, confidence)
        self._locals["_RET"] = _RET

        self._instructionUniverseBlock()

    def _sleepInstruction(self):
        self.requireSleep(self.IR["time"])

    def _logInstruction(self):
        self.logger.info(f"脚本执行器-{self.ID}: {self._evaInContext(self.IR['msg'])}")

    def _exitInstruction(self):
        raise StopInterruptions

    def _clickInstruction(self):
        x, y = self.IR["pos"]
        self.adb.shell("-s", self.serial, "input", "tap", x, y)
        self._locals["_RET"] = None

        self._instructionUniverseBlock()

    # =============== PRIVATE METHODS ===============

    # =============== PUBLIC METHODS ===============

    def run(self):

        self.Pause()
        self._interruptPeriod()

        try:
            self._initScript()
            self.logger.info(f"脚本执行器-{self.ID}: 脚本解析完成")
        except BaseException as e:
            self.interruption = e
        finally:
            self._interruptPeriod()

        # main
        while True:
            try:
                # atom operation
                self._fetchInstruction()
                self._executeInstruction()
            except BaseException as e:
                self.interruption = e
            finally:
                # if it needs a sleep
                if self.PSW.REQUIRE_SLEEP != -1:
                    # interrupt period
                    if not self._interruptPeriod():
                        break
                    # leave time to receive the external events and requests
                    self.msleep(int(self.PSW.REQUIRE_SLEEP * 1000))
                    self.PSW.REQUIRE_SLEEP = -1
                    # interrupt period
                    if not self._interruptPeriod():
                        break
                else:
                    # interrupt period
                    if not self._interruptPeriod():
                        break

        if self.IP == self.script.BeginAddress + self.script.Length:
            self.PSW.FINISHED = True
            self.PSW.PAUSED = False
            # send done signal
            self.logger.debug("完成")
            self.done.emit(self.ID)
        else:
            # send aborted signal
            self.logger.debug(f"停止")
            self.aborted.emit(self.ID)

    def requireSleep(self, s: float):
        self.PSW.REQUIRE_SLEEP = s

    def Pause(self):
        self.PSW.PAUSED = True

    def Resume(self):
        self.PSW.PAUSED = False

    def jumpTo(self, instructionPointer):
        self.IP = instructionPointer

    def safeJumpTo(self, instructionPointer):
        self.Pause()
        if instructionPointer in self.script:
            self.jumpTo(instructionPointer)
        self.Resume()

    # =============== PUBLIC METHODS ===============


class ScriptParseManager:
    """
    a class that manage the ScriptParse
    singleton
    """
    _CURRENT_ID = 0
    _MAX_INSTANCES = -1
    _instances: WeakValueDictionary[str, ScriptExecutor] = WeakValueDictionary()

    @classmethod
    def newInstance(cls, script: Script, instructionPointer=-1) -> Optional[int]:
        """
        create a new instance of ScriptParse
        """
        if cls._MAX_INSTANCES != -1 and len(cls._instances) >= cls._MAX_INSTANCES:
            return None
        ID = cls._CURRENT_ID
        cls._CURRENT_ID += 1
        _ = ScriptExecutor(script, ID, instructionPointer)
        _.start()
        cls._instances[str(ID)] = _
        del _
        return ID

    @classmethod
    def getInstance(cls, ID):
        """
        get the instance of ScriptParse by ID
        """
        return cls._instances.get(str(ID), None)
