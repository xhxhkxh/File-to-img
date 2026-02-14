CUSTOM_FILENAME_BEGIN = "Filename_beg:"
CUSTOM_FILENAME_END = "Filename_end"
CUSTOM_FILESIZE_BEGIN = "siZe:"
CUSTOM_FILESIZE_END = "size_end"
CUSTOM_CHECKSUM_BEGIN = "CRC16-CCITT:"
CUSTOM_CHECKSUM_END = "CRC16_end"

MB_SIZE = 1048576

SUB_LOG_PREFIX = "|____"


def getPrefix(depth: int) -> str:
    return "|" + "____" * depth
