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

    @staticmethod
    def device_on() -> bool:
        if not (rv := Adb.have_device()):
            print("No device found, sp exiting...")
            return rv
        return True

    def __init__(self, script: Script, ID=0, instructionPointer=-1):
        super().__init__()
        # thread ID
        self.ID = ID
        # a pointer that point to the next instruction, VISIBLE to the user
        self.IP = max(script.BeginAddress, instructionPointer)
        # a Register that save the current instruction, INVISIBLE to the user
        self.IR = None
        # a Register that save the current script
        self.script = script
        # a Register that save the current state of ScriptParse,VISIBLE to the user
        self.PSW = ScriptParsePSW()

    # =============== PRIVATE METHODS ===============

    def _fetchInstruction(self) -> bool:
        """
        fetch the next instruction
        return False if it needs to stop
        """
        self.IR = self.script[self.IP]
        self.IP += 1

        if self.IR is None:
            return False
        else:
            return True

    def _executeInstruction(self) -> bool:
        """
        execute the current instruction
        return False if it needs to stop
        """
        # simulate executing...
        self.msleep(1000)
        print("executed:", self.IR)
        self.instructionExecuted.emit(self.ID)
        return True

    def _interruptPeriod(self) -> bool:
        """
        interrupt period:
        followed the fetchInstruction and the executeInstruction period,
        there is a period that can check state and be allowed to process and answer the external events and requests
        return False if it needs to stop
        """
        # check state
        if not self.device_on():
            return False

        if self.PSW.PAUSED:
            self._onPaused()

            while self.PSW.PAUSED:
                self.msleep(100)
                if not self.device_on():
                    return False

            self._onResumed()

        self.interrupt.emit(self.ID)
        return True
        # check state

    def _onPaused(self):
        """
        issued when needed a pause,box the pause event
        """
        self.PSW.PAUSED = True
        self.paused.emit()
        print("paused")

    def _onResumed(self):
        """
        issued when needed a resume,box the resume event
        """
        self.PSW.PAUSED = False
        self.resumed.emit()
        print("resumed")

    # =============== PRIVATE METHODS ===============

    # =============== PUBLIC METHODS ===============

    def run(self):

        self.Pause()
        if not self._interruptPeriod():
            return

        # main
        while True:
            if not self._fetchInstruction():
                break

            if not self._executeInstruction():
                break

            if not self._interruptPeriod():
                break

        if self.IP == self.script.BeginAddress + self.script.Length:
            self.PSW.FINISHED = True
            self.PSW.PAUSED = False
        print("finished")

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
