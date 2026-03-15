#!/usr/bin/env python3
import math
import subprocess
import sys
from pathlib import Path

def parse_wcsinfo_text(text: str):
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or " " not in line:
            continue
        key, value = line.split(None, 1)
        data[key.strip()] = value.strip()
    return data

def as_float(d, key):
    v = d.get(key, "")
    if v == "":
        return None
    try:
        return float(v)
    except Exception:
        return None

def from_wcsinfo(wcs_path: str):
    proc = subprocess.run(
        ["wcsinfo", wcs_path],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"wcsinfo rc={proc.returncode}")

    d = parse_wcsinfo_text(proc.stdout)

    ra = as_float(d, "ra_center")
    dec = as_float(d, "dec_center")
    fov_x = as_float(d, "fieldw")
    fov_y = as_float(d, "fieldh")
    pixscale = as_float(d, "pixscale")
    rot = as_float(d, "orientation_center")
    if rot is None:
        rot = as_float(d, "orientation")

    if ra is None or dec is None:
        raise RuntimeError("wcsinfo returned no center coordinates")

    return {
        "ra_deg": ra,
        "dec_deg": dec,
        "fov_x_deg": fov_x,
        "fov_y_deg": fov_y,
        "pixscale_arcsec_per_pix": pixscale,
        "rotation_deg": rot,
        "engine": "wcsinfo",
        "message": "",
    }

def from_fits_wcs(wcs_path: str):
    from astropy.io import fits
    from astropy.wcs import WCS

    h = fits.getheader(wcs_path, 0)
    w = WCS(h)

    naxis1 = h.get("NAXIS1")
    naxis2 = h.get("NAXIS2")
    if not naxis1 or not naxis2:
        raise RuntimeError("missing NAXIS1/NAXIS2 in WCS header")

    cx = naxis1 / 2.0
    cy = naxis2 / 2.0
    ra, dec = w.wcs_pix2world([[cx, cy]], 0)[0]

    if "CD1_1" in h:
        cd11 = float(h["CD1_1"])
        cd12 = float(h.get("CD1_2", 0.0))
        cd21 = float(h.get("CD2_1", 0.0))
        cd22 = float(h["CD2_2"])
        sx = math.hypot(cd11, cd21)
        sy = math.hypot(cd12, cd22)
        pixscale = ((sx + sy) / 2.0) * 3600.0
        rot = math.degrees(math.atan2(cd12, cd11))
    else:
        cdelt1 = abs(float(h.get("CDELT1", 0.0)))
        cdelt2 = abs(float(h.get("CDELT2", 0.0)))
        sx = cdelt1
        sy = cdelt2
        pixscale = ((sx + sy) / 2.0) * 3600.0 if sx and sy else None
        rot = None

    fov_x = float(naxis1) * sx
    fov_y = float(naxis2) * sy

    return {
        "ra_deg": float(ra),
        "dec_deg": float(dec),
        "fov_x_deg": fov_x,
        "fov_y_deg": fov_y,
        "pixscale_arcsec_per_pix": pixscale,
        "rotation_deg": rot,
        "engine": "astropy-wcs",
        "message": "fallback from FITS WCS",
    }

def main():
    if len(sys.argv) != 2:
        print("usage: astro_extract_wcsinfo.py /path/to/solution.wcs", file=sys.stderr)
        sys.exit(2)

    wcs_path = sys.argv[1]
    if not Path(wcs_path).exists():
        print(f"missing file: {wcs_path}", file=sys.stderr)
        sys.exit(3)

    try:
        result = from_wcsinfo(wcs_path)
    except Exception as e1:
        try:
            result = from_fits_wcs(wcs_path)
            result["message"] = f"wcsinfo failed: {e1}; astropy fallback used"
        except Exception as e2:
            print(f"ERROR\twcsinfo={e1}\tastropy={e2}")
            sys.exit(4)

    print(
        "OK\t{ra_deg}\t{dec_deg}\t{fov_x_deg}\t{fov_y_deg}\t{pixscale_arcsec_per_pix}\t{rotation_deg}\t{engine}\t{message}".format(
            ra_deg="" if result["ra_deg"] is None else result["ra_deg"],
            dec_deg="" if result["dec_deg"] is None else result["dec_deg"],
            fov_x_deg="" if result["fov_x_deg"] is None else result["fov_x_deg"],
            fov_y_deg="" if result["fov_y_deg"] is None else result["fov_y_deg"],
            pixscale_arcsec_per_pix="" if result["pixscale_arcsec_per_pix"] is None else result["pixscale_arcsec_per_pix"],
            rotation_deg="" if result["rotation_deg"] is None else result["rotation_deg"],
            engine=result["engine"],
            message=result["message"],
        )
    )

if __name__ == "__main__":
    main()
