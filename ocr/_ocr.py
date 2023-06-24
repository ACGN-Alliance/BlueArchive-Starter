"""
本软件包用于进行图像定位操作
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops

CONFIDENCE = 0.9  # 图像相似度阈值


def compare_img(
        x: float,
        y: float,
        width: float,
        height: float,
        origin_img: str | Path | BytesIO,
        similar_img: str | Path | BytesIO,
        confidence: float = CONFIDENCE,
        *args,
        **kwargs,
) -> bool:
    """
    比较两张图片是否相似


    :param x: 原始图片的x坐标
    :param y: 原始图片的y坐标
    :param width: 原始图片的宽度
    :param height: 原始图片的高度
    :param origin_img: 原始图片
    :param similar_img: 需要对比的图片
    :param confidence: 相似度阈值
    :return: 如果相似度大于阈值，则返回True，否则返回False
    """
    if confidence > 1 or confidence < 0:
        raise ValueError("置信度范围为 [0, 1]")

    im: Image.Image = Image.open(origin_img)
    if x + width > im.width or y + height > im.height:
        raise ImageSizeException("需定位的图像位置超出范围")
    im_s: Image.Image = Image.open(similar_img)
    if im_s.width != width or im_s.height != height:
        raise ImageSizeException("图片大小与需求不一致")
    im = im.convert("RGB")
    im_s = im_s.convert("RGB")
    im = im.crop((x, y, x + width, y + height))
    compare = ImageChops.difference(im, im_s)
    # 判断对比合成图有多少RGB(0, 0, 0)像素点
    # 如果有超过阈值的像素点，则认为两张图不相似
    colors = compare.getcolors(maxcolors=16384)
    all_count = len(im.getdata())
    white_count = 0
    for color in colors:
        if color[1] == (0, 0, 0):
            white_count += 1
    now_confidence = white_count / all_count
    if now_confidence > CONFIDENCE:
        return True
    else:
        return False


class ImageSizeException(BaseException):
    pass
