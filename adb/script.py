script_dict = {
    1: {
        "name": "adb操作",
        "action": "adb",
        "args": ["shell", "getprop", "ro.product.model"],
        "condition": ["return", "Ok"]
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
    }
}


class Script:

    @staticmethod
    def checkJson(_json):
        """
        check if the json is valid:whether key is always int
        """
        return all([isinstance(key, int) for key in _json.keys()])

    def __init__(self, _json=None):
        # check script json is valid
        if self.checkJson(_json):
            self.script = _json
        else:
            raise Exception("Invalid script")

        # calculate the length of script,and the lowest instruction pointer
        self._length = len(self.script)
        self._beginAddress = min(self.script.keys())

    def __getitem__(self, key):
        return self.script.get(key, None)

    def __contains__(self, key):
        return key in self.script

    @property
    def Length(self):
        return self._length

    @property
    def BeginAddress(self):
        return self._beginAddress


script = Script(script_dict)
