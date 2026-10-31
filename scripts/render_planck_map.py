"""Render measured SMICA temperatures; pixel degradation is for display only."""
from argparse import ArgumentParser
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
import healpy as hp
from cmb_lab.data import sha256, load_spectra
from cmb_lab.statistics import dl_to_cl
from cmb_lab.plots import style

p = ArgumentParser(description=__doc__)
p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
a = p.parse_args()
manifest = json.loads((a.root / "data/manifest.json").read_text())
record = manifest["smica"]
path = a.root / record["path"]
assert sha256(path) == record["sha256"], "SMICA input checksum changed"
out = a.root / "results/maps"
out.mkdir(parents=True, exist_ok=True)
style()
with fits.open(path, memmap=True) as hdus:
    header = hdus[1].header
    order = header["ORDERING"]
    unit = hdus[1].columns["I_STOKES"].unit
    if unit not in ("K_CMB", "K", "Kcmb"):
        raise ValueError(f"Unexpected temperature units: {unit}")
    assert header["NSIDE"] == 2048
    temperature = hp.ud_grade(hdus[1].data["I_STOKES"].ravel(), 256, order_in=order, order_out="RING") * 1e6
    mask_fraction = hp.ud_grade(hdus[1].data["TMASK"].ravel().astype(float), 256, order_in=order, order_out="RING")
    header_info = {key: header.get(key) for key in ("ORDERING", "NSIDE", "COORDSYS", "POLCCONV")}
display_mask = (mask_fraction < .95) | ~np.isfinite(temperature) | (np.abs(temperature) > 1e10)
visible = hp.ma(temperature)
visible.mask = display_mask
fig = plt.figure(figsize=(11, 5.7))
hp.mollview(visible, fig=fig.number, min=-300, max=300, cmap="RdBu_r", badcolor="#d5d9db",
            title="Planck 2018 / SMICA temperature", unit=r"$\Delta T$ [$\mu$K]", coord="G")
hp.graticule(dpar=30, dmer=60, alpha=.25)
fig.text(.5, .03, "Measured component-separated sky | Galactic coordinates | Grey: confidence mask\nPixel averaging to NSIDE 256 for display; this image is not used for the spectral p-values.", ha="center", fontsize=9)
fig.savefig(out / "planck_temperature.png", dpi=180, bbox_inches="tight")
plt.close(fig)

# Dedicated illustrative realizations, explicitly separate from the spectral MC batches.
_, theory_table = load_spectra(a.root, 128)
ell = theory_table[:, 0].astype(int)
cl = np.zeros(129)
cl[2:] = dl_to_cl(ell, theory_table[:, 1])
rng = np.random.default_rng(20261032)
fig = plt.figure(figsize=(11, 7))
for index in range(4):
    ls, ms = hp.Alm.getlm(128)
    alm = (rng.normal(size=len(ls)) + 1j * rng.normal(size=len(ls))) * np.sqrt(cl[ls] / 2)
    zero = ms == 0
    alm[zero] = rng.normal(size=zero.sum()) * np.sqrt(cl[ls[zero]])
    sky = hp.alm2map(alm, nside=64, lmax=128, fwhm=np.deg2rad(5), pol=False)
    hp.mollview(sky, fig=fig.number, sub=(2, 2, index + 1), min=-120, max=120, cmap="RdBu_r",
                title=f"Gaussian LCDM realization {index + 1}", unit=r"$\mu$K", cbar=True)
fig.suptitle("Different patterns from the same cosmology", y=.97, fontsize=16)
fig.text(.5, .035, "Simulated, not observed | ell = 2-128 | 5 degree Gaussian smoothing | seed 20261032", ha="center", fontsize=9)
fig.savefig(out / "simulated_skies.png", dpi=180, bbox_inches="tight")
plt.close(fig)
(out / "provenance.json").write_text(json.dumps({"source_sha256": record["sha256"], "source_url": record["url"],
    "input_header": header_info, "input_temperature_unit": unit, "display_nside": 256,
    "display_mask_min_fraction": .95, "display_retained_fraction": float((~display_mask).mean()),
    "map_used_for_significance": False, "illustrative_simulation_seed": 20261032,
    "healpy_version": hp.__version__}, indent=2) + "\n")
print("Rendered original Planck map and four illustrative Gaussian skies")
