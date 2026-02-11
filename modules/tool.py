'''
/modules/tool.py

This sub module contains some essential functions.
'''
from PIL import Image
import base64
import io


def b2mb(b):
    return b / 1048576


def sep(obj):
    try:
        s1 = obj[0]
    except:
        s1 = 0
    try:
        s2 = obj[1]
    except:
        s2 = 0
    try:
        s3 = obj[2]
    except:
        s3 = 0
    return (s1, s2, s3)


def pil_to_b64(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
