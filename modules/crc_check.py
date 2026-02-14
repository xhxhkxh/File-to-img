from modules.custom import getPrefix
from modules.tool import b2mb
from datetime import datetime


def generate_crc16_table(poly=0x1021):
    """
    生成CRC16查找表
    poly: 生成多项式，常见的有：
          CRC16-CCITT: 0x1021
          CRC16-IBM:   0x8005
    """
    table = []
    for i in range(256):
        crc = i << 8  # 将字节左移8位
        for _ in range(8):  # 处理8个比特
            if crc & 0x8000:  # 检查最高位
                crc = ((crc << 1) & 0xFFFF) ^ poly
            else:
                crc = (crc << 1) & 0xFFFF
        table.append(crc)
    return table


print("[CRC16] Loading module...")
CRC16_CCITT_TABLE = generate_crc16_table(0x1021)
print("[CRC16] CRC16-CCITT lookup table generated.")
print(
    f"[CRC16] CRC16-CCITT Table Size: {len(CRC16_CCITT_TABLE)} entries. {CRC16_CCITT_TABLE[:5]} ... {CRC16_CCITT_TABLE[-5:]}")
print("[CRC16] Module loaded.")


def direct_crc16_ccitt(data: bytes, report, rep_size=-1) -> int:
    avg_clk = 0
    tsl_rec = []
    st = datetime.now()
    et = datetime.now()
    tel = et-st
    crc = 0xFFFF
    if report:
        if rep_size == -1:
            rep_size = max(1048576, len(data) // 100)  # 最多报告100次
            print(
                f"{getPrefix(3)} [CRC16-Direct:INFO] Report Interval not set, setting to: {rep_size/1024/1024:.2f}MB")
    wcount = 0
    for byte in data:
        if report and wcount % rep_size == 0:
            st = datetime.now()

        crc = ((crc << 8) & 0xFFFF) ^ CRC16_CCITT_TABLE[(
            (crc >> 8) ^ byte) & 0xFF]
        wcount += 1
        if report and wcount % rep_size == 0:
            print(
                f"\r{getPrefix(3)} [CRC16-Direct] Processed {wcount}/{len(data)} bytes| Progress: {wcount/len(data)*100:.2f}%", end="")
            et = datetime.now()
            tel = et-st
            tsl_rec.append(tel.total_seconds())
            if len(tsl_rec) > 100:
                tsl_rec.pop(0)
            avg_clk = sum(tsl_rec) / len(tsl_rec)
            eta = avg_clk * (len(data) - wcount) / rep_size
            print(
                f" | Average {avg_clk:.4f} s/chunk, ETA:{eta:.2f}s", end="")
    return crc


def crc16_ccitt(data: bytes, report, rep_size=1248576 * 10) -> int:
    '''
    crc16_ccitt 的 Docstring

    :param data: 传入的一个bytes对象，表示要计算CRC16校验码的数据
    :type data: bytes
    :return: 返回的校验码
    :rtype: int
    '''

    if report:
        size = len(data)
        print(
            f"{getPrefix(2)} [CRC16] Calculating CRC16-CCITT with report mode on.")
        print(
            f"{getPrefix(2)} [CRC16] With report param: {rep_size} bytes ({b2mb(rep_size)} mb)")
        wcount = 0

    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF

        if report:
            wcount += 1
            if wcount % rep_size == 0:
                print(
                    f"\r{getPrefix(3)} [CRC16] Processed {b2mb(wcount)} mb, Total {b2mb(size)} mb. | Progress: {wcount/size*100:.2f}%", end="\r")

    return crc
