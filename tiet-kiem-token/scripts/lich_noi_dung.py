"""Dựng nội dung lịch tự đo (plist macOS, dòng crontab). Chỉ dựng chuỗi/bytes, không đụng launchd/crontab thật,
để do-tu-dong.py gọi và để bộ thử kiểm đường dẫn có ký tự đặc biệt (& ' % khoảng trắng)."""
import plistlib
import shlex


def dung_plist(nhan, py, sc, goc, thu, gio):
    """Bytes của tệp plist launchd; plistlib tự thoát ký tự XML."""
    return plistlib.dumps({
        "Label": nhan,
        "ProgramArguments": [str(py), str(sc), "chay", "--thu-muc", str(goc)],
        "StartCalendarInterval": {"Weekday": (thu + 1) % 7, "Hour": int(gio), "Minute": 0},
        "StandardOutPath": str(goc / "tu-dong.log"),
        "StandardErrorPath": str(goc / "tu-dong.log"),
    })


def dung_dong_cron(nhan, py, sc, goc, thu, gio):
    """1 dòng crontab: shlex.quote từng đường dẫn; '%' trong crontab là xuống dòng nên thoát thành '\\%'."""
    q = shlex.quote
    lenh = (f"{q(str(py))} {q(str(sc))} chay --thu-muc {q(str(goc))} "
            f">> {q(str(goc / 'tu-dong.log'))} 2>&1")
    return f"0 {int(gio)} * * {(thu + 1) % 7} {lenh.replace('%', chr(92) + '%')} # {nhan}"
