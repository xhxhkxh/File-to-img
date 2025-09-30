import flet as ft
from PIL import Image
from math import sqrt, ceil
from struct import pack
from os import path
import sys
import io
import base64
import os


def pil_to_b64(pil_img: Image.Image) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def _is_android_env() -> bool:
    """Rudimentary check whether we're running on Android."""
    try:
        return sys.platform.startswith('linux') and (
            'ANDROID_BOOTLOGO' in os.environ or
            'ANDROID_ROOT' in os.environ or
            'ANDROID_DATA' in os.environ
        )
    except Exception:
        return False


def _write_bytes_to_saf_uri(uri_str: str, data: bytes) -> bool:
    """Try to write bytes to a content:// URI using available Android bridges.

    Returns True on success, False on failure.
    """
    # Try an "android" helper module first (some packagers provide helpers)
    try:
        import android as _android
        if hasattr(_android, 'open_file'):
            with _android.open_file(uri_str, 'wb') as f:
                f.write(data)
            return True
    except Exception:
        pass

    # Try pyjnius to call Android APIs (preferred path)
    try:
        from jnius import autoclass, cast

        Uri = autoclass('android.net.Uri')
        activity = None
        # Known activity classes from various packagers
        for clsname in (
            'org.kivy.android.PythonActivity',
            'com.chaquo.python.PythonActivity',
            'org.renpy.android.PythonActivity',
            'org.beeware.android.PythonActivity',
            'io.flutter.embedding.android.FlutterActivity'
        ):
            try:
                PyAct = autoclass(clsname)
                # Try common patterns to obtain activity instance
                if hasattr(PyAct, 'mActivity'):
                    activity = PyAct.mActivity
                    break
                elif hasattr(PyAct, 'getInstance'):
                    activity = PyAct.getInstance()
                    break
            except Exception:
                continue

        # Fallback: ActivityThread.currentActivity()
        if activity is None:
            try:
                ActivityThread = autoclass('android.app.ActivityThread')
                activity = ActivityThread.currentActivity()
            except Exception:
                activity = None

        if activity is None:
            return False

        resolver = activity.getContentResolver()
        uri = Uri.parse(uri_str)

        # First try: openOutputStream (convenient)
        try:
            outstream = resolver.openOutputStream(uri)
            if outstream is not None:
                chunk_size = 16384
                off = 0
                b = data
                while off < len(b):
                    end = min(off + chunk_size, len(b))
                    outstream.write(bytearray(b[off:end]))
                    off = end
                outstream.close()
                return True
        except Exception:
            # Continue to fallback method
            pass

        # Fallback: openFileDescriptor + FileOutputStream
        try:
            ParcelFileDescriptor = autoclass('android.os.ParcelFileDescriptor')
            FileOutputStream = autoclass('java.io.FileOutputStream')

            pfd = resolver.openFileDescriptor(uri, 'w')
            if pfd is None:
                return False

            fd = pfd.getFileDescriptor()
            fos = FileOutputStream(fd)

            # write in chunks
            chunk_size = 16384
            off = 0
            b = data
            while off < len(b):
                end = min(off + chunk_size, len(b))
                fos.write(bytearray(b[off:end]))
                off = end

            fos.close()
            pfd.close()
            return True
        except Exception as ex2:
            print('SAF write via pyjnius (fd fallback) failed:', ex2)
            return False
    except Exception as ex:
        print('SAF write via pyjnius failed:', ex)
        return False


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
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.bgcolor = ft.Colors.GREY_50

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
            efn_text.value = global_file.name
            efs_text.value = f"{str(b2mb(global_file.size))} MB ({str(global_file.size)} bytes)"
            encode_file_card.visible = True
            page.update()
        elif e.files and ongoing_Type == "decode":
            global_file = e.files[0]
            dfn_text.value = global_file.name
            dfs_text.value = f"{str(b2mb(global_file.size))} MB ({str(global_file.size)} bytes)"
            decode_file_card.visible = True
            page.update()
        else:
            print("No file selected")
            show_invalid_alert(page)

    file_picker = ft.FilePicker(on_result=lambda e: on_file_picked(e))
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
        result_card.visible = True
        page.update()

    def save_btn_click(_):
        global pil_encoded
        if pil_encoded is None:
            page.snack_bar = ft.SnackBar(
                ft.Text("还没有可保存的图片！"),
                bgcolor=ft.Colors.ORANGE_400
            )
            page.snack_bar.open = True
            page.update()
            return
        save_image(pil_encoded)

    def save_image(img):
        def on_result(e: ft.FilePickerResultEvent):
            try:
                # Preferred: when a path is provided (desktop or writable path on mobile)
                if getattr(e, "path", None):
                    dest_path = e.path if e.path.lower().endswith(
                        (".png", ".jpg", ".jpeg")) else e.path + ".png"
                    Image.open(io.BytesIO(base64.b64decode(img))
                               ).save(dest_path, format="PNG")
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"✓ Image saved as {dest_path}", color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.GREEN_400,
                        duration=2000
                    )
                    page.snack_bar.open = True
                    page.update()
                else:
                    # Fallback when no concrete path is provided (common on some Android devices / SAF URIs)
                    # Try SAF write if on Android and a URI-like string is available in e.files[0].uri
                    fallback = "encoded_image.png"
                    saved = False
                    try:
                        # Some flet Android builds provide a `uri` or `uri_str` attribute on the FilePicker file entry
                        file_entry = None
                        if getattr(e, 'files', None):
                            file_entry = e.files[0]
                        uri_candidate = None
                        if file_entry is not None and hasattr(file_entry, 'uri'):
                            uri_candidate = file_entry.uri
                        if not uri_candidate and file_entry is not None and hasattr(file_entry, 'path'):
                            # path may be a content URI string in some runtimes
                            uri_candidate = file_entry.path

                        if _is_android_env() and uri_candidate and uri_candidate.startswith('content://'):
                            raw = base64.b64decode(img)
                            if _write_bytes_to_saf_uri(uri_candidate, raw):
                                page.snack_bar = ft.SnackBar(
                                    content=ft.Text(
                                        f"✓ Image saved to chosen location via SAF.", color=ft.Colors.WHITE),
                                    bgcolor=ft.Colors.GREEN_400,
                                    duration=3000
                                )
                                page.snack_bar.open = True
                                page.update()
                                saved = True
                        if not saved:
                            Image.open(io.BytesIO(base64.b64decode(img))).save(
                                fallback, format="PNG")
                            print(
                                f"Warning: save_file returned no path; saved to fallback {fallback}")
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text(
                                    f"✓ Image saved as {fallback} (fallback). On Android the chosen location may not be directly writable; check storage permissions or use a share action.",
                                    color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.ORANGE_400,
                                duration=4000
                            )
                            page.snack_bar.open = True
                            page.update()
                    except Exception as saf_ex:
                        print('SAF fallback failed:', saf_ex)
                        Image.open(io.BytesIO(base64.b64decode(img))
                                   ).save(fallback, format="PNG")
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(
                                f"Saved to fallback {fallback}. SAF attempt failed: {saf_ex}", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.ORANGE_400,
                            duration=4000
                        )
                        page.snack_bar.open = True
                        page.update()
            except Exception as ex:
                print("Save image failed:", ex)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(
                        f"✗ Save failed: {ex}", color=ft.Colors.WHITE),
                    bgcolor=ft.Colors.RED_400,
                    duration=4000
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

            dfn_complex_check.value = "✓ Valid"
            dfn_complex_check.color = ft.Colors.GREEN_700
            dfn_complex_check_fs.value = f"{file_size} bytes"
            dfn_complex_check_fn.value = file_name
            complexity_result_card.visible = True
        except Exception as ex:
            dfn_complex_check.value = "✗ Invalid"
            dfn_complex_check.color = ft.Colors.RED_700
            dfn_complex_check_fn.value = "-"
            dfn_complex_check_fs.value = "-"
            complexity_result_card.visible = True
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
                duration=2000
            )
            page.snack_bar.open = True
            page.update()
            return
        else:
            restore_manual_cancel = False

            def on_result(e: ft.FilePickerResultEvent):
                try:
                    # Try direct write to provided path (desktop or writable path on platform)
                    if getattr(e, "path", None):
                        dest_path = e.path
                        try:
                            with open(dest_path, 'wb') as file:
                                for i in datas:
                                    file.write(i)
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text(
                                    f"✓ File restored as {dest_path}", color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.GREEN_400,
                                duration=2000
                            )
                        except Exception as write_ex:
                            # Fallback: write to local app folder instead
                            fallback = restore_file_name if restore_file_name else "restored_file"
                            with open(fallback, 'wb') as file:
                                for i in datas:
                                    file.write(i)
                            print(
                                f"Write to {dest_path} failed: {write_ex}; saved to fallback {fallback}")
                            page.snack_bar = ft.SnackBar(
                                content=ft.Text(
                                    f"Saved to fallback {fallback} because writing to {dest_path} failed: {write_ex}",
                                    color=ft.Colors.WHITE),
                                bgcolor=ft.Colors.ORANGE_400,
                                duration=4000
                            )
                    else:
                        # No concrete path returned — save to fallback file in app directory
                        fallback = restore_file_name if restore_file_name else "restored_file"
                        with open(fallback, 'wb') as file:
                            for i in datas:
                                file.write(i)
                        page.snack_bar = ft.SnackBar(
                            content=ft.Text(
                                f"✓ File restored as {fallback} (fallback). On Android the chosen location may not be directly writable.", color=ft.Colors.WHITE),
                            bgcolor=ft.Colors.ORANGE_400,
                            duration=4000
                        )
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    print("Restore failed:", ex)
                    page.snack_bar = ft.SnackBar(
                        content=ft.Text(
                            f"✗ File restore failed: {ex}", color=ft.Colors.WHITE),
                        bgcolor=ft.Colors.RED_400,
                        duration=4000
                    )
                    page.snack_bar.open = True
                    page.update()
            sav_picker.on_result = on_result
            sav_picker.save_file(
                file_name=restore_file_name if restore_file_name else "restored_file",
                allowed_extensions=None
            )

    # UI Components - Encode Section
    efn_text = ft.Text("-", size=14, weight=ft.FontWeight.W_500)
    efs_text = ft.Text("-", size=12, color=ft.Colors.GREY_700)

    encode_file_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.INSERT_DRIVE_FILE,
                        color=ft.Colors.BLUE_700, size=20),
                ft.Column([
                    ft.Text("File Name", size=11, color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500),
                    efn_text
                ], spacing=2, expand=True)
            ], spacing=10),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            ft.Row([
                ft.Icon(ft.Icons.DATA_USAGE,
                        color=ft.Colors.BLUE_700, size=20),
                ft.Column([
                    ft.Text("File Size", size=11, color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500),
                    efs_text
                ], spacing=2, expand=True)
            ], spacing=10)
        ], spacing=12),
        padding=15,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.BLUE_200),
        visible=False
    )

    dres_img = ft.Image(border_radius=8)

    result_card = ft.Container(
        content=ft.Column([
            ft.Text("Encoded Result", size=16,
                    weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
            ft.Container(
                content=dres_img,
                border_radius=8,
                border=ft.border.all(2, ft.Colors.GREEN_200)
            )
        ], spacing=10),
        padding=15,
        bgcolor=ft.Colors.GREEN_50,
        border_radius=10,
        visible=False
    )

    # UI Components - Decode Section
    dfn_text = ft.Text("-", size=14, weight=ft.FontWeight.W_500)
    dfs_text = ft.Text("-", size=12, color=ft.Colors.GREY_700)

    decode_file_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.IMAGE, color=ft.Colors.PURPLE_700, size=20),
                ft.Column([
                    ft.Text("File Name", size=11, color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500),
                    dfn_text
                ], spacing=2, expand=True)
            ], spacing=10),
            ft.Divider(height=1, color=ft.Colors.GREY_300),
            ft.Row([
                ft.Icon(ft.Icons.DATA_USAGE,
                        color=ft.Colors.PURPLE_700, size=20),
                ft.Column([
                    ft.Text("File Size", size=11, color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500),
                    dfs_text
                ], spacing=2, expand=True)
            ], spacing=10)
        ], spacing=12),
        padding=15,
        bgcolor=ft.Colors.PURPLE_50,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.PURPLE_200),
        visible=False
    )

    dfn_complex_check = ft.Text("-", size=16, weight=ft.FontWeight.BOLD)
    dfn_complex_check_fn = ft.Text("-", size=13)
    dfn_complex_check_fs = ft.Text("-", size=13)

    complexity_result_card = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.VERIFIED, size=20),
                ft.Text("Complexity Check", size=14,
                        weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_800)
            ], spacing=8),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Status:", size=12,
                                color=ft.Colors.GREY_600, width=120),
                        dfn_complex_check
                    ]),
                    ft.Row([
                        ft.Text("Original Name:", size=12,
                                color=ft.Colors.GREY_600, width=120),
                        dfn_complex_check_fn
                    ]),
                    ft.Row([
                        ft.Text("Original Size:", size=12,
                                color=ft.Colors.GREY_600, width=120),
                        dfn_complex_check_fs
                    ])
                ], spacing=8),
                padding=10,
                bgcolor=ft.Colors.WHITE,
                border_radius=6
            )
        ], spacing=10),
        padding=15,
        bgcolor=ft.Colors.GREY_100,
        border_radius=10,
        border=ft.border.all(1, ft.Colors.GREY_300),
        visible=False
    )

    # Main Tabs (改为 Column + Buttons)
    def show_encode(e):
        encode_content.visible = True
        decode_content.visible = False
        page.update()

    def show_decode(e):
        encode_content.visible = False
        decode_content.visible = True
        page.update()

    encode_content = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Encode Files to Images",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_900),
                    ft.Text("Convert any file into an encoded image format",
                            size=13,
                            color=ft.Colors.GREY_600)
                ], spacing=5),
                padding=ft.padding.only(bottom=20)
            ),
            ft.ElevatedButton(
                "Select File to Encode",
                icon=ft.Icons.UPLOAD_FILE,
                on_click=encode_btn_click,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_700,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            ),
            encode_file_card,
            ft.ElevatedButton(
                "Start Encoding",
                icon=ft.Icons.ROCKET_LAUNCH,
                on_click=in_page_encode,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_600,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            ),
            result_card,
            ft.ElevatedButton(
                "Save Image",
                icon=ft.Icons.SAVE,
                on_click=save_btn_click,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.AMBER_700,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            )
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30,
        visible=True
    )

    decode_content = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Text("Decode Images to Files",
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.PURPLE_900),
                    ft.Text("Extract original files from encoded images",
                            size=13,
                            color=ft.Colors.GREY_600)
                ], spacing=5),
                padding=ft.padding.only(bottom=20)
            ),
            ft.ElevatedButton(
                "Select Image to Decode",
                icon=ft.Icons.IMAGE_SEARCH,
                on_click=decode_btn_click,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.PURPLE_700,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            ),
            decode_file_card,
            ft.ElevatedButton(
                "Run Complexity Check",
                icon=ft.Icons.FACT_CHECK,
                on_click=decode_complexity_check,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.INDIGO_600,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            ),
            complexity_result_card,
            ft.ElevatedButton(
                "Start Decoding",
                icon=ft.Icons.PLAY_ARROW,
                on_click=in_page_decode,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_600,
                    padding=15,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=250
            )
        ], spacing=20, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30,
        visible=False
    )

    tabs = ft.Column(
        [
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Encode", on_click=show_encode, width=140),
                    ft.ElevatedButton(
                        "Decode", on_click=show_decode, width=140),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12
            ),
            ft.Divider(height=1, color=ft.Colors.GREY_200),
            encode_content,
            decode_content
        ],
        expand=1,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Header
    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.LOCK, size=40, color=ft.Colors.BLUE_700),
                ft.Column([
                    ft.Text("FTI Encoder/Decoder",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_900),
                    ft.Text("By XTeclab",
                            size=14,
                            italic=True,
                            color=ft.Colors.GREY_600)
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
        ]),
        padding=20,
        margin=ft.margin.only(bottom=20)
    )

    # Main container
    main_container = ft.Container(
        content=ft.Column([
            header,
            ft.Container(
                content=tabs,
                bgcolor=ft.Colors.WHITE,
                border_radius=15,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                    offset=ft.Offset(0, 2)
                ),
                padding=0,
                expand=True
            )
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        width=800,
        expand=True
    )

    page.add(main_container)
    page.overlay.append(file_picker)
    page.overlay.append(sav_picker)
    page.update()


ft.app(main)
