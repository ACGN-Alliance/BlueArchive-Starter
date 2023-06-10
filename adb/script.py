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
    }
}