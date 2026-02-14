import base64
from io import BytesIO
import flet as ft
from PIL import Image, ImageShow
from modules.enc import encode, decode, headerInfo
from modules.tool import sep, b2mb, pil_to_b64
from datetime import datetime
import asyncio

globalfiles = []

enc_b64 = ''
enc_bytes = b''
ignore_crc_mismatch = False


async def mainEncode(page: ft.Page) -> None:
    global globalfiles, enc_b64, enc_bytes

    pring = ft.ProgressRing(visible=True, width=20,
                            height=20, align=ft.Alignment.CENTER)
    page.add(pring)
    page.update()

    await asyncio.sleep(0.5)

    if len(globalfiles) == 0:  # type: ignore
        no_file_dialog = ft.AlertDialog(
            title="No File Selected",
            alignment=ft.Alignment.CENTER,
            actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
        )
        page.show_dialog(no_file_dialog)
        return
    st = datetime.now()
    print(f"[{st}][Main-ENC] Entering encoding sequence...")
    print(f"[Main-ENC] File to encode: {globalfiles[0]}")  # type: ignore
    if (type(globalfiles[0]) != str):  # type: ignore
        print("[Main-ENC:ERROR] Invalid file path! Exiting...")
        return
    resImage = encode(globalfiles[0])  # type: ignore
    enc_b64 = pil_to_b64(resImage[0])
    enc_bytes = resImage[1]
    et = datetime.now()
    print(f"[{et}][Main-ENC] Exited with b64:", enc_b64[:100] + "...")
    ee = et - st
    print(f"[Main-ENC] Time taken: {ee}")
    current_view = page.views[-1]
    if b2mb(len(enc_bytes)) >= 100:
        warn = ft.Text("Large file is not shown in preview.")
        prev_b64 = enc_b64[:100]
        prev_text = ft.Text(
            f"Preview (first 100 chars of base64): {prev_b64}...")

        current_view.controls.append(warn)
        current_view.controls.append(prev_text)
    else:
        img = ft.Image(src=enc_b64, width=400, height=400)
        current_view.controls.append(img)
    for view in page.views:
        if pring in view.controls:
            view.controls.remove(pring)
            break
    page.update()


