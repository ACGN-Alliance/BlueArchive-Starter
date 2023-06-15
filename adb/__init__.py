import weakref
from typing import Optional
from weakref import WeakValueDictionary

from .Interruptions import StopInterruptions
from .adb_utils import Adb
from .script import script_dict, Script
from log import LoggerDisplay

from PyQt6.QtCore import QThread, pyqtSignal


def _have_device():
    return len(Adb.get_device_list()) != 0


class ScriptParsePSW:
    """
    a class that record the state of ScriptParse(程序状态字寄存器)
    """

    def __init__(self):
        self.PAUSED = False
        self.FINISHED = False


class ScriptParseThread(QThread):
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
        self.PSW = ScriptParsePSW()
        # logger
        self.logger = logger
        # device serial
        self.serial = serial
        # adb
        self.adb = adb

        self.Exception = None

    def _parser(self, script: dict):
        """
        脚本解析
        :param script:
        :return:
        """
        name = script.get("name", None)
        action = script.get("action", None)
        args = {k: v for k, v in script.items() if k not in ("name", "action")}

        if action == "exit":
            return -1
        elif action == "adb":
            out = self.adb.get_command_output(args["args"])
        elif action == "ocr":
            out = 0
        else:
            self.logger.error(f"未知的action:{action}")
            return -1

        cond = script.get("extra")
        if not cond:
            return -1
        else:
            for operation in cond:
                if operation[0] == "return":
                    if out == operation[1]:
                        return 0
                    else:
                        return -1
                else:
                    self.logger.error(f"未知的操作:{operation[0]}")
                    return -1

    # =============== PRIVATE METHODS ===============

    def _fetchInstruction(self):
        """
        fetch the next instruction
        """
        self.IR = self.script[self.IP]
        self.IP += 1

        if self.IR is None:
            raise StopInterruptions

    def _executeInstruction(self):
        """
        execute the current instruction
        """
        # simulate executing...
        self.logger.info(f"正在执行:{self.IR}")
        ret = self._parser(self.IR)
        # TODO ret=-1时结束
        self.instructionExecuted.emit(self.ID)
        return True

    def _interruptPeriod(self):
        """
        interrupt period:
        followed the fetchInstruction and the executeInstruction period,
        there is a period that can check state and be allowed to process and answer the external events and requests
        """

        # check state
        if not self.device_on():
            self.Exception = StopInterruptions()

        if self.PSW.PAUSED:
            self._onPaused()

            while self.PSW.PAUSED:
                self.msleep(100)
                if not self.device_on():
                    self.Exception = StopInterruptions()
                    break

            self._onResumed()

        self.interrupt.emit(self.ID)

        # process exceptions
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
                self.msleep(1000)
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
            self.logger.debug("停止")
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


class ScriptParseManager:
    """
    a class that manage the ScriptParse
    singleton
    """
    _CURRENT_ID = 0
    _MAX_INSTANCES = -1

    _instances = WeakValueDictionary()

    @classmethod
    def newInstance(cls, script: Script, instructionPointer=-1) -> Optional[int]:
        """
        create a new instance of ScriptParse
        """
        if cls._MAX_INSTANCES != -1 and len(cls._instances) >= cls._MAX_INSTANCES:
            return None
        ID = cls._CURRENT_ID
        cls._CURRENT_ID += 1
        cls._instances[str(ID)] = ScriptParse(script, ID, instructionPointer)
        return ID

    @classmethod
    def getInstance(cls, ID):
        """
        get the instance of ScriptParse by ID
        """
        return cls._instances.get(ID, None)



