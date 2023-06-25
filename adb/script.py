from adb.script_parser import ScriptParser


class Script:

    def __init__(self, file, interval=-1):
        parser = ScriptParser(interval)
        self.script = parser.parse(file)

        # calculate the length of script,and the lowest instruction pointer
        self._length = len(self.script)
        self._beginAddress = 0

    def __getitem__(self, key):
        return self.script[key]

    def __contains__(self, key):
        return key in self.script

    @property
    def Length(self):
        return self._length

    @property
    def BeginAddress(self):
        return self._beginAddress


script_dict = {
    1: {
        "name": "adb操作",
        "action": "adb",
        "args": ["shell", "getprop", "ro.product.model"],
        "extra": [("return", "Ok")]
    },
    2: {
        "name": "图片识别",
        "action": "ocr",
        "pos_and_size": [20, 20, 40, 40],
        "similar_image": "path/to/image"
    },
    3: {
        "name": "图片识别",
        "action": "ocr",
        "pos_and_size": [20, 20, 40, 40],
        "similar_image": "path/to/image"
    },
    4: {
        "name": "图片识别",
        "action": "ocr",
        "pos_and_size": [20, 20, 40, 40],
        "similar_image": "path/to/image"
    },
    5: {
        "name": "图片识别",
        "action": "ocr",
        "pos_and_size": [20, 20, 40, 40],
        "similar_image": "path/to/image"
    },
    6: {
        "name": "终止",
        "action": "exit"
    }
}
