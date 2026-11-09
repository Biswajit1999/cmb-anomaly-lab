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
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cmb_lab.plots import style

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results/baseline/results.json").read_text())
M = json.loads((ROOT / "results/masked_sky/results.json").read_text())
P = json.loads((ROOT / "results/primordial/results.json").read_text())
V = json.loads((ROOT / "results/extension_validation.json").read_text())
C = json.loads((ROOT / "results/conditional/results.json").read_text())
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
style()
equation_count = 0


def equation(latex):
    global equation_count
    latex = re.sub(r'\\(mathsf|mathcal|mathbf|mathbb) ([A-Za-z])', r'\\\1{\2}', latex)
    equation_count += 1
    folder = ROOT / 'reports/equations'
    folder.mkdir(exist_ok=True)
    fig = plt.figure(figsize=(7.1,.55))
    fig.text(.5,.5,'$'+latex+'$',ha='center',va='center',fontsize=14)
    path = folder / f'equation_{equation_count:02d}.png'
    fig.savefig(path,dpi=300,bbox_inches='tight',pad_inches=.1)
    plt.close(fig)
    with PILImage.open(path) as im:
        w,h=im.size
    scale=min(500/w,42/h)
    story.extend([Image(str(path),width=w*scale,height=h*scale),Spacer(1,9)])
    md.extend(['$$',latex,'$$',''])


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
text("Biswajit Jana | Research report v0.3.0 | 9 November 2026", "h2")
text("Spectra, measured skies, transfer physics and conditional morphology experiments.", "small")
text("Original Planck data. Mathematical physics. Reproducible simulation.")
figure("results/maps/planck_fullsky.png", "ESA / Planck Collaboration SMICA measurements, rendered in a blue-orange palette by Biswajit Jana. Unmasked display; the statistical analysis uses a confidence mask.", 250)
text("The scientific question", "h2")
text("Planck's familiar all-sky image maps tiny temperature fluctuations in the cosmic microwave background. Some of its largest angular patterns have prompted persistent questions. This project asks whether low quadrupole power, weak large-angle correlations, odd/even imbalance, and low variance provide distinct evidence, or partly reflect the same modes of one observed sky.")
text("Finding and scope", "h2")
text(f"Conditioning on C2 changes the spectral S1/2 probability from {pvalue('s_half'):.4f} to {R['conditioned_on_observed_C2']['s_half']['p']:.4f}. A separate matched map experiment measures cut-sky correlation and directional variance. A primordial-suppression fit gives search-calibrated p = {P['search_calibrated_p']['p']:.3f}. These experiments quantify anomalies and model performance without establishing new physics.")
text("Authorship: Biswajit Jana. Literature retrieval, coding and drafting assisted by OpenAI Codex. Observations: ESA and the Planck Collaboration; distribution: NASA/IPAC IRSA.", "small")

page("01 / What is actually measured?")
text("The CMB is a nearly uniform thermal radiation field. Its anisotropies carry contributions from intrinsic photon perturbations, gravitational redshift, velocities, and propagation effects. A hot pixel is not a unique measurement of an overdensity; interpretation requires a cosmological transfer model.")
text("Data products", "h2")
text("We use official PR3 unbinned TT power-spectrum estimates (R3.01), the published best-fit TTTEEE + lowl + lowE + lensing theory, and the PR3 SMICA I_STOKES map with its temperature confidence mask. The spectrum and map experiments use distinct estimators. These are processed scientific products, not a new reduction of raw detector time streams. [1-4]")
figure("results/baseline/figures/spectrum.png", "The observed low-multipole spectrum and the fixed LCDM reference. The shaded region is a pointwise 95% cosmic-variance envelope, not an observational likelihood confidence region.", 240)
text("Why the comparison is approximate", "h2")
text("The archive point estimates encode foreground cleaning and likelihood choices. Our simulated spectra instead follow an ideal full-sky, noise-free Gaussian distribution. We do not propagate the published spectrum estimator's joint sampling covariance or refit the cosmology. The results are therefore diagnostic reference probabilities. They must not be substituted for Planck's official anomaly significances.")
text("All input URLs, sizes and SHA-256 fingerprints are stored in data/manifest.json. Small spectrum files are versioned; the large FITS map is downloaded on demand. PR3 is used for a stable reproducible starting point, while the literature review includes NPIPE/PR4 work. [11, 12]")

