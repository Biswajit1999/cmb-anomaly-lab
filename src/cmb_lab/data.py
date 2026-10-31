"""Download official Planck products with explicit provenance and content hashes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import requests
import numpy as np

BASE = "https://irsa.ipac.caltech.edu/data/Planck/release_3/"
PRODUCTS = {
    "observed": "ancillary-data/cosmoparams/COM_PowerSpect_CMB-TT-full_R3.01.txt",
    "theory": "ancillary-data/cosmoparams/COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt",
    "smica": "all-sky-maps/maps/component-maps/cmb/COM_CMB_IQU-smica_2048_R3.00_full.fits",
}


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch(root, include_map=False):
    root = Path(root)
    raw = root / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = root / "data/manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for key in (["observed", "theory", "smica"] if include_map else ["observed", "theory"]):
        url = BASE + PRODUCTS[key]
        dest = raw / PRODUCTS[key].split("/")[-1]
        old = manifest.get(key)
        if dest.exists():
            digest = sha256(dest)
            if old and digest != old["sha256"]:
                raise ValueError(f"Checksum mismatch for {dest}; refusing to use changed input")
            if old:
                print(f"Verified {dest.name}", flush=True)
                continue
        else:
            print(f"Downloading {url}", flush=True)
            partial = dest.with_suffix(dest.suffix + ".part")
            offset = partial.stat().st_size if partial.exists() else 0
            headers = {"Range": f"bytes={offset}-"} if offset else {}
            with requests.get(url, headers=headers, stream=True, timeout=(30, 180)) as response:
                response.raise_for_status()
                if offset and response.status_code == 206:
                    if not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
                        raise IOError("Unexpected resume byte range")
                    mode = "ab"
                    print(f"  Resuming at {offset / 1e6:.0f} MB", flush=True)
                else:
                    offset, mode = 0, "wb"
                n = offset
                mark = offset
                with partial.open(mode) as out:
                    for chunk in response.iter_content(4 * 1024 * 1024):
                        out.write(chunk)
                        n += len(chunk)
                        if n - mark > 100_000_000:
                            print(f"  {n / 1e6:.0f} MB", flush=True)
                            mark = n
                expected = response.headers.get("Content-Length")
                if expected and n - offset != int(expected):
                    raise IOError("Truncated download")
            partial.replace(dest)
            digest = sha256(dest)
            if old and digest != old["sha256"]:
                raise ValueError("Remote product differs from recorded checksum")
        manifest[key] = {
            "url": url, "path": str(dest.relative_to(root)).replace("\\", "/"),
            "sha256": digest, "bytes": dest.stat().st_size,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "credit": "ESA and Planck Collaboration; NASA/IPAC IRSA distribution",
            "kind": "component-separated sky map" if key == "smica" else
                    ("published TT spectrum estimate" if key == "observed" else "best-fit LCDM theoretical D_ell"),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_spectra(root, lmax=128):
    manifest = json.loads((Path(root) / "data/manifest.json").read_text())
    arrays = []
    for key in ("observed", "theory"):
        path = Path(root) / manifest[key]["path"]
        if sha256(path) != manifest[key]["sha256"]:
            raise ValueError(f"Input changed: {key}")
        a = np.loadtxt(path)
        a = a[(a[:, 0] >= 2) & (a[:, 0] <= lmax)]
        if not np.array_equal(a[:, 0], np.arange(2, lmax + 1)):
            raise ValueError("Missing, repeated, or unordered multipoles")
        if not np.isfinite(a).all():
            raise ValueError("Non-finite spectrum")
        arrays.append(a)
    if np.any(arrays[1][:, 1] <= 0):
        raise ValueError("Theory spectrum must be positive")
    return arrays
