import re
from typing import Optional, List
from weakref import WeakValueDictionary

from .Interruptions import StopInterruptions
from .adb_utils import Adb
from .script import script_dict, Script
from log import LoggerDisplay

from PyQt6.QtCore import QThread, pyqtSignal


class ScriptExecutorPSW:
    """
    a class that record the state of ScriptParse(程序状态字寄存器)
    """

    def __init__(self):
        self.PAUSED = False
        self.FINISHED = False
        self.ENABLE_INTERRUPT = True


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
                 script: Script,
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
        # a pointer that point to the next instruction, VISIBLE to the user
        self.IP = max(script.BeginAddress, instruction_pointer)
        # a Register that save the current instruction, INVISIBLE to the user
        self.IR = None
        # a Register that save the current script
        self.script = script
        # a Register that save the current state of ScriptParse,VISIBLE to the user
        self.PSW = ScriptExecutorPSW()
        # logger
        self.logger = logger
        # device serial
        self.serial = serial
        # adb
        self.adb = adb

        self.Exception = None

    # =============== PRIVATE METHODS ===============

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
        self.logger.info(f"正在执行:{self.IR}")
        ret = self._parser(self.IR)
        # TODO ret = -1时结束
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
            self.Exception = StopInterruptions()

        self.interrupt.emit(self.ID)

        # process exceptions,
        match self.Exception:
            case StopInterruptions():
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

    # =============== PRIVATE METHODS ===============

    # =============== PUBLIC METHODS ===============

    def run(self):

        self.Pause()
        try:
            self._interruptPeriod()
        except StopInterruptions:
            return

        # main
        while True:
            try:
                # atom operation
                self._fetchInstruction()
                self._executeInstruction()
            except BaseException as e:
                self.Exception = e
            finally:
                # interrupt period
                if not self._interruptPeriod():
                    break
                # leave time to receive the external events and requests
                self.msleep(500)
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


class ScriptParser:
    EOF = "$"

    def __init__(self):
        self.lines: List[str] = []
        self.nested = []
        self.parsed = []

    def parse(self, scriptFile: str):
        with open(scriptFile, "r", encoding="utf-8") as f:
            self.lines = f.readlines()

        self.lines.append(self.EOF)
        # nested
        self._nested()

    def _nested(self):
        self.lineno = 0
        last_stmt = None
        while self.lineno < len(self.lines):
            line = self.lines[self.lineno]

            if line.strip() == "" or line.startswith("#"):
                # ignore empty line and comment line
                continue

            if not line.startswith("\t"):
                stmt_type = line.split(' ')[0]

                if stmt_type in ('adb', 'ocr', 'exit', 'click', 'sleep', 'log'):
                    last_stmt = line
                    stmt_type = line.split(' ')[0]
                    self.nested.append({
                        "raw": line.strip(),
                        "type": stmt_type,
                        "block": [],
                    })
                    self.lineno += 1

                else:
                    raise Exception(f"语法错误:line={self.lineno}: {stmt_type}:\n未知的语句")

            else:
                line = line.strip("\t")
                stmt_type = line.split(' ')[0]
                if stmt_type in ('check', 'stay', 'arg'):
                    self.nested[last_stmt]["block"].append({
                        "type": stmt_type,
                        "raw": line.strip()
                    })
                    self.lineno += 1
                else:
                    raise Exception(f"语法错误:line={self.lineno}: {stmt_type}:\n未知的子句")

    def _parser(self, stmt_info: dict):
        match stmt_info['type']:
            case 'adb':
                self._adb_parser(stmt_info)
            case 'ocr':
                self._ocr_parser(stmt_info)
            case 'exit':
                self._exit_parser(stmt_info)
            case 'click':
                self._click_parser(stmt_info)
            case 'sleep':
                self._sleep_parser(stmt_info)
            case 'log':
                self._log_parser(stmt_info)

    def _block_parser(self, block: List[str]):
        # TODO

        """
        check,stay,arg,arg del
        """
        for stmt in block:
            stmt = stmt.strip()

        pass

    def _exit_parser(self, stmt_info: dict):
        pass

    def _click_parser(self, stmt_info: dict):
        pass

    def _sleep_parser(self, stmt_info: dict):
        pass

    def _log_parser(self, stmt_info: dict):
        pass

    def _adb_parser(self, stmt_info: dict):
        stmt = stmt_info["raw"]
        if stmt.endswith(":\n"):
            stmt = stmt[:-2].strip()
            # TODO stmt_info['block']的处理
        elif stmt.endswith("\n"):
            stmt = stmt[:-1].strip()
        elif self.lineno == len(self.lines) - 2:
            stmt = stmt.strip()
            if stmt_info["block"]:
                raise Exception(f"语法错误:line={self.lineno}: {stmt_info['type']}:\n语句块应为空")

    def _ocr_parser(self, stmt_dict: dict):
        """
        ocr x:<int>,y:<int>,w:<int>,h:<int> 'path/to/image':<str>
        提取出x,y,w,h,path
        """
        stmt = stmt_dict["raw"]
        x, y, w, h, path = re.findall(r"ocr\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\'(.+)\'", stmt)[0]


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
