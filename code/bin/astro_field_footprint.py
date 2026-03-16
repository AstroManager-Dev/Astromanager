#!/usr/bin/env python3
import json
import math
import sys
from pathlib import Path

from astropy.io import fits
from astropy.wcs import WCS


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def load_header(path: str):
    with fits.open(path) as hdul:
        return hdul[0].header


def get_pixel_scale_deg_per_pix(hdr) -> tuple[float, float]:
    if "CD1_1" in hdr:
        cd11 = float(hdr["CD1_1"])
        cd12 = float(hdr.get("CD1_2", 0.0))
        cd21 = float(hdr.get("CD2_1", 0.0))
        cd22 = float(hdr.get("CD2_2", 0.0))
        sx = math.hypot(cd11, cd21)
        sy = math.hypot(cd12, cd22)
        return abs(sx), abs(sy)
    if "CDELT1" in hdr and "CDELT2" in hdr:
        return abs(float(hdr["CDELT1"])), abs(float(hdr["CDELT2"]))
    raise ValueError("No CD/CDELT information found")


def main() -> None:
    if len(sys.argv) != 3:
        die("usage: astro_field_footprint.py <solution.wcs> <reference_image.fits>")

    wcs_path = sys.argv[1]
    ref_path = sys.argv[2]

    if not Path(wcs_path).is_file():
        die(f"WCS file not found: {wcs_path}")
    if not Path(ref_path).is_file():
        die(f"Reference FITS not found: {ref_path}")

    wh = load_header(wcs_path)
    ih = load_header(ref_path)

    nx = ih.get("NAXIS1")
    ny = ih.get("NAXIS2")
    if not nx or not ny:
        die("Reference FITS missing NAXIS1/NAXIS2")

    w = WCS(wh)

    cx = nx / 2.0
    cy = ny / 2.0

    center = w.wcs_pix2world([[cx, cy]], 0)[0]
    ul = w.wcs_pix2world([[0.0, 0.0]], 0)[0]
    ur = w.wcs_pix2world([[float(nx), 0.0]], 0)[0]
    lr = w.wcs_pix2world([[float(nx), float(ny)]], 0)[0]
    ll = w.wcs_pix2world([[0.0, float(ny)]], 0)[0]

    sx, sy = get_pixel_scale_deg_per_pix(wh)
    fovx = float(nx) * sx
    fovy = float(ny) * sy
    radius = 0.5 * math.hypot(fovx, fovy) * 1.10

    rotation = None
    if "CD1_1" in wh and "CD1_2" in wh:
        rotation = math.degrees(math.atan2(float(wh["CD1_2"]), float(wh["CD1_1"])))

    out = {
        "center_ra_deg": float(center[0]),
        "center_dec_deg": float(center[1]),
        "fov_x_deg": float(fovx),
        "fov_y_deg": float(fovy),
        "footprint_radius_deg": float(radius),
        "rotation_deg": None if rotation is None else float(rotation),
        "corner_ul_ra_deg": float(ul[0]),
        "corner_ul_dec_deg": float(ul[1]),
        "corner_ur_ra_deg": float(ur[0]),
        "corner_ur_dec_deg": float(ur[1]),
        "corner_lr_ra_deg": float(lr[0]),
        "corner_lr_dec_deg": float(lr[1]),
        "corner_ll_ra_deg": float(ll[0]),
        "corner_ll_dec_deg": float(ll[1]),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
