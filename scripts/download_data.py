from argparse import ArgumentParser
from pathlib import Path
from cmb_lab.data import fetch

p = ArgumentParser(description="Download and verify original public Planck products")
p.add_argument("--with-map", action="store_true", help="Also download the ~2.0 GB SMICA FITS product")
p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
a = p.parse_args()
fetch(a.root, a.with_map)
