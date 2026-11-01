"""Build matching Markdown and PDF research reports from executed JSON results."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as PILImage
import matplotlib

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results/baseline/results.json").read_text())
OUT = ROOT / "reports"
OUT.mkdir(exist_ok=True)
fontdir = Path(matplotlib.get_data_path()) / "fonts/ttf"
pdfmetrics.registerFont(TTFont("DejaVu", str(fontdir / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuBold", str(fontdir / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVuBold", italic="DejaVu", boldItalic="DejaVuBold")
INK = colors.HexColor("#182f40")
BLUE = colors.HexColor("#287f91")
PALE = colors.HexColor("#edf4f5")
styles = {
    "title": ParagraphStyle("title", fontName="DejaVuBold", fontSize=31, leading=37, textColor=INK, spaceAfter=14),
    "h1": ParagraphStyle("h1", fontName="DejaVuBold", fontSize=20, leading=26, textColor=INK, spaceAfter=13),
    "h2": ParagraphStyle("h2", fontName="DejaVuBold", fontSize=12, leading=17, textColor=BLUE, spaceBefore=12, spaceAfter=7),
    "p": ParagraphStyle("p", fontName="DejaVu", fontSize=9.4, leading=14.3, textColor=INK, spaceAfter=9),
    "small": ParagraphStyle("small", fontName="DejaVu", fontSize=8, leading=11.5, textColor=INK, spaceAfter=7),
    "caption": ParagraphStyle("caption", fontName="DejaVu", fontSize=8, leading=11, textColor=BLUE, spaceAfter=10),
}
story, md = [], []


def text(s, kind="p"):
    story.append(Paragraph(escape(s), styles[kind]))
    prefix = "# " if kind == "title" else "## " if kind == "h1" else "### " if kind == "h2" else ""
    md.extend([prefix + s, ""])


def page(title):
    story.append(PageBreak())
    text(title, "h1")


def figure(relative, caption, maxheight=270):
    p = ROOT / relative
    if not p.exists():
        return
    with PILImage.open(p) as im:
        w, h = im.size
    scale = min(515 / w, maxheight / h)
    story.append(Image(str(p), width=w * scale, height=h * scale))
    story.append(Spacer(1, 5))
    story.append(Paragraph(escape(caption), styles["caption"]))
    md.extend([f"![{caption}](../{relative})", ""])


def table(headers, rows, widths):
    data = [[Paragraph(escape(str(c)), styles["small"]) for c in row] for row in [headers] + rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("LINEBELOW", (0, 0), (-1, 0), .7, BLUE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 1), (-1, -1), .3, colors.HexColor("#dbe3e8"))]))
    story.extend([t, Spacer(1, 10)])
    md.append("| " + " | ".join(headers) + " |")
    md.append("| " + " | ".join(["---"] * len(headers)) + " |")
    md.extend("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
    md.append("")


def pvalue(key):
    return R["statistics"][key]["p"]


text("CMB Anomaly Lab", "title")
text("Five questions about the largest patterns in the oldest light", "h1")
text("Biswajit Jana | Research report v0.1.0 | 1 November 2026", "h2")
text("Numerical analysis and literature search: 31 October 2026.", "small")
text("Original Planck data. Mathematical physics. Reproducible simulation.")
figure("results/maps/planck_temperature.png", "ESA / Planck Collaboration SMICA temperature measurement, displayed with its confidence mask. Grey regions are excluded from the display.", 250)
text("The scientific question", "h2")
text("Planck's familiar all-sky image maps tiny temperature fluctuations in the cosmic microwave background. Some of its largest angular patterns have prompted persistent questions. This project asks whether low quadrupole power, weak large-angle correlations, odd/even imbalance, and low variance provide distinct evidence, or partly reflect the same modes of one observed sky.")
text("Finding and scope", "h2")
text(f"In the spectrum-based Gaussian reference experiment, fixing C2 to its observed value changes the S1/2 lower-tail probability from {pvalue('s_half'):.4f} to {R['conditioned_on_observed_C2']['s_half']['p']:.4f}. This is a reproducible dependence diagnostic, not a new physical explanation. The analysis is exploratory and does not reproduce the full masked-sky Planck inference pipeline.")
text("Authorship: Biswajit Jana. Literature retrieval, coding and drafting assisted by OpenAI Codex. Observations: ESA and the Planck Collaboration; distribution: NASA/IPAC IRSA.", "small")

page("01 / What is actually measured?")
text("The CMB is a nearly uniform thermal radiation field. Its anisotropies carry contributions from intrinsic photon perturbations, gravitational redshift, velocities, and propagation effects. A hot pixel is not a unique measurement of an overdensity; interpretation requires a cosmological transfer model.")
text("Data products", "h2")
text("We use the official PR3 unbinned TT power-spectrum estimates (R3.01), the matching published best-fit TTTEEE + lowl + lowE + lensing theoretical spectrum, and the PR3 SMICA I_STOKES map for visualization. The measured spectrum and theoretical spectrum are distinct inputs. These are processed scientific products, not a fresh reduction of raw detector time streams. [1-4]")
figure("results/baseline/figures/spectrum.png", "The observed low-multipole spectrum and the fixed LCDM reference. The shaded region is a pointwise 95% cosmic-variance envelope, not an observational likelihood confidence region.", 240)
text("Why the comparison is approximate", "h2")
text("The archive point estimates encode foreground cleaning and likelihood choices. Our simulated spectra instead follow an ideal full-sky, noise-free Gaussian distribution. We do not propagate the published spectrum estimator's joint sampling covariance or refit the cosmology. The results are therefore diagnostic reference probabilities. They must not be substituted for Planck's official anomaly significances.")
text("All input URLs, sizes and SHA-256 fingerprints are stored in data/manifest.json. Small spectrum files are versioned; the large FITS map is downloaded on demand. PR3 is used for a stable reproducible starting point, while the literature review includes NPIPE/PR4 work. [11, 12]")

page("02 / The mathematical experiment")
text("Represent the temperature field in spherical harmonics. At each multipole ell, C-ell is the average squared harmonic amplitude. The archive supplies D-ell = ell(ell+1) C-ell / (2 pi), so the code explicitly converts to C-ell.")
text("A Gaussian isotropic null", "h2")
text("For a real, noiseless full sky, (2 ell + 1) times measured C-ell divided by theoretical C-ell follows a chi-square distribution with 2 ell + 1 degrees of freedom. Its variance is 2 C-ell squared / (2 ell + 1). This permits exact power-spectrum simulation without generating a pixel map for every realization.")
table(["Question", "Statistic and fixed choice"], [
    ["Low quadrupole", "C2; lower tail; checked against an exact chi-square CDF"],
    ["Weak correlation", "S1/2 = integral from -1 to 1/2 of C(x)^2 dx; ell 2-64"],
    ["Odd/even imbalance", "Mean even D-ell / mean odd D-ell; ell 2-29"],
    ["Low variance", "Sum of (2 ell+1) C-ell / (4 pi); ell 2-29"],
    ["Independent clues?", "Conditioning, tail co-occurrence and calibrated minimum-p"]], [125, 390])
text("Correlation is reconstructed as C(x) = sum [(2 ell+1) C-ell P-ell(x)] / (4 pi), where x = cos(theta). Its square-integral is a quadratic form C-transpose K C. Gauss-Legendre quadrature with L+1 nodes integrates the degree-2L polynomial exactly up to roundoff. Full equations and derivations are in docs/methods.md.")
text(f"We draw {R['config']['n_reference']:,} reference spectra and {R['config']['n_calibration']:,} independent calibration spectra, using separate seed streams from {R['config']['seed']}. A lower-tail probability is estimated as (k+1)/(N+1). Exact binomial intervals report only Monte Carlo counting uncertainty.")
text("The protocol is retrospective and motivated by the literature. It is not a preregistered search. The quadrupole, correlation and parity statistics have extensive prior art. [5-9]")

page("03 / Results from the published spectrum")
rows = []
labels = {"quadrupole": "C2 [microK^2]", "s_half": "S1/2 [microK^4]", "parity_2_29": "Parity ratio", "variance_2_29": "Variance [microK^2]"}
for k, val in R["statistics"].items():
    rows.append([labels[k], f"{val['observed']:.4f}", f"{val['p']:.5f}", f"{val['ci95'][0]:.5f} - {val['ci95'][1]:.5f}"])
table(["Statistic", "Measured", "Lower-tail p", "95% MC interval"], rows, [135, 110, 105, 165])
figure("results/baseline/figures/null_distributions.png", "Blue: unconditional reference. Dark outlines: the same model conditioned on observed C2. Orange: the measured statistic. Plot ranges omit very remote tails.", 340)
text(f"The exact quadrupole lower-tail probability is {R['quadrupole_exact_p']:.5f}, agreeing with Monte Carlo. The parity ratio is the strongest of the four fixed diagnostics. A p-value is a probability of a statistic under a specified null, not the probability that the null theory is true.")
text("These are not the northern-hemisphere variance or the phase-dependent alignment statistics used in some combined-anomaly papers. Our result cannot validate or refute those combined claims. [14, 15]", "small")

page("04 / How much does the quadrupole explain?")
figure("results/baseline/figures/correlation.png", "Correlation from the released spectrum. Reference bands use 5,000 spectra for display; numerical p-values use all 100,000 calibration spectra. Bands are pointwise, not simultaneous.", 250)
text("The conditional question", "h2")
text("Keep every calibration realization's multipoles above ell=2, but replace its quadrupole by the published observed value. In the ideal Gaussian model, distinct multipoles are independent, so this samples a well-defined conditional ensemble. It asks how unusual the remaining structure looks once C2 is known.")
table(["Statistic", "Unconditional p", "C2 fixed p"], [[labels[k], f"{pvalue(k):.5f}", f"{v['p']:.5f}"] for k, v in R["conditioned_on_observed_C2"].items()], [225, 145, 145])
text("The correlation statistic and variance lose much of their rarity in this conditional experiment. Parity retains a lower-tail preference. This supports shared information in the spectrum-based tests; it does not show that all map anomalies are dependent, and does not explain why C2 is small.")
text("Estimator dependence matters", "h2")
text("Full-sky reconstructed correlations and direct cut-sky correlations are different observables. Prior work finds materially different probabilities for these estimators. The present S1/2 result is not a failed reproduction of the masked-sky result: that observational experiment has not yet been performed here. [5-7]")

page("05 / Paying for the searches we perform")
figure("results/baseline/figures/search_penalties.png", "Local ranks along two explicit searches and independently calibrated scan probabilities. Each corrected line answers the question posed by the entire corresponding scan.", 230)
table(["Declared family", "Calibrated minimum-p probability"], [
    ["Four fixed statistics", f"{R['four_test_family']['p']:.5f}"],
    ["Parity cutoff: every integer 10-29", f"{R['parity_scan']['corrected']['p']:.5f}"],
    ["Angular thresholds: 45-90 deg in 5 deg steps", f"{R['angular_scan']['corrected']['p']:.5f}"],
    ["Four fixed tests plus both scans", f"{R['all_declared_tests_family']['p']:.5f}"]], [320, 195])
text("The reference ensemble defines marginal ranks. Each independent calibration spectrum undergoes the same complete search. The calibration therefore retains dependence among neighboring cutoffs and among the different statistics.")
text("A larger family can produce a smaller corrected result when it also finds a more extreme observed minimum. Corrections should be compared with the minimum of their own family. No multiplication of nominal p-values or assumption of independent diagnostics is needed.")
text("This addresses the declared finite searches, not the unknown historical selection of interesting CMB statistics. It does not settle the 2026 disagreement about combined anomaly significance. Conditioning, cutoff-sensitivity checks and counterfactual diagnostics are exploratory follow-ups, not additional claimed detections. [14, 15]")

page("06 / A concrete cancellation diagnostic")
figure("results/baseline/figures/cancellation.png", "An algebraic intervention on C2, holding all other observed multipoles fixed. The curve is not a cosmological likelihood.", 210)
d = R["cancellation_diagnostic"]
text("Because S = C-transpose K C, its derivative with respect to C2 is twice the quadrupole component of K C. Setting this derivative to zero gives an exact conditional minimum, subject to C2 being nonnegative.")
text(f"For the chosen spectrum and bandlimit, the observed C2 is {d['C2_observed']:.2f} microkelvin squared and the minimizing value is {d['C2_minimizing_S_with_other_multipoles_fixed']:.2f}. The theory mean is {d['C2_theory']:.2f}. Their proximity is a post-result observation with no calibrated significance; measurement uncertainty in C2 is much larger than their difference. It is not a new-physics or fine-tuning claim.")
figure("results/baseline/figures/dependencies.png", "Bulk rank dependence and one-multipole replacement effects. Cross terms mean the replacement effects are not additive. Tail co-occurrence is recorded separately in results.json.", 210)
text("The useful next question is whether a prespecified cancellation diagnostic retains information after propagating map uncertainty and conditioning on both quadrupole and variance. This proposal has unverified novelty; covariance and conditioning already have substantial prior art. [5]", "small")

page("07 / Physics beyond the first experiment")
text("A physical explanation must predict more than a small number. A primordial-power modification changes C-ell through a transfer integral: C-ell = 4 pi integral d ln k P_R(k) Delta_T,ell(k)^2. A viable model must also predict TE and EE and survive parameter-fitting penalties. Directly suppressing selected C-ell values is only a toy model.")
figure("results/maps/simulated_skies.png", "Four separately generated Gaussian LCDM skies. These are explicitly simulated; they are not the observed Planck image or a search over selected extreme skies.", 265)
table(["Candidate explanation", "Necessary discrimination"], [
    ["A chance realization", "Matched estimator and mask simulations"],
    ["Primordial power modification", "Joint TT/TE/EE predictions from transfer physics"],
    ["Foregrounds or processing residuals", "Frequency, mask and cleaning-pipeline tests"],
    ["Topology or anisotropic covariance", "Phase-sensitive tests with orientation penalties"]], [195, 320])
text("A 2024 PR4 study found the modeled local thermal and kinetic Sunyaev-Zeldovich contributions too small to explain the tested anomalies. This does not exclude every foreground mechanism. Other proposals, including causal-coherence interpretations, remain candidates requiring discriminating tests. [12, 13]", "small")

page("08 / Interpretation, validation and next work")
text("The live scientific disagreement", "h2")
text("Jones and collaborators emphasize rare joint tails of four map-based anomaly classes and argue that the anomalies deserve a physical explanation. Guth and Namjoo challenge the significance assigned after test selection and the identification of spectrum anomalies with anisotropy. Their papers motivate explicit search calibration here. Our smaller spectral experiment does not adjudicate their full dispute. [14, 15]")
text("Validation actually performed", "h2")
text("The numerical test suite checks units, Legendre orthogonality, independent adaptive integration, cosmic-variance moments, the exact quadrupole distribution, parity normalization, edge probabilities, independent-family calibration, duplicate-test behavior, batch consistency, and the stationary-point derivation. The production run uses fixed seeds, input hashes, software versions and source fingerprints. Bandlimit checks from 32 to 128 keep S1/2 probabilities close to 0.075.")
text("Material limits", "h2")
text("The null omits observational mask coupling, foregrounds, instrument noise, estimator covariance and cosmological-parameter uncertainty. Conditioning uses an exact plug-in C2 estimate. Temperature spectra omit phases; rotationally invariant power deficits cannot alone establish a preferred direction. Binomial intervals are not a complete uncertainty budget. The same sky observed by several instruments is not several independent cosmic samples.")
text("Next experiment", "h2")
text("Freeze a map-and-mask estimator; process data and simulations through identical harmonic smoothing, pixel windows, masking and monopole/dipole removal; check closure; compare multiple component-separation products and PR4 simulations; and then formulate polarization predictions with the joint TT/TE/EE covariance. The present version includes a map download and renderer, not a validated masked-sky inference pipeline.")
text("Reproduce the run", "h2")
text("Install the package with the dev and report extras, run scripts/download_data.py, run pytest, then run cmb-lab. Rebuild this document with scripts/build_report.py. Use the maps extra and render_planck_map.py for the measured-sky figure. README.md contains complete commands, and requirements-lock.txt records the executed environment.")
text("Repository: https://github.com/Biswajit1999/cmb-anomaly-lab", "small")

page("References and research provenance")
text("A focused reading guide with reading-depth labels, caveats and primary-source links is provided in docs/literature-review.md. The following references anchor this report; inclusion is not endorsement of every interpretation.")
refs = [
 ("Planck Collaboration. Planck 2018 results VII: Isotropy and Statistics (2020)", "https://arxiv.org/abs/1906.02552"),
 ("Planck Collaboration. Planck 2018 results V: Power spectra and likelihoods (2020)", "https://arxiv.org/abs/1907.12875"),
 ("Planck Collaboration. Planck 2018 results IV: Diffuse component separation (2020)", "https://arxiv.org/abs/1807.06208"),
 ("Planck Collaboration. Planck 2018 results VI: Cosmological parameters (2020)", "https://arxiv.org/abs/1807.06209"),
 ("Muir, Adhikari and Huterer. Covariance of CMB anomalies (2018)", "https://arxiv.org/abs/1806.02354"),
 ("Efstathiou, Ma and Hanson. Large-Angle Correlations (2010)", "https://arxiv.org/abs/0911.5399"),
 ("Copi et al. Lack of large-angle TT correlations persists (2015)", "https://arxiv.org/abs/1310.3831"),
 ("Schwarz et al. CMB Anomalies after Planck (2016)", "https://arxiv.org/abs/1510.07929"),
 ("Copi et al. Large-angle anomalies in the CMB (2010)", "https://arxiv.org/abs/1004.5602"),
 ("Copi et al. Large-scale alignments from WMAP and Planck (2015)", "https://arxiv.org/abs/1311.4562"),
 ("Planck Collaboration. Intermediate results LVII: NPIPE (2020)", "https://arxiv.org/abs/2007.04997"),
 ("Jung et al. Revisiting large-scale anomalies: local SZ contributions (2024)", "https://arxiv.org/abs/2406.11543"),
 ("Hogan et al. Dipole-independent nearly-zero CMB correlation (2025)", "https://arxiv.org/abs/2312.16147v7"),
 ("Jones et al. Strong Evidence Against a Statistically Isotropic Universe (2026 revision)", "https://arxiv.org/abs/2310.12859v3"),
 ("Guth and Namjoo. Statistical isotropy and the look-elsewhere effect (2026)", "https://arxiv.org/abs/2602.10178v2"),
 ("Gorski et al. HEALPix (2005)", "https://arxiv.org/abs/astro-ph/0409513"),
]
for i, (label, url) in enumerate(refs, 1):
    story.append(Paragraph(f'{i}. {escape(label)}. <link href="{url}" color="#287f91">Primary paper</link>', styles["small"]))
    md.extend([f"{i}. [{label}]({url})", ""])
text("Data: NASA/IPAC IRSA Planck PR3 ancillary products and CMB maps. Credit ESA and the Planck Collaboration. Some visualization results use healpy and HEALPix. Original software and prose: MIT license, copyright 2026 Biswajit Jana. Third-party data retain their source terms.", "small")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#dbe3e8"))
    canvas.line(40, 37, 555, 37)
    canvas.setFont("DejaVu", 7)
    canvas.setFillColor(INK)
    canvas.drawString(40, 24, "BISWAJIT JANA  /  CMB ANOMALY LAB  /  EXPLORATORY RESEARCH")
    canvas.drawRightString(555, 24, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT / "cmb-anomaly-lab.pdf"), pagesize=(595, 842),
    leftMargin=40, rightMargin=40, topMargin=43, bottomMargin=53,
    title="CMB Anomaly Lab", author="Biswajit Jana", subject="Planck large-angle temperature experiments")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / "research-report.md").write_text("\n".join(md), encoding="utf-8")
print(f"Built {OUT / 'cmb-anomaly-lab.pdf'} and matching Markdown")
