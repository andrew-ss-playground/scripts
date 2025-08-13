from typing import Any

def parse_phone(raw_phone: Any) -> str | None:
    digits = ''.join(filter(str.isdigit, str(raw_phone or "")))
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        return raw_phone if raw_phone else None
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

def parse_full_location(row) -> str:
    dropoff_parts = [
        row["DropoffLocation"],
        row["DropoffDormRoomNumber"],
        row["DropoffDormRoomLetter"],
        row["DropoffAddressLine1"],
        row["DropoffAddressLine2"],
    ]
    return " ".join(str(part) for part in dropoff_parts if part not in (None, "", "None", "Off-Campus")).strip()

def parse_file_type(filepath: str) -> str:
    if "." in filepath:
        return filepath.split(".")[-1]
    else:
        raise Exception(f"{filepath} is missing a file type")