async def main(page: ft.Page):
    global globalfiles, ignore_crc_mismatch
    # Page Settings
    page.title = "File to Image Converter"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Func

    async def handle_file_decode() -> None:
        global globalfiles
        files = await ft.FilePicker().pick_files(allow_multiple=False, allowed_extensions=["png"])
        fileValues = [i.path for i in files] if files else "Cancelled"
        if fileValues == "Cancelled":
            page.show_dialog(cancel_dialog)
            return
        print(fileValues)
        img = Image.open(fileValues[0])  # type: ignore
        try:
            info = headerInfo(img)
        except Exception as e:
            print(f"Error occured during headerInfo: {e}")
            errText = ft.Text(
                "Error occured during headerInfo: " + str(e), color=ft.Colors.RED)
            current_view = page.views[-1]
            current_view.controls.append(errText)
            page.update()
            return
        fName.value = "Filename: " + info[0]
        fSize.value = "Filesize: " + \
            str(b2mb(info[1])) + f" MB - ({info[1]}) bytes)"
        fChecksum.value = "Checksum: " + info[2]
        if b2mb(info[1]) >= 100:
            page.show_dialog(file_too_big_dialog)
        page.update()
        globalfiles = fileValues[0]

    def change_ignore_crc_mismatch(ignore) -> None:
        global ignore_crc_mismatch
        ignore_crc_mismatch = ignore
        print(f"[Main] Ignore CRC mismatch: {ignore_crc_mismatch}")

    async def handle_file_picked() -> list | str:
        global globalfiles
        files = await ft.FilePicker().pick_files(allow_multiple=False)
        fileValues = [i.path for i in files] if files else "Cancelled"
        if fileValues == "Cancelled":
            page.show_dialog(cancel_dialog)
            return "Cancelled"
        print(fileValues)
        with open(fileValues[0], 'rb') as file:  # type: ignore
            data = file.read()
        if fileValues != "Cancelled":
            fc_filename.value = "File Name: " + str(fileValues[0])
            fc_filesize.value = "File Size: " + \
                str(b2mb(len(data))) + \
                f" MB - ({len(data)}) bytes"
            page.update()
            globalfiles = fileValues
        return fileValues

    async def save_file() -> None:
        global globalfiles
        if globalfiles == []:
            print("No file to save.")
            page.show_dialog(not_encoded_dialog)
            return
        files = await ft.FilePicker().save_file(allowed_extensions=[".png"], file_name="encoded_image.png", src_bytes=enc_bytes)
        if files is None:
            print("Save cancelled.")
            page.show_dialog(cancel_dialog)
            return

    def process_checksum_mismatch_switch_change():
        global ignore_crc_mismatch
        ignore_crc_mismatch = not ignore_crc_mismatch
        if ignore_crc_mismatch:
            page.show_dialog(disable_crc_check_dialog)

    async def save_dec_file() -> None:
        global globalfiles, ignore_crc_mismatch
        if globalfiles == []:
            print("No file to save.")
            page.show_dialog(not_encoded_dialog)
            return
        fn = fName.value.split("Filename: ")[1]
        src = 'not_decoded'
        clc = 'not_decoded'
        try:
            src, clcSum = decode(Image.open(globalfiles),  # type: ignore
                                 ignore_crc_mismatch)  # type: ignore
        except Exception as e:
            if "Checksum Mismatch at Decoding process" in str(e):
                if ignore_crc_mismatch == True:
                    page.show_dialog(checksum_mismatch_dialog)
                err_clc = str(e).split(":")[1]
                fChecksum_calc.value = "Checksum: " + err_clc
                page.update()
                clc = err_clc
            else:
                # 其他异常
                print(f"其他错误: {e}")
                newErrorText = ft.Text(
                    f"Error occuared during decode: {e}", color=ft.Colors.RED)
                current_view = page.views[-1]
                current_view.controls.append(newErrorText)
                page.update()
                raise  # 重新抛出
        if clc != fChecksum.value[fChecksum.value.index(": ") + 1:] and not ignore_crc_mismatch:
            # Aborted becuse checksum mismatch
            page.show_dialog(checksum_mismatch_not_ignored_dialog)
        fChecksum_calc.value = "Checksum: " + clcSum
        if clcSum != fChecksum.value[fChecksum.value.index(": ") + 1:] and ignore_crc_mismatch:
            page.show_dialog(checksum_mismatch_dialog)
        # page.show_dialog(checksum_check_dialog)
        sf = await ft.FilePicker().save_file(file_name=fn, src_bytes=src)  # type: ignore
        if sf is None:
            print("Save cancelled.")
            page.show_dialog(cancel_dialog)
            return

    # UI Section

    # Page: Main Page
    def main_page():
        return ft.View(
            route="/", controls=main_page_ctrls, scroll=ft.ScrollMode.ADAPTIVE)

    # Page: Encoding page

    def encoding_page():
        return ft.View(
            route="/encode", controls=enc_page_ctrls, scroll=ft.ScrollMode.ADAPTIVE)

    # Page: Decoding page
    def decoding_page():
        return ft.View(
            route="/decode", controls=dec_page_ctrls, scroll=ft.ScrollMode.ADAPTIVE)

    cancel_dialog = ft.AlertDialog(
        title="Pick File Cancelled",
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
    )

    no_file_dialog = ft.AlertDialog(
        title="No File Selected",
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
    )

    not_encoded_dialog = ft.AlertDialog(
        title="No File Encoded",
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
    )

    file_too_big_dialog = ft.AlertDialog(
        title="Your file is too large",
        content=ft.Text("Your file is bigger than 100MB, the decoding and saving process will take a\
relevetively long time to complete."),
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
    )

    header = ft.Text("File to Image Converter",
                     size=20, align=ft.Alignment.CENTER)

    enc_container = ft.Container(content=ft.Column([
        ft.Text("Encode a file to an image:"),
    ]
    ), alignment=ft.Alignment
        .CENTER, padding=10, border=ft.Border.all(1, "black"), width=400)

    enc_cf_btn = ft.Button(
        "Choose File", on_click=handle_file_picked, icon=ft.icons.Icons.FOLDER_OPEN)

    fc_filesize = ft.Text("File Size: ")
    fc_filename = ft.Text("File Name: ")

    fileContainer = ft.Container(content=ft.Column([
        fc_filesize,
        fc_filename
    ]
    ), alignment=ft.Alignment
        .CENTER, padding=10, border=ft.Border.all(1, "black"), width=400)

    enc_btn = ft.Button(
        "Encode", on_click=lambda e: page.run_task(mainEncode, page), icon=ft.icons.Icons.LOCK)

    save_btn = ft.Button(
        "Save", on_click=lambda e: page.run_task(save_file), icon=ft.icons.Icons.DOWNLOAD)

    jmp_dec_btn = ft.TextButton(
        "Go to Decode Page", on_click=lambda _: asyncio.create_task(page.push_route("/decode")))

    enc_page_ctrls = [header, enc_container,
                      enc_cf_btn, fileContainer, enc_btn, save_btn, jmp_dec_btn]

    # UI for decoding page

    dec_text = ft.Text("Decode an image to file:")
    hint_text = ft.Text("Select an encoded image, and the file header would be auto\
matically shown below.")

    fileSelectBtn = ft.Button("Select Image", on_click=lambda e: page.run_task(
        handle_file_decode), icon=ft.icons.Icons.FOLDER_OPEN)

    saveFileBtn = ft.Button("Save Decoded File", on_click=lambda e: page.run_task(
        save_dec_file), icon=ft.icons.Icons.DOWNLOAD)

    # Decoding file header prediction
    fName = ft.Text("Filename: ")
    fSize = ft.Text("Filesize: ")
    fChecksum = ft.Text("Checksum: ")
    fChecksum_calc = ft.Text("Calculated Checksum: ")

    fileHeaderContainer = ft.Container(content=ft.Column([
        fName, fSize]), alignment=ft.Alignment.CENTER, padding=10, border=ft.Border.all(1, "black"), width=400)

    checksumContainer = ft.Container(
        content=ft.Column([fChecksum, fChecksum_calc]))

    # -----------Checksum Dialog----------------------
    checksum_check_dialog = ft.AlertDialog(
        title="Please check your file's checksum, then process to save if they are the same.",
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton(
            "I Acknowledged", on_click=lambda _: page.pop_dialog())]
    )

    disable_crc_check_dialog = ft.AlertDialog(
        title="Disable Checksum Check",
        content=ft.Text("You are trying to disable the checksum check. After disabling this feature,\
the program will unable to tell the file is modified, corrupted."),
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("    ", on_click=lambda _: page.pop_dialog(
        ))]
    )

    checksum_mismatch_not_ignored_dialog = ft.AlertDialog(
        title="Checksum Mismatch",
        content=ft.Text("The checksum of the decoded file does not match the original file's checksum.\n\
The file may be corrupted or the file may have been modified."),
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
    )

    checksum_mismatch_dialog = ft.AlertDialog(
        title="⚠Checksum Mismatch⚠",
        content=ft.Text(
            "Decode success. You have turned off the checksum check and this file's checksum doesn't match its original value.\n \
The file may be corrupted or the file may have been modified.\nYOU HAVE BEEN WARNED", color=ft.Colors.YELLOW),
        alignment=ft.Alignment.CENTER,
        actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog(
        )), ft.TextButton("Cancel", on_click=lambda _: exit())]
    )

    # ------------------------------------------------

    pcBtn = ft.Button("Back to Encoding Page", on_click=lambda _: asyncio.create_task(
        page.push_route("/encode")))

    ignore_crc_text = ft.Text("Ignore Checksum Mismatch")

    ignore_mismatch_switch = ft.Switch(
        label="Ignore Mismatch", value=False, on_change=lambda _: process_checksum_mismatch_switch_change())

    secure_settings = ft.Container(content=ft.Column([
        ignore_crc_text, ignore_mismatch_switch
    ]), alignment=ft.Alignment.CENTER, padding=10, border=ft.Border.all(1, "black"), width=400)
    dec_page_ctrls = [header, hint_text, dec_text,
                      fileHeaderContainer, fileSelectBtn, checksumContainer, saveFileBtn, secure_settings, pcBtn]

    # UI for main page

    mHearder = ft.Text("Welcome to File to Image Converter!", size=20)
    mText = ft.Text(
        "This application allows you to encode any file into a PNG image and decode it back to the original file. Click the button below to get started.")
    mEncBtn = ft.Button(
        "Start Encode", on_click=lambda _: page.push_route("/encode"))
    mDecBtn = ft.Button(
        "Start Decode", on_click=lambda _: page.push_route("/decode"))
    main_page_ctrls = [mHearder, mText, mEncBtn, mDecBtn]

    # Page Routing
    def route_change(route):
        page.views.clear()
        page.views.append(encoding_page())
        if page.route == "/encode":
            page.views.clear()
            page.views.append(encoding_page())
        elif page.route == "/decode":
            page.views.clear()
            page.views.append(decoding_page())
        elif page.route == "/":
            page.views.clear()
            page.views.append(main_page())

    async def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        await page.push_route(top_view.route)  # type: ignore
        page.update()

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    asyncio.create_task(page.push_route("/encode"))  # type: ignore
    page.update()


if __name__ == "__main__":
    ft.run(main)
