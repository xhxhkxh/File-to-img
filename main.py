import flet as ft
from PIL import Image
from math import sqrt, ceil
from struct import pack
from os import path
import sys
import io
import base64

restore_manual_cancel = False
restore_file_name = None


def pil_to_b64(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def decode(page, fp):
    global restore_file_name
    img = Image.open(fp)
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

    restore_file_name = file_name

    datas = data_unzip[500:500+int(file_size)]

    def b2mb(b):
        return b / 1048576

    print(f"Readed {len(datas)} bytes, {b2mb(len(datas))} mb")
    print(f"It should be {file_size}, plese check.")

    show_confirm_dialog(page, file_size, len(datas))

    return datas


def pil2ft(image):
    img_byte_arr = image.tobytes()
    print(
        f"Image byte array size: {len(img_byte_arr)},Preview(first 500 bytes): {img_byte_arr[:500]}")
    print("Done, returning image...")
    return ft.Image(
        src_base64=img_byte_arr,
        width=image.width,
        height=image.height,
    )


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
    print("Received encode request for file:", fnp)
    fn = fnp

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

    return pil_to_b64(img)


def b2mb(b):
    return b / 1048576


def manual_result(page, state):
    global restore_manual_cancel
    restore_manual_cancel = state
    page.close(page.dialog)


def show_confirm_dialog(page, size, res_size):
    global restore_manual_cancel
    dig = ft.AlertDialog(
        modal=True,
        title=ft.Text("File Restore Complexity Check"),
        content=ft.Text(
            f"The file size is {size}, the restored file size would be {res_size}, please check.\nAre the the SAME?\nIf not, the decoded file is corrupted."),
        actions=[
            ft.ElevatedButton(
                "I see.", on_click=lambda _: manual_result(page, False)),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )
    page.dialog = dig
    page.open(dig)
    page.dialog.open = True
    page.update()


def show_invalid_alert(page: ft.Page):
    page.snack_bar = ft.SnackBar(
        content=ft.Text("文件选择无效", color=ft.Colors.WHITE),
        bgcolor=ft.Colors.RED_400,
        duration=2000   # 2 秒后自动消失
    )
    page.snack_bar.open = True
    page.update()


def main(page: ft.Page):
    page.title = "FTI - Encoder/Decoder"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Variables Declaration
    global_file = None
    ongoing_Type = None
    pil_encoded = None

    # Functions

    def on_file_picked(e: ft.FilePickerResultEvent):
        print("File Picked:", e.files)
        global ongoing_Type, global_file
        if e.files and ongoing_Type == "encode":
            global_file = e.files[0]
            efn_text.value = "File Name: " + global_file.name
            efs_text.value = "File Size: " + \
                str(b2mb(global_file.size)) + \
                f" MB - ({str(global_file.size)}) bytes"
            page.update()
        elif e.files and ongoing_Type == "decode":
            global_file = e.files[0]
            dfn_text.value = "File Name: " + global_file.name
            dfs_text.value = "File Size: " + \
                str(b2mb(global_file.size)) + \
                f" MB - ({str(global_file.size)}) bytes"
            page.update()
        else:
            print("No file selected")
            show_invalid_alert(page)

    file_picker = ft.FilePicker(
        on_result=lambda e: on_file_picked(e))
    sav_picker = ft.FilePicker()

    def encode_btn_click(e):
        global ongoing_Type
        ongoing_Type = "encode"
        file_picker.pick_files()

    def decode_btn_click(e):
        global ongoing_Type
        ongoing_Type = "decode"
        file_picker.pick_files()

    def in_page_encode(e):
        global global_file, pil_encoded
        print("Starting encode sequence...")
        print(f"With arguments: {global_file}")
        if global_file is None:
            show_invalid_alert(page)
            return
        pil_encoded = encode(global_file.path)
        dres_img.src_base64 = pil_encoded
        page.update()

    def save_btn_click(_):
        global pil_encoded
        if pil_encoded is None:
            page.snack_bar = ft.SnackBar(ft.Text("还没有可保存的图片！"))
            page.snack_bar.open = True
            page.update()
            return
        save_image(pil_encoded)

    def save_image(img):
        def on_result(e: ft.FilePickerResultEvent):
            # Process to PIL Image
            if e.path:
                path = e.path if e.path.lower().endswith(
                    (".png", ".jpg", ".jpeg")) else e.path + ".png"
                Image.open(io.BytesIO(base64.b64decode(img))
                           ).save(path, format="PNG")
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        "Image saved as " + path, color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.GREEN_400,
                    duration=2000   # 2 秒后自动消失
                )
                page.snack_bar.open = True
                page.update()
        sav_picker.on_result = on_result
        sav_picker.save_file(allowed_extensions=[
                             "png"], file_name="encoded_image.png")

    def decode_complexity_check(e):
        global global_file
        if global_file is None:
            show_invalid_alert(page)
            return
        # Try to read first 500 bytes
        img = Image.open(global_file.path)
        w, h = img.size
        c = 0
        data = []
        data_unzip = []
        for i in range(w):
            for j in range(h):
                data.append(img.getpixel((i, j)))
                c += 1
                if c > 500:
                    break
            if c > 500:
                break
        data_unzip = []
        for i in data:
            for j in i:
                data_unzip.append(j.to_bytes())

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
        try:
            file_name = header[header.index(
                custom_fn_begin) + len(custom_fn_begin):header.index(custom_fn_end)]
            print(file_name)
            file_size = header[header.index(
                custom_size_begin)+len(custom_size_begin):header.index(custom_size_end)]
            print(file_size)

            dfn_complex_check.value = "Complexity check: [✔] Valid"
            dfn_complex_check_fs.value = "Oriiginal file Size: " + file_size + " bytes"
            dfn_complex_check_fn.value = "Original file Name: " + file_name
        except Exception as ex:
            dfn_complex_check.value = "Complexity check: [❌] Invalid"
            dfn_complex_check_fn.value = "Original file name: -"
            dfn_complex_check_fs.value = "Oriiginal file Size: -"
            print(ex)
        page.update()

    def in_page_decode(e):
        global global_file, restore_manual_cancel, restore_file_name
        print("Entering decode sequence...")
        datas = decode(page, global_file.path)
        if restore_manual_cancel:
            print("User cancelled the restore process.")
            page.snack_bar = ft.SnackBar(
                content=ft.Text("用户取消了还原过程", color=ft.Colors.WHITE),
                bgcolor=ft.Colors.RED_400,
                duration=2000   # 2 秒后自动消失
            )
            page.snack_bar.open = True
            page.update()
            return
        else:
            restore_manual_cancel = False

            # Save file dialog
            def on_result(e: ft.FilePickerResultEvent):
                if e.path:
                    path = e.path
                    with open(path, 'wb') as file:
                        for i in datas:
                            file.write(i)
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text("File restored as " + path,
                                        color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_400,
                        duration=2000   # 2 秒后自动消失
                    )
                    page.snack_bar.open = True
                    page.update()
            sav_picker.on_result = on_result
            sav_picker.save_file(
                file_name=restore_file_name if restore_file_name else "restored_file", allowed_extensions=None)

    # UI

    # Encode section UI
    efs_text = ft.Text("File Size: -")
    efn_text = ft.Text("File Name: -")
    dres_img = ft.Image()

    # Decode section UI
    dfs_text = ft.Text("File Size: -")
    dfn_text = ft.Text("File Name: -")

    dfn_complex_check = ft.Text("Complexity check: -")
    dfn_complex_check_fn = ft.Text("Original file name: -")
    dfn_complex_check_fs = ft.Text("Original file size: -")

    dc_file_header = ft.Text("Readed file header: -")
    dc_file_original_size = ft.Text("Original file size: -")

    tabs = ft.Tabs(
        tabs=[
            ft.Tab(
                text="Encode",
                content=ft.Column(
                    [
                        ft.Text("Encode mode"),
                        ft.Button("Pick a file",
                                  on_click=encode_btn_click),
                        ft.Text("Click the button below to select a file..."),
                        efs_text, efn_text,
                        ft.Button("🚀Encode!", on_click=in_page_encode),
                        dres_img,
                        ft.Button("💾Save", on_click=save_btn_click)
                    ]
                )
            ),
            ft.Tab(
                text="Decode",
                content=ft.Column(
                    [
                        ft.Text("Decode mode"),
                        ft.Text("🏗This Page is UNDER CONSTRUCTING!"),
                        ft.Text("Click the button below to select a file..."),
                        ft.Button("Pick a file",
                                  on_click=decode_btn_click),

                        dfs_text, dfn_text,
                        ft.Button("👀Complexity check",
                                  on_click=decode_complexity_check),
                        dfn_complex_check, dfn_complex_check_fn, dfn_complex_check_fs,
                        ft.Button("🗡Decode", on_click=in_page_decode)
                    ]
                )
            )]

    )

    text_header = ft.Text("FTI - Encoder/Decoder", size=30, weight="bold")
    txt_desc = ft.Text("—By XTeclab —", italic=True)
    page.add(text_header, txt_desc, tabs)
    page.overlay.append(file_picker)
    page.overlay.append(sav_picker)
    page.update()


ft.app(main)
