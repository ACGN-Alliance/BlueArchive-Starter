import json
import re
import warnings
from typing import List, Dict


class CompiledExpr:
    def __init__(self, expr: str, lineno: int):
        self.expr = expr
        self.lineno = lineno

        self.compiled_expr = self._compile_python_expr(expr, lineno)

    @staticmethod
    def _compile_python_expr(expr: str, lineno: int):
        try:
            return compile(expr, "<string>", "eval")
        except Exception as e:
            raise Exception(f"语法错误:line={lineno}: 表达式编译错误:{expr}\n{e}")

    def __str__(self):
        return f"<CompiledExpr: expr={self.expr} , lineno={self.lineno}>"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.expr == other.expr and self.lineno == other.lineno

    def __hash__(self):
        return hash((self.expr, self.lineno))


class ScriptTreeJsonEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, CompiledExpr):
            return str(o)
        return super().default(o)


class ScriptParser:
    EOF = "$"

    def __init__(self):
        self.lineno = 1
        self.lines: List[str] = []
        self.nested = []
        self.parsed = []

    def parse(self, scriptFile: str):
        with open(scriptFile, "r", encoding="utf-8") as f:
            self.lines = f.readlines()

        self.lines.append(self.EOF)
        self.lines.insert(0, "^")
        # nested
        self._nested()

        for p in self.nested:
            self._parser(p)

        for p in self.parsed:
            print(json.dumps(p, indent=4, sort_keys=True, ensure_ascii=False, cls=ScriptTreeJsonEncoder))

    def _nested(self):
        self.lineno = 1
        last_stmt = None
        while self.lineno < len(self.lines):
            line = self.lines[self.lineno]

            if line.strip() == "" or line.startswith("#"):
                # ignore empty line and comment line
                continue

            if not line.startswith('\t') and not line.startswith("    "):
                stmt_type = line.split(' ')[0]

                if stmt_type in ('adb', 'ocr', 'exit', 'click', 'sleep', 'log'):
                    last_stmt = line
                    stmt_type = line.split(' ')[0]
                    raw = line.strip()
                    if raw.endswith(":"):
                        raw = raw[:-1]
                    self.nested.append({
                        "raw": raw,
                        "type": stmt_type,
                        "lineno": self.lineno,
                        "block": []
                    })
                    self.lineno += 1
                elif line == "$":
                    break
                else:
                    raise Exception(f"语法错误:line={self.lineno}: {stmt_type}:\n未知的语句")

            else:
                line = line.strip()
                stmt_type = line.split(' ')[0]
                if stmt_type in ('check', 'stay', 'arg'):
                    try:
                        self.nested[-1]["block"].append({
                            "type": stmt_type,
                            "raw": line.strip(),
                            "lineno": self.lineno
                        })
                    except IndexError:
                        raise Exception(f"语法错误:line={self.lineno}: {stmt_type}:\n文件开头不应出现子句")
                    self.lineno += 1
                else:
                    raise Exception(f"语法错误:line={self.lineno}: {stmt_type}:\n未知的子句")

    def _parser(self, stmt_info: dict):
        match stmt_info['type']:
            case 'adb':
                self.parsed.append(self._adb_parser(stmt_info))
            case 'ocr':
                self.parsed.append(self._ocr_parser(stmt_info))
            case 'exit':
                self.parsed.append(self._exit_parser(stmt_info))
            case 'click':
                self.parsed.append(self._click_parser(stmt_info))
            case 'sleep':
                self.parsed.append(self._sleep_parser(stmt_info))
            case 'log':
                self.parsed.append(self._log_parser(stmt_info))
        self.lineno += 1

    def _exit_parser(self, stmt_info: Dict[str, str]):
        if stmt_info["block"]:
            raise Exception(f"语法错误:line={stmt_info['lineno']}: {stmt_info['type']}:\n不应出现语句子块")
        return {"type": "exit"}

    def _click_parser(self, stmt_info: Dict[str, str]):
        """
        click SPACE? x:int SPACE? , SPACE? y:int SPACE?
        提取x,y
        {"type": "click", "pos": (x, y)}
        """
        parsed = {"type": "click"}
        stmt = stmt_info["raw"]
        x, y = re.findall(r"^click\s+(\d+)\s*,\s*(\d+)$", stmt)[0]
        parsed["pos"] = (int(x), int(y))
        return parsed

    def _sleep_parser(self, stmt_info: Dict[str, str]):
        """
        sleep <float> | <int>
        {"type": "sleep", "time": float}
        """
        return {"type": "sleep", "time": float(stmt_info["raw"].split(" ")[1])}

    def _log_parser(self, stmt_info: Dict[str, str]):
        """
        log <str>
        {"type": "log", "msg": str}
        """
        python_expr = " ".join(stmt_info["raw"].split(" ")[1:])
        return {"type": "log", "msg": CompiledExpr(python_expr, int(stmt_info["lineno"]))}

    def _adb_parser(self, stmt_info: Dict[str, str | List]):
        parsed = {"type": "adb"}
        stmt = stmt_info["raw"]
        parsed["cmd"] = tuple(stmt.split(" ")[1:])
        parsed_block = self._block_parser(stmt_info, stmt_info["block"])
        parsed["block"] = parsed_block
        return parsed

    def _ocr_parser(self, stmt_dict: Dict[str, str | List]):
        """
        ocr x:<int>,y:<int>,w:<int>,h:<int> 'path/to/image':<str>
        提取出x,y,w,h,path
        """
        parsed = {"type": "ocr"}
        stmt = stmt_dict["raw"]
        x, y, w, h, path = re.findall(r"ocr\s+(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\"(.+)\"", stmt)[0]
        parsed["pos"] = (int(x), int(y), int(w), int(h))
        parsed["path"] = path
        parsed_block = self._block_parser(stmt_dict, stmt_dict["block"])
        parsed["block"] = parsed_block
        return parsed

    def _block_parser(self, super_stmt_info, block: List[Dict[str, str]]):
        """
        check,stay,arg,arg del
        [{
            "type": "check",
            "raw": "check (hard | soft) (_RET (n)eq <str> | _RET (n)in <List>)"
        }]
        """
        parsed_block = {}
        stmt_types = set()
        for stmt_info in block:
            stmt_type = stmt_info["type"]
            if stmt_type not in stmt_types:
                parsed_block[stmt_type] = []
            stmt_types.add(stmt_type)
            parsed = getattr(self, f"_{stmt_type}_parser")(stmt_info)
            parsed_block[stmt_type].append(parsed)

        if "check" in stmt_types and "stay" in stmt_types:
            warnings.warn(
                message=f"语法警告:line={super_stmt_info['lineno']}: 子句块中check和stay同时出现，stay可能被忽略")
        return parsed_block

    def _check_parser(self, stmt_info: Dict[str, str]):
        """
        check (hard | soft)? (_RET (n)eq <str> | _RET (n)in <List>) -> {
            "check_mode": "hard",
            "test_expr: <python expr>,
        }
        """
        parsed = {}
        tokens = stmt_info["raw"].split(" ")[1:]
        if (token := tokens.pop(0)) in ("hard", "soft"):
            parsed["check_mode"] = token
        elif self._is_ID(token):
            parsed["check_mode"] = "hard"
            tokens.insert(0, token)
        else:
            raise Exception(
                f"语法错误:line={stmt_info['lineno']}: {stmt_info['type']}:\nstatement check excepts hard | soft,got {token}")

        python_expr = " ".join(tokens)
        python_expr = python_expr.replace("neq", "!=").replace("eq", "==").replace("nin", "not in")
        parsed["test_expr"] = CompiledExpr(python_expr, int(stmt_info["lineno"]))
        return parsed

    def _stay_parser(self, stmt_info: Dict[str, str]):
        """
        stay (int|float)? until (_RET (n)eq <str> | _RET (n)in <List>)
        until 后面的表达式可以省略，省略后默认为 _RET == True
        -> {
            "test_expr: <python expr>,
        }
        """
        parsed = {}
        tokens = stmt_info["raw"].split(" ")[1:]

        token = tokens.pop(0)

        # 如果token是一个整数或者浮点数，那么就是stay的时间提取时间
        if re.match(r"^\d+(\.\d+)?$", token):
            parsed["time"] = float(token)
        else:
            tokens.insert(0, token)
            parsed["time"] = 1.0

        if not (token := tokens.pop(0)) == "until":
            raise Exception(f"语法错误:line={stmt_info['lineno']}: {stmt_info['type']}:\nexcept 'until', got {token}")
        python_expr = " ".join(tokens)
        if not python_expr:
            python_expr = "_RET"
        python_expr = python_expr.replace("eq", "==").replace("neq", "!=").replace("nin", "not in")
        parsed["test_expr"] = CompiledExpr(python_expr, int(stmt_info["lineno"]))
        return parsed

    def _arg_parser(self, stmt_info: Dict[str, str]):
        """
        arg <ID> = _RET | <str> | <int> | <float>
        arg del <ID>
        """
        parsed = {}
        tokens = stmt_info["raw"].split(" ")[1:]
        if (token := tokens.pop(0)) == "del":
            parsed["del"] = True
            parsed["ID"] = tokens.pop(0)
            parsed["value"] = ""
        else:
            parsed["del"] = False
            parsed["ID"] = token
            if (token := tokens.pop(0)) != "=":
                raise Exception(f"语法错误:line={stmt_info['lineno']}: {stmt_info['type']}:\nexcept '=', got {token}")
            parsed["value"] = " ".join(tokens)
        return parsed

    @staticmethod
    def _is_ID(token: str):
        return re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", token) is not None


if __name__ == '__main__':
    parser = ScriptParser()
    parser.parse("../BASL/test.bas")
