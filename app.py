from PIL import Image
from math import sqrt, ceil
from struct import pack
from os import path
import sys


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


def encode(fnp):
    fn = input("File name and it's path:")

    with open(fn, 'rb') as file:
        data = file.read()

    fn = path.basename(fn)

    bytes = []

    for byte in data:
        bytes.append(byte)
    # print(rgb_spl)

    byte_size = len(bytes)
    print("Adding file head, the size of the head depends the filename and it's own size.")
    file_head = str(f"Filename_beg:{fn}Filename_end,siZe:" +
                    str(byte_size) + "size_end").encode("utf-8")

    file_head_l = []
    for b in file_head:
        file_head_l.append(b)

    print(f"Current file head size is {
          len(file_head_l)}, would expand to 500 b")
    offset = 500 - len(file_head_l)
    if offset < 0:
        print("File head too long! Exiting!")
        exit(0)
    for i in range(offset):
        file_head_l.append(0)

    bytes = file_head_l + bytes

    re_bt_size = len(bytes)
    print(f"After this operation, the file size would expand from {byte_size} to {re_bt_size}, ({b2mb(re_bt_size)}) mb)" +
          f" expanded {((re_bt_size / byte_size) - 1) * 100} %")

    print("Performing format...")
    rgb_spl = [bytes[i:i+3] for i in range(0, len(bytes), 3)]

    imgsize = ceil(sqrt(len(rgb_spl)))

    print("Original file size:{} b (Estimalte {} mb)\nImage output would be {}x{}".format(
        byte_size, byte_size / 1048576,  imgsize, imgsize))

    stack_size = imgsize*imgsize
    print("Performing list checksum...")
    offset = stack_size - len(rgb_spl)
    print(f"Offset: {offset}, after checksum, additional {
          offset} null object would be append after the original file.")

    for i in range(offset):
        rgb_spl.append([0, 0, 0])

    print("Done.")

    print("Performing list checksum...")
    offset = stack_size - len(rgb_spl)
    print(f"Offset: {offset}, checking it twice...")
    if offset != 0:
        print("Error occured when handleing offset process, exiting...")
    print("Done.")

    img = Image.new(mode="RGB", size=(imgsize, imgsize))

    write_count = 0

    for i in range(imgsize):
        for j in range(imgsize):
            img.putpixel((i, j), (sep(rgb_spl[write_count])))
            write_count += 1

    print("Performing complextiy check...")
    print(re_bt_size, write_count * 3, re_bt_size - write_count*3)

    img.save("./res.png")


def decode():
    img = Image.open(r"res.png")
    data = []
    w, h = img.size
    for i in range(w):
        for j in range(h):
            data.append(img.getpixel((i, j)))

    data_unzip = []

    for i in data:
        for j in i:
            data_unzip.append(j.to_bytes())

    # print(data_unzip[:300])
    header = ''
    print("Reading file header...")
    for x in data_unzip[:500]:
        try:
            header += x.decode('utf-8')
        except:
            header += 'e'
    # print(header)

    custom_fn_begin = "Filename_beg:"
    custom_fn_end = "Filename_end"

    custom_size_begin = ",siZe:"
    custom_size_end = "size_end"
    print()
    file_name = header[header.index(
        custom_fn_begin) + len(custom_fn_begin):header.index(custom_fn_end)]
    print(file_name)
    file_size = header[header.index(
        custom_size_begin)+len(custom_size_begin):header.index(custom_size_end)]
    print(file_size)

    datas = data_unzip[500:500+int(file_size)]

    def b2mb(b):
        return b / 1048576

    print(f"Readed {len(datas)} bytes, {b2mb(len(datas))} mb")
    print(f"It should be {file_size}, plese check.")

    # print(datas[:30])

    with open(f"{file_name}", 'wb') as file:
        for i in datas:
            file.write(i)


usage = r'''
 __   ___            _       _     
 \ \ / / |          | |     | |    
  \ V /| |_ ___  ___| | __ _| |__  
   > < | __/ _ \/ __| |/ _` | '_ \ 
  / . \| ||  __/ (__| | (_| | |_) |
 /_/ \_\\__\___|\___|_|\__,_|_.__/ 
                                  
FIMG v1
File to Img decode and encode tool for cmd.

Usage:
python ./app.py [option] [file]

option:
-d : decode mode, doesn't need file argument (read res.png)
-e: encode mode, type with the file path below the -e argument

'''

mode = sys.argv[1]

try:
    if mode == '-d':
        decode()
    elif mode == '-e':
        encode(sys.argv[2])
except:
    print(usage)
