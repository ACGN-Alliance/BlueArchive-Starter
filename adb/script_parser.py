import json
import re
import warnings
from typing import List, Dict


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

        for p in self.nested:
            self._parser(p)

        for p in self.parsed:
            print(json.dumps(p, indent=4, sort_keys=True, ensure_ascii=False))

    def _nested(self):
        self.lineno = 0
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
                        "block": [],
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
                    self.nested[-1]["block"].append({
                        "type": stmt_type,
                        "raw": line.strip()
                    })
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

    def _exit_parser(self, stmt_info: Dict[str, str]):
        if stmt_info["block"]:
            raise Exception(f"语法错误:line={self.lineno}: {stmt_info['type']}:\n不应出现语句子块")
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
        return {"type": "log", "msg": " ".join(stmt_info["raw"].split(" ")[1:])}

    def _adb_parser(self, stmt_info: Dict[str, str | List]):
        parsed = {"type": "adb"}
        stmt = stmt_info["raw"]
        parsed["cmd"] = tuple(stmt.split(" ")[1:])
        parsed_block = self._block_parser(stmt_info["block"])
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
        parsed_block = self._block_parser(stmt_dict["block"])
        parsed["block"] = parsed_block
        return parsed

    def _block_parser(self, block: List[Dict[str, str]]):
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
                message=f"语法警告:line={self.lineno}: {stmt_info['type']}:\ncheck和stay同时出现，stay可能被忽略")
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
        else:
            parsed["check_mode"] = "hard"
            tokens.insert(0, token)

        python_expr = " ".join(tokens)
        python_expr = python_expr.replace("neq", "!=").replace("eq", "==").replace("nin", "not in")
        parsed["test_expr"] = python_expr
        return parsed

    def _stay_parser(self, stmt_info: Dict[str, str]):
        """
        stay (int|float)? until (_RET (n)eq <str> | _RET (n)in <List>) -> {
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
            raise Exception(f"语法错误:line={self.lineno}: {stmt_info['type']}:\nexcept 'until', got {token}")
        python_expr = " ".join(tokens)
        python_expr = python_expr.replace("eq", "==").replace("neq", "!=").replace("nin", "not in")
        parsed["test_expr"] = python_expr
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
                raise Exception(f"语法错误:line={self.lineno}: {stmt_info['type']}:\nexcept '=', got {token}")
            parsed["value"] = " ".join(tokens)
        return parsed


if __name__ == '__main__':
    parser = ScriptParser()
    parser.parse("../BASL/test.bas")
