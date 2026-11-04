"""Publication-style plots generated only from measured or simulated arrays."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401; registers the scientific styles
import numpy as np
from .statistics import NAMES, correlation_matrix, s_stat

INK, BLUE, RED = "#182f40", "#287f91", "#bf593d"


def style():
    plt.style.use(["science", "no-latex", "bright"])
    plt.rcParams.update({"font.family": "serif", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.labelcolor": INK, "text.color": INK, "axes.titleweight": "bold",
        "figure.facecolor": "white", "savefig.facecolor": "white", "savefig.dpi": 240,
        "pdf.fonttype": 42, "ps.fonttype": 42})


def save(fig, folder, name):
    fig.savefig(folder / f"{name}.png", bbox_inches="tight")
    fig.savefig(folder / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def make_plots(out, ell, obs, theory, cal, cal_m, cond_m, r, effects, kernel):
    style()
    folder = out / "figures"
    folder.mkdir(exist_ok=True)
    factor = ell * (ell + 1) / (2 * np.pi)
    fig, ax = plt.subplots(figsize=(9, 4.3), layout="constrained")
    low, high = np.quantile(cal * factor, [.025, .975], axis=0)
    ax.fill_between(ell, low, high, color=BLUE, alpha=.17, label="95% full-sky cosmic variance (pointwise)")
    ax.plot(ell, theory * factor, c=BLUE, label="Planck best-fit LCDM")
    ax.plot(ell, obs * factor, ".-", c=RED, ms=4, lw=.8, label="Published PR3 TT estimates")
    ax.set(xlabel=r"Multipole $\ell$", ylabel=r"$D_\ell$ [$\mu$K$^2$]", title="Large angular scales: one sky, wide cosmic variance", xlim=(2, ell[-1]))
    ax.legend(fontsize=8)
    save(fig, folder, "spectrum")

    theta = np.linspace(0, 180, 361)
    matrix = correlation_matrix(ell, np.cos(np.deg2rad(theta)))
    # Subset only for pointwise visualization; statistics use the full batch.
    curves = cal[:5000] @ matrix.T
    q = np.quantile(curves, [.025, .16, .84, .975], axis=0)
    fig, ax = plt.subplots(figsize=(9, 4.3), layout="constrained")
    ax.fill_between(theta, q[0], q[3], color=BLUE, alpha=.12, label="95% pointwise reference band")
    ax.fill_between(theta, q[1], q[2], color=BLUE, alpha=.20, label="68% pointwise reference band")
    ax.plot(theta, matrix @ theory, c=BLUE, label="Theory mean")
    ax.plot(theta, matrix @ obs, c=RED, label="From published TT spectrum")
    ax.axhline(0, color=INK, lw=.5)
    ax.axvline(60, ls="--", c=INK, lw=.7)
    ax.set(xlabel="Angular separation [degrees]", ylabel=r"$C(\theta)$ [$\mu$K$^2$]", title=rf"Correlation reconstructed from the spectrum ($2\leq\ell\leq{ell[-1]}$)", xlim=(0, 180))
    ax.legend(fontsize=8, loc="upper right")
    save(fig, folder, "correlation")

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), layout="constrained")
    labels = [r"$C_2$ [$\mu$K$^2$]", r"$S_{1/2}$ [$\mu$K$^4$]", r"$R^{TT}_{2:29}$", r"$V_{2:29}$ [$\mu$K$^2$]"]
    for j, ax in enumerate(axes.flat):
        vals = cal_m[:, j]
        lo, hi = np.quantile(vals, [.0005, .995])
        bins = np.geomspace(lo, hi, 65) if j == 1 else np.linspace(lo, hi, 65)
        ax.hist(vals, bins=bins, density=True, color=BLUE, alpha=.65, label="Unconditional")
        if j > 0:
            ax.hist(cond_m[:, j], bins=bins, density=True, histtype="step", color=INK, label="C2 fixed to observed")
        ax.axvline(r["statistics"][NAMES[j]]["observed"], color=RED, lw=1.8, label="Observed")
        if j == 1:
            ax.set_xscale("log")
        ax.set(xlabel=labels[j], ylabel="Probability density", title=f"Lower-tail p = {r['statistics'][NAMES[j]]['p']:.4f}")
        ax.legend(fontsize=7)
    save(fig, folder, "null_distributions")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.1), layout="constrained")
    scans = [(r["parity_scan"], "lmax", "Parity upper multipole"), (r["angular_scan"], "angles_deg", "Minimum separation [degrees]")]
    for ax, (scan, key, label) in zip(axes, scans):
        ax.plot(scan[key], scan["local_reference_p"], "o-", color=RED, ms=3, label="Local lower-tail rank")
        ax.axhline(scan["corrected"]["p"], color=BLUE, ls="--", label="Scan-corrected p")
        ax.set(yscale="log", xlabel=label, ylabel="p", title="Selection changes the question")
        ax.legend(fontsize=8)
    save(fig, folder, "search_penalties")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.3), layout="constrained")
    corr = np.asarray(r["spearman_correlation"])
    im = axes[0].imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    short = ["C2", "S1/2", "Parity", "Variance"]
    axes[0].set_xticks(range(4), short, rotation=30)
    axes[0].set_yticks(range(4), short)
    axes[0].set_title("Bulk rank correlations")
    for i in range(4):
        for j in range(4):
            axes[0].text(j, i, f"{corr[i,j]:.2f}", ha="center", va="center", color="white" if abs(corr[i,j]) > .6 else INK)
    fig.colorbar(im, ax=axes[0], fraction=.046)
    idx = np.argsort(np.abs(effects[:, 1]))[-10:]
    axes[1].barh([str(int(x)) for x in effects[idx, 0]], effects[idx, 1], color=BLUE)
    axes[1].axvline(0, color=INK, lw=.5)
    axes[1].set(xlabel=r"Change in $S_{1/2}$ [$\mu$K$^4$]", ylabel="Replaced multipole", title="One-at-a-time theory replacement")
    save(fig, folder, "dependencies")

    c2 = np.linspace(0, 2 * theory[0], 400)
    changed = np.tile(obs, (len(c2), 1))
    changed[:, 0] = c2
    fig, ax = plt.subplots(figsize=(9, 4), layout="constrained")
    ax.plot(c2, s_stat(changed, kernel), c=BLUE)
    ax.axvline(obs[0], c=RED, label="Observed C2")
    ax.axvline(theory[0], c=INK, ls="--", label="Theory C2")
    ax.set(xlabel=r"Counterfactual $C_2$ [$\mu$K$^2$]", ylabel=r"$S_{1/2}$ [$\mu$K$^4$]", title="Cancellation diagnostic: all other measured multipoles held fixed")
    ax.legend()
    save(fig, folder, "cancellation")
