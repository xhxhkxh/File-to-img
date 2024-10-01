from PIL import Image
from math import sqrt, ceil
from struct import pack
from os import path


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

print(f"Current file head size is {len(file_head_l)}, would expand to 500 b")
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
