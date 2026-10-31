"""Check source/data provenance and repeat primary statistics with an independent seed."""
from pathlib import Path
import json
import numpy as np
from cmb_lab.data import sha256, load_spectra
from cmb_lab.statistics import NAMES, dl_to_cl, s_kernel, metrics, simulate, lower_tail

root = Path(__file__).resolve().parents[1]
result = json.loads((root / "results/baseline/results.json").read_text())
for name, digest in result["provenance"]["source_sha256"].items():
    assert sha256(root / name) == digest, f"Source differs from executed run: {name}"
for record in result["provenance"]["input_products"].values():
    assert sha256(root / record["path"]) == record["sha256"]
observed, theoretical = load_spectra(root, result["config"]["lmax"])
ell = observed[:, 0].astype(int)
obs = dl_to_cl(ell, observed[:, 1])
theory = dl_to_cl(ell, theoretical[:, 1])
n = 100000
seed = 904210
sims = simulate(ell, theory, n, np.random.default_rng(seed))
k = s_kernel(ell)
obs_m, sim_m = metrics(ell, obs, k), metrics(ell, sims, k)
checks = {}
for j, name in enumerate(NAMES):
    repeat = lower_tail(sim_m[:, j], obs_m[j])
    first = result["statistics"][name]
    sd = np.sqrt(first["p"] * (1 - first["p"]) / first["n"] + repeat["p"] * (1 - repeat["p"]) / n)
    difference = abs(repeat["p"] - first["p"])
    assert difference < 5 * sd, f"Unexpected seed instability: {name}"
    checks[name] = {"baseline_p": first["p"], "independent_seed": repeat,
                    "difference_in_combined_mc_sd": difference / sd}
out = {"status": "passed", "source_and_input_hashes_verified": True,
       "independent_seed": seed, "n_independent_spectra": n, "checks": checks,
       "scope": "Primary marginal probabilities only; not a second independent observation"}
(root / "results/validation.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