page("02 / The mathematical experiment")
text("Represent the temperature field in spherical harmonics. At each multipole ell, C-ell is the average squared harmonic amplitude. The archive supplies D-ell = ell(ell+1) C-ell / (2 pi), so the code explicitly converts to C-ell.")
equation(r'T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n),\qquad \widehat C_\ell=\frac{1}{2\ell+1}\sum_m|a_{\ell m}|^2')
text("A Gaussian isotropic null", "h2")
text("For a real, noiseless full sky, (2 ell + 1) times measured C-ell divided by theoretical C-ell follows a chi-square distribution with 2 ell + 1 degrees of freedom. Its variance is 2 C-ell squared / (2 ell + 1). This permits exact power-spectrum simulation without generating a pixel map for every realization.")
equation(r'\frac{(2\ell+1)\widehat C_\ell}{C_\ell}\sim\chi^2_{2\ell+1},\qquad {\rm Var}(\widehat C_\ell)=\frac{2C_\ell^2}{2\ell+1}')
table(["Question", "Statistic and fixed choice"], [
    ["Low quadrupole", "C2; lower tail; checked against an exact chi-square CDF"],
    ["Weak correlation", "S1/2 = integral from -1 to 1/2 of C(x)^2 dx; ell 2-64"],
    ["Odd/even imbalance", "Mean even D-ell / mean odd D-ell; ell 2-29"],
    ["Low variance", "Sum of (2 ell+1) C-ell / (4 pi); ell 2-29"],
    ["Independent clues?", "Conditioning, tail co-occurrence and calibrated minimum-p"]], [125, 390])
text("Correlation is reconstructed as C(x) = sum [(2 ell+1) C-ell P-ell(x)] / (4 pi), where x = cos(theta). Its square-integral is a quadratic form C-transpose K C. Gauss-Legendre quadrature with L+1 nodes integrates the degree-2L polynomial exactly up to roundoff. Full equations and derivations are in docs/methods.md.")
equation(r'S_{1/2}=\int_{-1}^{1/2} C(x)^2\,dx=\mathbf{C}^{\mathsf T}K\mathbf{C}')
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
text("Full-sky reconstructed correlations and cut-sky correlations are different observables. Prior work finds materially different probabilities for these estimators. Sections 09-11 now measure a finite-band cut-sky estimator from SMICA and calibrate it with matched Gaussian maps. Its mask, projection and smoothing remain distinct from official Planck analyses. [5-7]")

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

page("08 / Interpretation and validation")
text("The live scientific disagreement", "h2")
text("Jones and collaborators emphasize rare joint tails of four map-based anomaly classes and argue that the anomalies deserve a physical explanation. Guth and Namjoo challenge the significance assigned after test selection and the identification of spectrum anomalies with anisotropy. Their papers motivate explicit search calibration here. Our smaller spectral experiment does not adjudicate their full dispute. [14, 15]")
text("Validation actually performed", "h2")
text("The 28 numerical tests cover units, integration, cosmic-variance moments, quadrupole probabilities, parity, tail calibration, batch consistency, cancellation derivatives, nuisance projection, pixel-pair powers, dense covariance, primordial limits, likelihood algebra, conditional EE, fixed-power moments, Haar isotropy, rotation conservation, simultaneous coverage and injection response. Production runs record seeds, hashes and software versions. Independent checks include 100,000 additional spectra, 2,048 baseline maps and the held-out sets in the conditional extension.")
text("Material limits", "h2")
text("The spectral null omits mask coupling; the new map null explicitly includes the selected mask and projection. Both omit foreground/noise realizations and cosmological-parameter uncertainty. Conditioning uses an exact plug-in C2 estimate. A spectral power deficit alone does not imply a preferred direction. Binomial intervals are not a complete uncertainty budget. Different instruments observe the same cosmic sample.")
text("Completed extensions", "h2")
text("The following sections report an executed map-and-mask experiment, analytic variance closure, a calibrated hemisphere-direction search, processing sensitivity, and a primordial model propagated through CAMB. Noise/foreground end-to-end simulations and an observed polarization likelihood remain outside this defined study; the polarization curves are explicit model predictions.")
text("Reproduce the run", "h2")
text("Install the package with the dev and report extras, run scripts/download_data.py, run pytest, then run cmb-lab. Rebuild this document with scripts/build_report.py. Use the maps extra and render_planck_map.py for the measured-sky figure. README.md contains complete commands, and requirements-lock.txt records the executed environment.")
text("Repository: https://github.com/Biswajit1999/cmb-anomaly-lab", "small")
text("Website: https://biswajit1999.github.io/cmb-anomaly-lab/ . The project notebook contains 19 executed code cells with real-data outputs and is ready to open in Google Colab. Saved execution occurred in a local Python kernel.", "small")

