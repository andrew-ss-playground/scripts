from typing import Any
from datetime import date, datetime

def parse_phone(raw_phone: Any) -> str | None:
    digits = ''.join(filter(str.isdigit, str(raw_phone or "")))
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        return raw_phone if raw_phone else None
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

def parse_full_location(row) -> str:
    dropoff_parts = [
        row.get("DropoffLocation"),
        row.get("DropoffDormRoomNumber"),
        row.get("DropoffDormRoomLetter"),
        row.get("DropoffAddressLine1"),
        row.get("DropoffAddressLine2"),
    ]
    return " ".join(str(part) for part in dropoff_parts if part not in (None, "", "None", "Off-Campus")).strip()

def parse_file_type(filepath: str) -> str:
    if "." in filepath:
        return filepath.split(".")[-1]
    else:
        raise Exception(f"{filepath} is missing a file type")

def parse_date(val: Any) -> date | None:
    if not val:
        return None
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        for format in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(val, format).date()
            except Exception:
                continue
    return None  # Instead of raising ValueError

def parse_int(val: Any) -> int | None:
    try:
        i = int(val)
        return i if i != 0 else None
    except (TypeError, ValueError):
        return None
