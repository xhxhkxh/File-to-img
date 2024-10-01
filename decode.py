from PIL import Image
from math import sqrt, ceil
import struct

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