page("09 / From native pixels to a matched experiment")
text("We verify the original 2.01 GB SMICA FITS file against its recorded SHA-256 hash. Its nested pixels are converted to ring ordering. Harmonics through ell=128 are extracted at native NSIDE=2048 before smoothing or resolution reduction. Temperature is converted from K_CMB to microkelvin.")
equation(r'a^{\rm out}_{\ell m}=a^{\rm in}_{\ell m}\frac{b^{\rm out}_\ell p^{\rm out}_\ell}{b^{\rm in}_\ell p^{\rm in}_\ell},\qquad b_\ell=e^{-\ell(\ell+1)\sigma_b^2/2}')
text("We adopt the 5 arcmin Gaussian SMICA temperature beam and HEALPix pixel windows. The baseline analysis uses a 5 degree output beam and NSIDE=32; native mask fractions must be at least 0.95. A full-sky low-order subtraction followed by the cut-sky fit removes arbitrary monopole and dipole. The second operation is applied identically to every simulation. Smoothing can spread residual foregrounds beyond the mask, which this CMB-only null does not model.")
equation(r'\mathbf r=P\mathbf t,\qquad P=I-X(X^{\mathsf T}X)^{-1}X^{\mathsf T},\qquad X=(1,n_x,n_y,n_z)')
text("Here t and X contain only retained pixels. P is an orthogonal projection; masking inserts zero outside that sky after fitting. The Gaussian simulations have independent real m=0 modes and complex m>0 modes with the correct variance. Every sky receives the output beam, pixel window, mask and projection.")
figure("results/masked_sky/figures/analysis_sky.png", "The measured sky actually used for map statistics. Grey pixels are excluded; Galactic coordinates. This is separate from the high-resolution display on the cover.", 230)
text(f"Reference maps: {M['config']['n_reference']:,}. Independent calibration maps: {M['config']['n_calibration']:,}. Baseline retained sky: {100*M['variants']['baseline']['f_sky']:.2f}%. Each map is analysed under three declared processing variants.", "small")

page("10 / The cut-sky correlation measurement")
equation(r'\widehat C_W(x)=\frac{\sum_{\ell=0}^{L}(2\ell+1)\widetilde C_\ell P_\ell(x)}{\sum_{\ell=0}^{L}(2\ell+1)W_\ell P_\ell(x)},\qquad S^W_{1/2}=\int_{-1}^{1/2}\widehat C_W(x)^2 dx')
text("The numerator is the pseudo-spectrum of masked, projected temperatures; W-ell is the spectrum of the binary mask. We use L=95 and 192 Gauss-Legendre nodes. This is a finite-band pair-normalized correlation estimator. A hard mask creates higher harmonics, so it is not an exact all-pairs estimator at infinite resolution. No pseudo-spectrum is identified with an unbiased full-sky spectrum.")
figure("results/masked_sky/figures/cut_sky_correlation.png", "Measured cut-sky correlation and pointwise Gaussian ranges using the identical estimator. The projection is included in the simulations; the shaded envelope is not a simultaneous confidence region.", 250)
mb=M['variants']['baseline']
map_labels={'cut_sky_s_half':'Cut-sky S1/2 [microK^4]','masked_variance':'Masked variance [microK^2]','pseudo_parity':'Masked pseudo-parity','hemisphere_max_contrast':'Maximum hemisphere contrast'}
table(['Diagnostic','Measured','Tail p','95% MC interval'],[[map_labels[k],f"{v['observed']:.4g}",f"{v['p']:.5f}",f"{v['ci95'][0]:.5f} - {v['ci95'][1]:.5f}"] for k,v in mb['statistics'].items()],[190,80,75,170])
text("The first three tails are lower; the hemisphere-contrast tail is upper. These probabilities describe the defined CMB-only null. Foreground residuals, instrument noise and cleaning uncertainty are not integrated out.","small")

