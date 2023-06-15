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


class ScriptParse(QThread):
    paused = pyqtSignal()
    resumed = pyqtSignal()

    # not implemented,emit ID of the sp, so that the main thread can know which sp is during interrupt period
    interrupt = pyqtSignal(int)
    instructionExecuted = pyqtSignal(int)

    done = pyqtSignal(int)
    aborted = pyqtSignal(int)

    @staticmethod
    def device_on() -> bool:
        if not (rv := Adb.have_device()):
            return False
        return True

    def __init__(self, script: Script, id_=0, instruction_pointer=-1, *args, logger: LoggerDisplay = None):
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

        self.Exception = None

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
            self.logger.debug("终止")
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
