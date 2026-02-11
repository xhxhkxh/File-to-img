'''
/modules/enc.py

This sub module contains the core functions of encoding and decoding.
'''
from modules.custom import CUSTOM_FILENAME_BEGIN, CUSTOM_FILENAME_END, CUSTOM_FILESIZE_BEGIN, CUSTOM_FILESIZE_END, SUB_LOG_PREFIX
from modules.custom import getPrefix
from os import path
from math import sqrt, ceil
from PIL import Image
from modules.tool import b2mb, sep
import PIL
from alive_progress import alive_bar


print("[ENC] Loading module...")

print(f"[ENC] PIL version: {PIL.__version__}")
print("[ENC Loading tools...")

print("[ENC] Loading custom settings...")
print("[ENC] Module loaded.")


def encode(filePath: str) -> Image.Image:
    '''
    将文件编码为图像格式

    该函数将指定路径的文件转换为RGB图像，通过以下步骤实现：
    1. 读取文件的二进制数据
    2. 添加包含文件名和大小的自定义文件头
    3. 将字节数据按RGB三元组分组
    4. 计算合适的图像尺寸并创建正方形图像
    5. 将数据填充到图像像素中

    参数:
        filePath (str): 要编码的文件的完整路径

    返回:
        Image.Image: 包含编码文件数据的PIL图像对象
    '''
    print(f"{SUB_LOG_PREFIX} [ENC] Encoding file: {filePath}")

    # 读取文件的二进制数据
    with open(filePath, 'rb') as file:
        data = file.read()
    fn = path.basename(filePath)

    # 将数据转换为字节列表
    bytes = []
    for byte in data:
        bytes.append(byte)
    byte_size = len(bytes)

    print(f"{SUB_LOG_PREFIX} [ENC] Adding file header.")
    # 创建包含文件信息的头部
    file_head = str(f"{CUSTOM_FILENAME_BEGIN}{fn}{CUSTOM_FILENAME_END},{CUSTOM_FILESIZE_BEGIN}" +
                    str(byte_size) + f"{CUSTOM_FILESIZE_END}").encode("utf-8")

    file_head_l = []
    for b in file_head:
        file_head_l.append(b)

    # 确保文件头长度固定为512字节
    print(
        f"{SUB_LOG_PREFIX} [ENC]Current file head size is {len(file_head_l)}, would expand to 512 b")
    offset = 512 - len(file_head_l)
    if offset < 0:
        print(f"{SUB_LOG_PREFIX} [ENC-WARN]File head too long! Exiting!")
        exit(0)
    for i in range(offset):
        file_head_l.append(0)

    # 合并文件头和原始数据
    bytes = file_head_l + bytes

    re_bt_size = len(bytes)
    print(f"{getPrefix(2)} [ENC-SizeAnalyze]After this operation, the file size would expand from {byte_size} to {re_bt_size}, ({b2mb(re_bt_size)}) mb)" +
          f" expanded {((re_bt_size / byte_size) - 1) * 100} %")

    print(f"{getPrefix(2)} [ENC-INFO]Performing format...")
    # 将字节数据按RGB三元组分组
    rgb_spl = [bytes[i:i+3] for i in range(0, len(bytes), 3)]

    # 计算图像尺寸（正方形）
    imgsize = ceil(sqrt(len(rgb_spl)))

    print("{} [ENC-INFO]Original file size:{} b (Estimalte {} mb)\nImage output would be {}x{}".format(getPrefix(2),
                                                                                                       byte_size, byte_size / 1048576,  imgsize, imgsize))

    stack_size = imgsize*imgsize
    print("[ENC-SizeAnalyze]Performing square filling...")
    # 计算需要填充的数据量
    offset = stack_size - len(rgb_spl)
    print(
        f"{getPrefix(2)} [ENC-INFO]Offset: {offset}, after filling, additional {offset} would be append after the original file.")

    # 用零值填充至完整图像尺寸
    for i in range(offset):
        rgb_spl.append([0, 0, 0])

    print(f"{SUB_LOG_PREFIX} [ENC]Done.")

    print(f"{getPrefix(2)} [ENC-LC]Performing size check...")
    # 再次验证填充是否正确
    offset = stack_size - len(rgb_spl)
    print(f"{getPrefix(3)} [ENC-LC]Offset: {offset}, checking it twice...")
    if offset != 0:
        print(
            f"{getPrefix(3)} [ENC-WARN]Error occured when handleing offset process, exiting...")
        exit(1)
    print(f"{getPrefix(2)} [ENC-LC]Done.")

    # 创建新的RGB图像
    img = Image.new(mode="RGB", size=(imgsize, imgsize))

    write_count = 0

    # 将RGB数据写入图像像素
    for i in range(imgsize):
        for j in range(imgsize):
            img.putpixel((i, j), (sep(rgb_spl[write_count])))
            write_count += 1
    print(f"{getPrefix(2)} [ENC-LW]Done.")

    print(f"{SUB_LOG_PREFIX} [ENC-RiskControl]Performing offset check...")
    print(getPrefix(3), re_bt_size, write_count *
          3, re_bt_size - write_count*3, offset)

    print(f"{getPrefix(3)} [ENC-RiskControl] OK")

    print(f"{SUB_LOG_PREFIX} [ENC] Encoding completed.")
    return img


def decode(img: Image.Image) -> list[bytes]:
    '''
    从图像中解码提取原始文件数据

    该函数将编码后的图像解码回原始文件的字节数据。解码过程包括：
    1. 从图像像素中提取所有数据
    2. 解析文件头信息（文件名和大小）
    3. 提取实际的文件数据
    4. 验证数据完整性

    参数:
        img (Image.Image): 包含编码文件数据的PIL图像对象

    返回:
        list[bytes]: 解码后的文件字节数据列表

    异常:
        Exception: 当解码过程中文件大小不匹配时抛出
    '''
    print("[DEC] Decoding file...")
    data = []
    w, h = img.size
    # 提取图像中所有像素的RGB值
    for i in range(w):
        for j in range(h):
            data.append(img.getpixel((i, j)))
    unzip_data = []
    # 将嵌套的像素数据展平为一维列表
    for i in data:
        for j in i:
            unzip_data.append(j)
    print(f"{SUB_LOG_PREFIX}[DEC] Analyzing file header...")
    head = bytes(unzip_data[:500])
    head_str = head.decode("utf-8")
    # 解析文件头中的文件名信息
    fn = head_str.split(CUSTOM_FILENAME_BEGIN)[
        1].split(CUSTOM_FILENAME_END+",")[0]
    # 解析文件头中的文件大小信息
    size = head_str.split(CUSTOM_FILESIZE_BEGIN)[
        1].split(CUSTOM_FILESIZE_END)[0]
    print(f"{SUB_LOG_PREFIX}Filename: {fn}, Size: {size} b ({b2mb(int(size))} mb)")
    print(f"{SUB_LOG_PREFIX}[DEC] Extracting file data...")
    # 提取实际的文件数据（跳过前500字节的文件头）
    ext_data = unzip_data[500:500+int(size)]

    print(
        f"{SUB_LOG_PREFIX}[DEC] Readed {len(ext_data)} b, {b2mb(len(ext_data))} mb, checking it with file head...")
    # 验证提取的数据大小是否与文件头中声明的大小一致
    if len(ext_data) != int(size):
        print(f"{SUB_LOG_PREFIX}Error occured when handleing file data, exiting...")
        raise Exception("File Size Mismatch at Decoding process")
    print(f"{SUB_LOG_PREFIX}[DEC] Decoding completed.")
    return [i for i in ext_data]