page("11 / Direction searches, robustness and closure")
equation(r'A_{\max}=\max_{\hat d\in\mathcal D}\frac{|V_+(\hat d)-V_-(\hat d)|}{V_+(\hat d)+V_-(\hat d)}')
text("D contains 24 unoriented HEALPix axes. Each hemisphere variance is computed about its own mean after the global cut-sky projection. Every simulated map repeats all directions before taking the maximum. The reported p therefore pays for this finite direction search. It does not cover every possible local-disc or multipole selection.")
figure("results/masked_sky/figures/map_robustness.png", "Baseline, stricter 0.99 mask threshold, and 8 degree smoothing. Each variant is processed on the same skies; intervals quantify Monte Carlo counting uncertainty.", 220)
text(f"The baseline four-diagnostic family gives p = {mb['family']['p']:.5f}; the twelve columns spanning all three variants give p = {M['all_variants_family']['p']:.5f}. These are within-experiment calibrations, not a single global correction for the entire research project.")
equation(r'\langle V_W\rangle=C(0)-\frac{1}{N_W}{\rm tr}\!\left[(X^{\mathsf T}X)^{-1}X^{\mathsf T}\Sigma X\right]')
text(f"The analytic projected-variance mean is {mb['variance_closure']['analytic']:.3f} microkelvin squared; simulations give {mb['variance_closure']['simulation_mean']:.3f}, a difference of {mb['variance_closure']['standard_errors']:.2f} Monte Carlo standard errors. Doubling integration nodes changes measured S by {mb['quadrature_relative_change']:.2g} fractionally. Independent tests also compare harmonic powers to explicit pixel pairs and the variance formula to a dense covariance matrix.")
text(f"An independent 2,048-map seed reproduces the four local tails within {max(x['difference_in_combined_mc_sd'] for x in V['checks'].values()):.2f} combined Monte Carlo standard deviations. Changing correlation L=95 to 64 changes measured S by {100*abs(V['numerical_convergence']['L64_relative_to_L95']['cut_sky_s_half']):.4f}%; refining quadrature pixels to NSIDE=64 at fixed smoothed sky and mask footprint changes it by {100*abs(V['numerical_convergence']['Nside64_quadrature_relative_to_Nside32']['cut_sky_s_half']):.3f}%.","small")

page("12 / A primordial hypothesis with transfer physics")
text("We test a nonnegative long-wavelength suppression family. It describes a possible primordial power shape; it is not derived here from a specific inflationary potential. Low-power primordial mechanisms have a long literature, so this ansatz is not presented as a new discovery. [17, 18]")
equation(r'\mathcal P_{\mathcal R}(k)=A_s\left(\frac{k}{k_*}\right)^{n_s-1}\left[1-Ae^{-(k/k_c)^2}\right],\qquad 0\leq A\leq1')
equation(r'C_\ell^{XY}=4\pi\int d\ln k\;\mathcal P_{\mathcal R}(k)\Delta_\ell^X(k)\Delta_\ell^Y(k),\qquad X,Y\in\{T,E\}')
text("CAMB computes linear scalar transfer functions at a fixed near-Planck background cosmology. We propagate the modified primordial spectrum through TT, TE and EE. Unlensed scalar spectra depend linearly on primordial power, allowing exact amplitude interpolation within this transfer calculation. The fit uses the published TT point estimates over ell=2-29.")
table(['Quantity','Fixed value or search'],[['H0; physical baryon/CDM densities','67.36 km/s/Mpc; 0.02237; 0.12000'],['tau; ns; As','0.0544; 0.9649; 2.10e-9'],['Neutrinos; curvature','0.06 eV; spatially flat'],['Amplitude A','0 to 1 in steps of 0.1'],['Cutoff kc','16 log-spaced values: 3e-5 to 8e-4 Mpc^-1']],[190,325])
text(f"The computed baseline TT differs from the official best-fit TT by at most {100*P['baseline_max_fractional_TT_difference_from_official_ell2_29']:.2f}% over the fit range. This quantifies the distinction between our fixed background/unlensed calculation and the archived best fit. We do not silently treat them as identical.")

