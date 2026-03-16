#!/usr/bin/env python3
import sys
from typing import Dict

KEYS = [
    "OBJECT",
    "RA",
    "DEC",
    "OBJCTRA",
    "OBJCTDEC",
    "EXPTIME",
    "EXPOSURE",
    "GAIN",
    "FILTER",
    "DATE-OBS",
    "BAYERPAT",
    "XBAYROFF",
    "YBAYROFF",
    "COLORTYP",
    "CFA",
]

SEP = "|"

def clean(value: str) -> str:
    return str(value).replace(SEP, "/").strip()

def parse_value(raw: str):
    raw = raw.strip()
    if not raw:
        return ""
    if raw.startswith("'"):
        end = raw.rfind("'")
        if end > 0:
            return raw[1:end].strip()
        return raw.strip("'").strip()
    if raw in ("T", "F"):
        return raw
    try:
        if any(c in raw for c in (".", "E", "e")):
            return str(float(raw))
        return str(int(raw))
    except Exception:
        return raw

def read_header(path: str) -> Dict[str, str]:
    result: Dict[str, str] = {}
    with open(path, "rb") as handle:
        while True:
            block = handle.read(2880)
            if not block:
                break
            if len(block) % 80 != 0:
                raise ValueError("invalid FITS header block size")
            for idx in range(0, len(block), 80):
                card = block[idx:idx + 80].decode("ascii", errors="ignore")
                key = card[:8].strip()
                if key == "END":
                    return result
                if not key:
                    continue
                if card[8:10] == "= ":
                    value_part = card[10:]
                    if "/" in value_part:
                        value_part = value_part.split("/", 1)[0]
                    if key in KEYS:
                        result[key] = parse_value(value_part)
    return result

def first_nonempty(data: Dict[str, str], names):
    for name in names:
        val = data.get(name, "")
        if val not in ("", None):
            return clean(str(val))
    return ""

def infer_bayer(data: Dict[str, str]) -> str:
    direct = first_nonempty(data, ["BAYERPAT"])
    if direct:
        return direct.upper()
    cfa = first_nonempty(data, ["CFA", "COLORTYP"]).upper()
    if cfa in {"RGGB", "BGGR", "GBRG", "GRBG"}:
        return cfa
    return ""

def emit(*fields: str) -> None:
    print(SEP.join("" if f is None else clean(str(f)) for f in fields))

def main() -> int:
    if len(sys.argv) != 2:
        emit("badfit", "usage error", "", "", "", "", "", "", "", "", "", "", "", "")
        return 0

    path = sys.argv[1]
    try:
        data = read_header(path)
    except Exception as exc:
        emit("badfit", f"header parse failed: {exc}", "", "", "", "", "", "", "", "", "", "", "", "")
        return 0

    obj = first_nonempty(data, ["OBJECT"])
    ra = first_nonempty(data, ["RA", "OBJCTRA"])
    dec = first_nonempty(data, ["DEC", "OBJCTDEC"])
    exptime = first_nonempty(data, ["EXPTIME", "EXPOSURE"])
    gain = first_nonempty(data, ["GAIN"])
    filt = first_nonempty(data, ["FILTER"])
    date_obs = first_nonempty(data, ["DATE-OBS"])
    bayerpat = infer_bayer(data)
    xbayroff = first_nonempty(data, ["XBAYROFF"])
    ybayroff = first_nonempty(data, ["YBAYROFF"])

    is_color_sensor = "1" if bayerpat else "0"
    debayer_required = "1" if bayerpat else "0"

    emit(
        "ok",
        "",
        obj,
        ra,
        dec,
        exptime,
        gain,
        filt,
        date_obs,
        bayerpat,
        xbayroff,
        ybayroff,
        is_color_sensor,
        debayer_required,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
