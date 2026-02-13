import base64
from io import BytesIO
import flet as ft
from PIL import Image, ImageShow
from modules.enc import encode, decode
from modules.tool import sep, b2mb, pil_to_b64
from datetime import datetime
import asyncio

globalfiles = []

enc_b64 = ''
enc_bytes = b''


async def mainEncode(page: ft.Page) -> None:
    global globalfiles, enc_b64, enc_bytes

    pring = ft.ProgressRing(visible=True, width=20,
                            height=20, align=ft.Alignment.CENTER)
    page.add(pring)
    page.update()

    await asyncio.sleep(0.5)

    if len(globalfiles) == 0:
        no_file_dialog = ft.AlertDialog(
            title="No File Selected",
            alignment=ft.Alignment.CENTER,
            actions=[ft.TextButton("OK", on_click=lambda _: page.pop_dialog())]
        )
        page.show_dialog(no_file_dialog)
        return
    st = datetime.now()
    print(f"[{st}][Main-ENC] Entering encoding sequence...")
    print(f"[Main-ENC] File to encode: {globalfiles[0]}")
    if (type(globalfiles[0]) != str):
        print("[Main-ENC] Invalid file path! Exiting...")
        return
    resImage = encode(globalfiles[0])
    enc_b64 = pil_to_b64(resImage[0])
    enc_bytes = resImage[1]
    et = datetime.now()
    print(f"[{et}][Main-ENC] Exited with b64:", enc_b64[:100] + "...")
    ee = et - st
    print(f"[Main-ENC] Time taken: {ee}")
    img = ft.Image(src=enc_b64, width=400, height=400)
    page.remove(pring)
    page.add(img)
    page.update()


def main(page: ft.Page):
    global globalfiles
    # Page Settings
    page.title = "File to Image Converter"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Func

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

    # UI Section

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

    header = ft.Text("File to Image Converter", size=20)

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

    page_ctrls = [header, enc_container,
                  enc_cf_btn, fileContainer, enc_btn, save_btn]

    for i in page_ctrls:
        page.add(i)


if __name__ == "__main__":
    ft.run(main)