page("13 / Does the alternative earn its extra freedom?")
equation(r'2\Delta\ln\mathcal L=\sum_\ell(2\ell+1)\left[\ln\frac{C^0_\ell}{C_\ell}+\widehat C_\ell\left(\frac{1}{C^0_\ell}-\frac{1}{C_\ell}\right)\right]')
text("This likelihood expression is exact for ideal full-sky Gaussian temperature powers. On published Planck point estimates it is a likelihood proxy. We maximize it over all 161 distinct models, including the null, and repeat the same fit on 100,000 baseline simulated spectra. Monte Carlo calibration handles the amplitude boundary and unidentified cutoff at zero amplitude without assuming a chi-square likelihood-ratio law.")
figure("results/primordial/figures/primordial_search.png", "Left: fit improvement across the declared model grid. Right: distribution of the best improvement under the null, with the same parameter search repeated for each simulated spectrum.", 250)
text(f"The grid optimum is A = {P['best_amplitude']:.2f}, kc = {P['best_cutoff_mpc_inverse']:.3g} Mpc^-1. Its improvement is only 2 Delta ln L = {P['best_twice_log_likelihood_improvement']:.3f}; the calibrated probability is {P['search_calibrated_p']['p']:.4f} (95% MC interval {P['search_calibrated_p']['ci95'][0]:.4f}-{P['search_calibrated_p']['ci95'][1]:.4f}). This experiment provides no compelling preference for this suppression model.")
text(f"Doubling CAMB accuracy changes the fitted model's improvement by {P['accuracy_check']['improvement_absolute_difference']:.4g} and TT power by at most {100*P['accuracy_check']['max_TT_fractional_change_ell2_29']:.3f}%. The amplitude optimum lies at the grid boundary; it is not a parameter measurement or confidence interval. The calculation is not Bayesian evidence and does not refit background parameters.")

page("14 / Polarization as a discriminating prediction")
equation(r'a^E_{\ell m}\mid a^T_{\ell m}\sim\mathcal N\!\left(\frac{C_\ell^{TE}}{C_\ell^{TT}}a^T_{\ell m},\ C_\ell^{EE}-\frac{(C_\ell^{TE})^2}{C_\ell^{TT}}\right)')
text("The expression is understood for the independent real harmonic degrees of freedom. Temperature and E-mode polarization are correlated, so a polarization prediction conditioned on the observed temperature is more appropriate than pretending that TT and EE are independent tests.")
equation(r'\mathbb E[\widehat C_\ell^{EE}\mid\widehat C_\ell^{TT}]=C_\ell^{EE}-\frac{(C_\ell^{TE})^2}{C_\ell^{TT}}+\left(\frac{C_\ell^{TE}}{C_\ell^{TT}}\right)^2\widehat C_\ell^{TT}')
figure("results/primordial/figures/transfer_predictions.png", "TT data and model predictions. EE and TE are unmeasured predictions in this project. Dashed EE curves condition on the published TT power treated as exact; no polarization significance is claimed.", 210)
text("A model that merely reduces TT must also accept the TE and EE consequences of the same primordial spectrum. The CSV export supplies both unconditional and temperature-conditioned EE predictions. An observational polarization test requires masks, correlated noise and foreground uncertainties, which are not contained in these theoretical curves.")
text("Scientific conclusion", "h2")
text("The completed study demonstrates estimator-dependent large-angle rarity, shared low-multipole information, and a weak fit gain for one explicit primordial alternative. It establishes reproducible numerical results under stated models. It does not establish a physical origin for the anomalies or resolve the full cosmological debate. Independent review and realistic observational likelihoods are required for stronger conclusions.")

