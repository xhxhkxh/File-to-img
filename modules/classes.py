
from PIL import Image


class header:
    def __init__(self, fname: str, fsize: int, checksum: str, raw_data=[]):
        self.fname = fname
        self.fsize = fsize
        self.checksum = checksum
        self.raw_data = raw_data

    def toString(self) -> str:
        return f"Filename: {self.fname}\nFilesize: {self.fsize}\nChecksum: {self.checksum}"

    def fromImg(self, raw: Image.Image) -> None:
        from modules.enc import headerInfo
        self.fname, self.fsize, self.checksum, self.raw_data = headerInfo(raw)

    def toList(self) -> tuple[str, int, str, list]:
        return (self.fname, self.fsize, self.checksum, self.raw_data)

    def getRaw(self) -> list:
        return self.raw_data
