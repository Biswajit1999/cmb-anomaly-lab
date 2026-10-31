"""Run the retrospective spectral experiment and write auditable results."""
from argparse import ArgumentParser
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import time
import numpy as np
from scipy.stats import chi2, spearmanr
from .data import fetch, load_spectra, sha256
from .statistics import (NAMES, dl_to_cl, s_kernel, s_stat, metrics, parity,
                         simulate, lower_tail, empirical_p, family_min_p,
                         replacement_effects)


def run(root, config, out):
    start = time.perf_counter()
    root, out = Path(root), Path(out)
    if config.get("conditional_ell") != [2]:
        raise ValueError("This protocol supports conditioning on ell=2 only")
    if min(config["n_reference"], config["n_calibration"]) < 1000:
        raise ValueError("Use at least 1,000 spectra per batch for the tail diagnostics")
    if config["lmax"] < 29 or max(config["parity_scan_lmax"]) > config["lmax"]:
        raise ValueError("The analysis band must include all fixed and scanned multipoles")
    out.mkdir(parents=True, exist_ok=True)
    maxell = max(config["sensitivity_lmax"] + [config["lmax"]])
    obs_table, theory_table = load_spectra(root, maxell)
    ell_all = obs_table[:, 0].astype(int)
    obs_all = dl_to_cl(ell_all, obs_table[:, 1])
    theory_all = dl_to_cl(ell_all, theory_table[:, 1])
    streams = np.random.SeedSequence(config["seed"]).spawn(2)
    print("Generating independent reference and calibration ensembles", flush=True)
    ref_all = simulate(ell_all, theory_all, config["n_reference"], np.random.default_rng(streams[0]))
    cal_all = simulate(ell_all, theory_all, config["n_calibration"], np.random.default_rng(streams[1]))
    use = ell_all <= config["lmax"]
    ell, obs, theory = ell_all[use], obs_all[use], theory_all[use]
    ref, cal = ref_all[:, use], cal_all[:, use]
    kernel = s_kernel(ell)
    obs_m, ref_m, cal_m = metrics(ell, obs, kernel), metrics(ell, ref, kernel), metrics(ell, cal, kernel)
    results = {
        "status": "Exploratory spectral proxy; not an end-to-end Planck significance analysis",
        "config": config,
        "statistics": {name: {"observed": float(obs_m[j]), **lower_tail(cal_m[:, j], obs_m[j])}
                       for j, name in enumerate(NAMES)},
        "quadrupole_exact_p": float(chi2.cdf(5 * obs[0] / theory[0], 5)),
        "four_test_family": family_min_p(ref_m, cal_m, obs_m),
        "spearman_correlation": spearmanr(cal_m).statistic.tolist(),
    }
    print("Conditioning on the observed quadrupole", flush=True)
    conditioned = cal.copy()
    conditioned[:, 0] = obs[0]
    cond_m = metrics(ell, conditioned, kernel)
    results["conditioned_on_observed_C2"] = {
        name: lower_tail(cond_m[:, j], obs_m[j]) for j, name in enumerate(NAMES) if j > 0
    }
    # Direct tail co-occurrence; a rectangular event probability is not an omnibus p-value.
    joint = np.all(cal_m <= obs_m, axis=1)
    joint_est = lower_tail(joint.astype(int) * -1, -1)
    results["joint_lower_rectangle"] = {"event_probability": joint_est,
        "product_of_marginal_estimates": float(np.prod([results["statistics"][n]["p"] for n in NAMES])),
        "interpretation": "Probability of all four thresholds simultaneously; NOT a calibrated omnibus p-value"}
    pcal = empirical_p(ref_m, cal_m)
    results["tail_dependence"] = {}
    for q in (.01, .05, .10):
        indicators = pcal <= q
        cooccur = indicators.T.astype(int) @ indicators.astype(int) / len(cal)
        marg = indicators.mean(axis=0)
        ratio = cooccur / np.outer(marg, marg)
        results["tail_dependence"][str(q)] = {"joint_frequencies": cooccur.tolist(),
            "ratio_to_empirical_independence": ratio.tolist(), "marginal_frequencies": marg.tolist()}
    print("Calibrating multipole and angular search penalties", flush=True)
    pscan_ref = np.column_stack([parity(ell, ref, l) for l in config["parity_scan_lmax"]])
    pscan_cal = np.column_stack([parity(ell, cal, l) for l in config["parity_scan_lmax"]])
    pscan_obs = np.array([parity(ell, obs, l) for l in config["parity_scan_lmax"]])
    pscan_p = empirical_p(pscan_ref, pscan_obs)
    results["parity_scan"] = {"lmax": config["parity_scan_lmax"], "observed_ratios": pscan_obs.tolist(),
        "local_reference_p": pscan_p.tolist(), "best_lmax": config["parity_scan_lmax"][int(pscan_p.argmin())],
        "corrected": family_min_p(pscan_ref, pscan_cal, pscan_obs)}
    skernels = [s_kernel(ell, np.cos(np.deg2rad(a))) for a in config["s_scan_angles_deg"]]
    sref = np.column_stack([s_stat(ref, k) for k in skernels])
    scal = np.column_stack([s_stat(cal, k) for k in skernels])
    sobs = np.array([s_stat(obs, k) for k in skernels])
    results["angular_scan"] = {"angles_deg": config["s_scan_angles_deg"],
        "local_reference_p": empirical_p(sref, sobs).tolist(),
        "corrected": family_min_p(sref, scal, sobs)}
    # One finite family includes all four fixed statistics and both explicit scans.
    # Duplicate endpoints do not create independent trials and are harmless in min-p.
    results["all_declared_tests_family"] = family_min_p(
        np.column_stack([ref_m, pscan_ref, sref]),
        np.column_stack([cal_m, pscan_cal, scal]), np.r_[obs_m, pscan_obs, sobs])
    results["sensitivity"] = []
    for lmax in config["sensitivity_lmax"]:
        band = ell_all <= lmax
        k = s_kernel(ell_all[band])
        sob = float(s_stat(obs_all[band], k))
        sc = s_stat(cal_all[:, band], k)
        results["sensitivity"].append({"lmax": lmax, "s_half": sob, **lower_tail(sc, sob)})
    effects = replacement_effects(ell, obs, theory, kernel)
    np.savetxt(out / "multipole_replacement.csv", effects, delimiter=",",
               header="ell,delta_S_half_uK4", comments="", fmt=["%d", "%.12g"])
    np.savetxt(out / "spectrum.csv", np.column_stack([ell_all, obs_all, theory_all]), delimiter=",",
               header="ell,observed_Cl_uK2,theory_Cl_uK2", comments="", fmt=["%d", "%.12g", "%.12g"])
    # Analytic counterfactual optimum in C2 with all other observed multipoles fixed.
    stationary = -float(kernel[0, 1:] @ obs[1:]) / kernel[0, 0]
    results["cancellation_diagnostic"] = {
        "C2_observed": float(obs[0]), "C2_theory": float(theory[0]),
        "C2_minimizing_S_with_other_multipoles_fixed": max(0., stationary),
        "unconstrained_stationary_C2": stationary,
        "derivative_dS_dC2_at_observed": float(2 * (kernel @ obs)[0]),
        "interpretation": "Algebraic counterfactual; neither a new cosmology nor parameter inference"}
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, stderr=subprocess.DEVNULL, text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "uncommitted initial analysis"
    files = sorted((root / "src/cmb_lab").glob("*.py"))
    results["provenance"] = {"created_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(), "git_commit_at_run": commit,
        "packages": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "matplotlib", "requests")},
        "source_sha256": {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in files},
        "input_products": {k: json.loads((root / "data/manifest.json").read_text())[k]
                           for k in ("observed", "theory")},
        "seed_streams": [s.spawn_key for s in streams]}
    np.savez_compressed(out / "simulation_metrics.npz", reference=ref_m, calibration=cal_m,
                        conditional=cond_m, names=NAMES)
    from .plots import make_plots
    make_plots(out, ell, obs, theory, cal, cal_m, cond_m, results, effects, kernel)
    results["elapsed_seconds"] = time.perf_counter() - start
    (out / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    write_summary(out, results)
    print(json.dumps({n: v["p"] for n, v in results["statistics"].items()}, indent=2), flush=True)
    print(f"Results saved to {out}", flush=True)
    return results


def write_summary(out, r):
    lines = ["# Computed results", "", "Generated from the official PR3 TT estimates; all p-values below use an idealized full-sky Gaussian reference. They are not official Planck likelihood results.", "",
             "| Diagnostic | Observed | Lower-tail p | 95% Monte Carlo interval |", "|---|---:|---:|---:|"]
    for name, value in r["statistics"].items():
        lo, hi = value["ci95"]
        lines.append(f"| {name} | {value['observed']:.6g} | {value['p']:.5f} | {lo:.5f} - {hi:.5f} |")
    lines += ["", f"Four-test minimum-p family calibration: **{r['four_test_family']['p']:.5f}**.",
              f"All declared fixed/scan tests: **{r['all_declared_tests_family']['p']:.5f}**.",
              f"Parity cutoff scan (10-29), corrected: **{r['parity_scan']['corrected']['p']:.5f}**.",
              f"Angular threshold scan (45-90 degrees), corrected: **{r['angular_scan']['corrected']['p']:.5f}**.", "",
              "These corrections cover only the declared finite families, not all historical choices or all follow-up diagnostics.", "",
              "## Holding the quadrupole fixed", ""]
    for name, val in r["conditioned_on_observed_C2"].items():
        lines.append(f"- {name}: conditional p = {val['p']:.5f}.")
    lines += ["", "Conditioning is a diagnostic. It removes the probability cost of the low quadrupole, assumes its published estimate is exact, and does not establish a physical cause.", "",
              "## Resolution of the experiment", "", f"Reference spectra: {r['config']['n_reference']:,}; independent calibration spectra: {r['config']['n_calibration']:,}.",
              "The conditional ensemble reuses the calibration skies with C2 replaced. Zero observed events never imply zero probability. See results.json for exact counts, confidence intervals, source hashes, and software versions."]
    (out / "SUMMARY.md").write_text("\n".join(lines) + "\n")


def main():
    p = ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--config", type=Path, default=Path("config/analysis.json"))
    p.add_argument("--output", type=Path, default=Path("results/baseline"))
    p.add_argument("--quick", action="store_true", help="Use 2,000 spectra per batch; writes results/quick by default")
    p.add_argument("--fetch", action="store_true")
    a = p.parse_args()
    config = json.loads((a.root / a.config).read_text())
    if a.quick:
        config.update(n_reference=2000, n_calibration=2000)
        if a.output == Path("results/baseline"):
            a.output = Path("results/quick")
    if a.fetch:
        fetch(a.root)
    run(a.root, config, a.root / a.output)


if __name__ == "__main__":
    main()