page("15 / Separate power, morphology and orientation")
text("The new experiment asks what drives a masked-sky anomaly after conditioning on different information from the same map. We retain the existing four diagnostics and processing: ell <= 128, 5 degree beam, NSIDE 32, 0.95 mask fraction, retained-pixel monopole/dipole removal and the complete 24-axis hemisphere search. Estimator dependence and modulation-based sensitivity tests have an established literature. [1, 6, 21]")
table(['Ensemble','Held fixed','Randomized'],[['Gaussian theory','Theoretical spectrum','Powers and harmonic directions'],['Measured powers fixed','Every measured full-sky C-ell','Independent real harmonic directions'],['Measured pattern rotated','Entire pattern and relative geometry','One global Haar-uniform rotation']],[140,190,185])
equation(r'\mathbf{u}_\ell^*=\sqrt{(2\ell+1)\widehat C_\ell}\,\frac{\mathbf{z}_\ell}{\|\mathbf{z}_\ell\|},\qquad\mathbf{z}_\ell\sim\mathcal{N}(0,I)')
text("For the conditional Gaussian model, the 2 ell+1 independent real harmonic coefficients form a uniform direction on a sphere of fixed radius. The m>0 real and imaginary components carry a square-root-of-two weight. Normalizing a Gaussian draw randomizes relative amplitudes and phases, while exactly preserving its specified power. Random complex phases alone would be a different ensemble.")
equation(r'a_{\ell m}^R=\sum_{m^\prime}D^\ell_{mm^\prime}(R)a_{\ell m^\prime},\qquad d\mu(R)=\frac{d\alpha\,d\gamma\,d(\cos\beta)}{8\pi^2}')
text("Global rotations use Wigner matrices on the harmonics, with uniform azimuths and uniform cos(beta). This avoids pixel interpolation and preserves inter-multipole geometry. The fixed mask and finite axis grid do not rotate. These conditional hypotheses answer different questions; their probabilities are not pooled, multiplied or searched for the smallest discovery claim.")
text("Observational limitation", "h2")
text("Both conditional ensembles use the processed full-sky SMICA harmonics, including uncertain Galactic regions. Global harmonic filtering before masking can mix information across mask boundaries. These procedures do not remove foreground-cleaning uncertainty and are not estimates based only on uncontaminated raw pixels. Realistic noise and cosmological-parameter uncertainty remain omitted.")

page("16 / Executed conditional comparisons")
text("Each ensemble contains 1,024 reference skies, 4,096 calibration skies and 1,024 held-out validation skies: 18,432 realizations in total. Separate seeded streams prevent reuse between the three hypotheses. Source hashes, package versions, the conditioning spectrum and every diagnostic value are exported.")
figure('results/conditional/figures/conditional_tails.png','Three distinct null hypotheses. Bars are exact 95% binomial counting intervals for local one-sided tails; they do not represent observational systematic uncertainty.',245)
labels={'gaussian':'Gaussian theory','fixed_power':'Powers fixed','rotation':'Pattern rotated'}
table(['Ensemble','S lower','Variance lower','Parity lower','Hemisphere upper'],[[labels[n]]+[f"{e['statistics'][k]['p']:.4f}" for k in ['cut_sky_s_half','masked_variance','pseudo_parity','hemisphere_max_contrast']] for n,e in C['ensembles'].items()],[135,90,100,90,100])
g=C['ensembles']['gaussian']; f=C['ensembles']['fixed_power']; rot=C['ensembles']['rotation']
text(f"The measured cut-sky S is compared with Gaussian theory at p = {g['statistics']['cut_sky_s_half']['p']:.4f}, with measured powers fixed at p = {f['statistics']['cut_sky_s_half']['p']:.4f}, and with the measured pattern rotated at p = {rot['statistics']['cut_sky_s_half']['p']:.4f}. These values quantify different conditional questions; the latter two are not corrections to the former.")
text('Four-diagnostic family probabilities: '+', '.join(f"{labels[n]} {e['four_diagnostic_family']['p']:.4f}" for n,e in C['ensembles'].items())+'. The family covers four statistics within each null only; the separate envelope tests and prior analyses are not included.')
text(f"Maximum multipole power-preservation error is {max(f['max_relative_power_preservation_error'],rot['max_relative_power_preservation_error']):.2g} fractionally. Analytic projected-variance means agree with calibration means within {max(abs(e['variance_closure']['standard_errors']) for e in C['ensembles'].values()):.2f} Monte Carlo standard errors. These checks validate the implementation, not the completeness of the observational model.", 'small')

