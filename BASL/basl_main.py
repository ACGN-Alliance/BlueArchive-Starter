from typing import List
import re

program = """
fn func1(a,b):
    c = a + b
    d = a == b
    adb shell xxx
    return c
debug "1"
debug "2"
if func1(1,2) == 3:
    i=0
    while i < 3:
        debug "test{i}"
        i = i + 1
elif func1(1,2) == 4:
    debug "4"
else:
    debug "6"
adb shell xxx
debug "finished"
"""


class Parser:

    def __init__(self):
        self.raw = None
        self.nested = []

    def feed(self, program: List[str]):
        """
        解析程序
        :param program:
        :return:
        """
        self.raw = program
        self.nested = self.nested_parse(program, 0, 0)

    # TODO
    def nested_parse(self, program, lineno, indent):
        """
        将程序解析为嵌套结构
        先全部扫描一遍，并不解析语句本身，而是将:后的语句作为Block,挂载到上一行的语句上

        :param program:
        :return:
        """
        while lineno < len(program) and (line := program[lineno]).startswith("\t" * indent):
            if line.endswith(":"):
                # block
                self.nested.append({
                    line: self.nested_parse(program, lineno + 1)
                })
            else:
                # statement
                pass
            lineno += 1


class Lexer:
    """
    词法分析器
    分析
    """