page("17 / Simultaneous correlation envelopes")
equation(r'M(C)=\max_{\theta\in\Theta}\left|\frac{C(\theta)-\mu_{\rm ref}(\theta)}{s_{\rm ref}(\theta)}\right|,\qquad\Theta=\{60^\circ,61^\circ,\ldots,180^\circ\}')
text("Reference-only means and scales define the score. The independent calibration order statistic at rank ceil((n+1)*0.95) gives a 95% finite-grid prediction envelope. This is a two-sided maximum-deviation test, not the lower-tail S statistic or a confidence interval for a mean.")
figure('results/conditional/figures/simultaneous_envelopes.png','Envelopes cover all 121 declared angles simultaneously under each idealized ensemble. No continuum-wide guarantee is claimed. The measured curve is black.',365)
table(['Ensemble','Held-out coverage','95% counting interval','Max-deviation p'],[[labels[n],f"{e['simultaneous_band']['independent_validation_coverage']['rate']:.3f}", ' - '.join(f'{x:.3f}' for x in e['simultaneous_band']['independent_validation_coverage']['ci95']),f"{e['simultaneous_band']['upper_tail']['p']:.4f}"] for n,e in C['ensembles'].items()],[140,110,145,120])
text("Held-out coverage is measured on 1,024 independent skies for each ensemble. Both the envelope and its validation are conditional on the chosen null and reference fit. Small S and large standardized deviation are different events, so differing probabilities are expected.",'small')

page("18 / Injection, recovery and what a null result means")
equation(r'T_A(\hat n)=[1+A\,\hat n\cdot\hat p]T_{\rm smoothed}(\hat n)')
text("We apply a toy dipole modulation AFTER smoothing, at fixed Galactic direction (225 degrees, -27 degrees). Five amplitudes use 1,024 paired underlying Gaussian skies, for 5,120 processed maps. Every trial repeats mask projection and the 24-axis search. This measures our statistic's detection power, not a primordial amplitude or the significance of a different local-variance estimator. [21]")
figure('results/conditional/figures/injection_recovery.png','Detection fractions at a separately calibrated 5% threshold, and unsigned axis errors over all trials. Rate intervals are binomial; shaded direction intervals describe the trial distribution.',215)
table(['Injected A','Detection fraction','95% counting interval','Median axis error'],[[f"{v['amplitude']:.2f}",f"{v['detection']['rate']:.3f}",' - '.join(f'{x:.3f}' for x in v['detection']['ci95']),f"{v['median_axis_error_deg']:.1f} deg"] for v in C['injection']['rows']],[100,125,160,130])
text("The zero-amplitude row checks false alarms on data independent of the threshold calibration. Higher-amplitude rows measure power at one fixed direction; the same underlying skies make rows correlated. The estimated axis is unsigned and discretized. A failure to reject is not an exclusion limit on modulation amplitude, especially where recovery is weak.")
text("Reproduce this extension",'h2')
text("Run scripts/analyze_conditional.py and scripts/validate_conditional.py, or execute all 13 code cells in Planck_CMB_Advanced_Inference.ipynb. The saved notebook includes real-data outputs, three comparison maps and the full simulation execution. Local Python execution is documented; Google Colab compatibility does not imply execution on Google's infrastructure.",'small')

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
 ("Lewis, Challinor and Lasenby. Efficient computation of CMB anisotropies / CAMB (2000)", "https://arxiv.org/abs/astro-ph/9911177"),
 ("Contaldi et al. Suppressing the lower multipoles in the CMB anisotropies (2003)", "https://arxiv.org/abs/astro-ph/0303636"),
 ("Hivon et al. MASTER of the CMB anisotropy power spectrum (2002)", "https://arxiv.org/abs/astro-ph/0105302"),
 ("Probing foreground residuals in cleaned CMB temperature maps from Planck (2025)", "https://link.springer.com/article/10.1140/epjc/s10052-025-15246-y"),
 ("Akrami et al. Power asymmetry using a local variance estimator (2014)", "https://arxiv.org/abs/1402.0870"),
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
    canvas.drawString(40, 24, "Biswajit Jana  |  CMB Anomaly Lab")
    canvas.drawRightString(555, 24, f"Page {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT / "cmb-anomaly-lab.pdf"), pagesize=(595, 842),
    leftMargin=40, rightMargin=40, topMargin=43, bottomMargin=53,
    title="Cosmic Microwave Background Analysis - CMB Anomaly Lab", author="Biswajit Jana",
    subject="Planck measured-sky anomalies, Gaussian simulations and primordial transfer physics",
    keywords="cosmic microwave background, Planck, CMB anomalies, CAMB, HEALPix, SciencePlots, Biswajit Jana")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(OUT / "research-report.md").write_text("\n".join(md), encoding="utf-8")
print(f"Built {OUT / 'cmb-anomaly-lab.pdf'} and matching Markdown")
