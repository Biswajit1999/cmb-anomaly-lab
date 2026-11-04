# Research reading guide

Initial search and review: **31 October 2026**. Map/transfer-method additions checked **2-4 November 2026**. This is a focused evidence map, not an exhaustive systematic review. Primary papers and official data documentation were searched for Planck large-angle correlation, quadrupole, parity, covariance, foregrounds, and selection effects. Full-text methodological sections were examined where marked; other entries were checked at abstract/documentation level. No claim is made to have read every paper cited by these sources.

## Core observational and methodological literature

| Source | Reading depth | Relevance to this project |
|---|---|---|
| [Planck 2018 VII: Isotropy and Statistics](https://arxiv.org/abs/1906.02552), published 2020 | Selected full-text methods and results | Establishes the official anomaly context, including map and mask dependence. Our defined spectral and map experiments do not reproduce all of its tests or end-to-end simulations. |
| [Planck 2018 V: Power spectra and likelihoods](https://arxiv.org/abs/1907.12875), 2020 | Abstract and archive documentation | Explains the hybrid low/high multipole likelihood. Motivates the explicit distinction between released point estimates and an actual sampling likelihood. |
| [Planck 2018 IV: Diffuse component separation](https://arxiv.org/abs/1807.06208), 2020 | Abstract and map documentation | Describes the Commander, NILC, SEVEM and SMICA products and limitations in noise/systematics modelling. Supports the provenance of our measured SMICA input. |
| [Planck 2018 VI: Cosmological parameters](https://arxiv.org/abs/1807.06209), 2020 | Abstract | Supplies context for using the best-fit base-LCDM theory. We hold that theory fixed rather than refitting cosmological parameters. |
| [Muir, Adhikari & Huterer: Covariance of CMB anomalies](https://arxiv.org/abs/1806.02354), 2018 | Full-text statistics definitions and estimator comparison | Direct prior art for joint anomaly studies. Demonstrates that full-sky and cut-sky S1/2 probabilities differ. Our conditional and covariance work must not be presented as the first such investigation. |
| [Efstathiou, Ma & Hanson: Large-Angle Correlations](https://arxiv.org/abs/0911.5399), 2010 | Selected full text | Develops the estimator/reconstruction perspective and cautions against interpreting an a-posteriori correlation statistic in isolation. |
| [Copi et al.: Lack of large-angle TT correlations persists](https://arxiv.org/abs/1310.3831), 2015 | Abstract and journal methods excerpt | Argues for the robustness of low cut-sky correlations across WMAP and Planck. Provides a substantive contrasting perspective to reconstruction-based interpretations. |
| [Schwarz, Copi, Huterer & Starkman: CMB Anomalies after Planck](https://arxiv.org/abs/1510.07929), 2016 | Abstract | Organizes the wider anomaly landscape. Motivates a limited first project rather than treating every reported feature as one solved problem. |
| [Copi et al.: Large-angle anomalies in the CMB](https://arxiv.org/abs/1004.5602), 2010 | Abstract and journal excerpts | Historical background and discussion of the differences between full-sky and cut-sky correlation. |
| [Copi et al.: Large-scale alignments from WMAP and Planck](https://arxiv.org/abs/1311.4562), 2015 | Abstract and journal excerpt | Illustrates phase-dependent alignment questions. Our hemisphere search is also phase sensitive but does not measure quadrupole-octopole alignment. |

## Later results and live disagreements

**[Planck intermediate LVII: NPIPE](https://arxiv.org/abs/2007.04997), 2020.** Abstract checked. Describes joint LFI/HFI reprocessing and end-to-end simulations. It is the basis for extending the project beyond PR3; a new processing release is a systematic cross-check of the same sky, not an independent cosmic realization.

**[Jung et al.: Revisiting large-scale anomalies and local SZ contributions](https://arxiv.org/abs/2406.11543), 2024.** Selected full-text methods and results examined. Uses PR4 and constrained local-Universe simulations; the modeled local thermal and kinetic SZ contributions have negligible impact on the tested large-angle anomalies. This does not exclude every conceivable foreground mechanism.

**[Hogan et al.: Dipole-independent measurements of nearly-zero correlation](https://arxiv.org/abs/2312.16147v7), 2025.** Abstract and publication status checked. Investigates even-parity angular correlations and proposes a causal-coherence interpretation. The interpretation is a theoretical proposal, not an established explanation, and this repository does not reproduce its specialized statistic.

**[Jones, Copi, Starkman & Akrami: Strong Evidence Against a Statistically Isotropic Universe](https://arxiv.org/abs/2310.12859v3), revised March 2026.** Selected full text, tail-statistics and discussion examined. The authors emphasize joint tail rarity for four map-based anomaly classes and argue for a physical explanation. Their four statistics are not our four spectral diagnostics. The arXiv record describes preparation for resubmission; this guide does not presume final peer-review status.

**[Guth & Namjoo: Statistical isotropy and the look-elsewhere effect](https://arxiv.org/abs/2602.10178v2), February 2026.** Selected full text examined. Challenges combined-anomaly interpretation on two grounds: some statistics test a particular spectrum rather than isotropy, and selecting anomalies from a larger test set changes significance. The unknown historical search space remains difficult to quantify. We implement a transparent finite-family correction rather than assert either side has settled the issue.

## Numerical and archive references

**[Gorski et al.: HEALPix](https://arxiv.org/abs/astro-ph/0409513), 2005.** Abstract and package documentation checked. Equal-area spherical pixelization used to display the measured and simulated skies. **[healpy documentation](https://healpy.readthedocs.io/en/stable/)** explains map ordering, transforms, and degradation caveats. Pixel averaging here is visualization only.

**[IRSA PR3 ancillary products](https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/)** and **[IRSA PR3 CMB maps](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html)** were inspected directly. Exact product URLs and downloaded hashes appear in `data/manifest.json`.

## Synthesis

The existence of unusual low-order summary statistics is well studied. Their physical cause and overall evidential weight are unsettled. A useful contribution needs explicit estimators, selection rules, observational uncertainty, and a prediction that can fail. This project supplies reproducible experiments with quantified numerical checks and stated observational limits. Conditional tests, anomaly covariance, and look-elsewhere corrections all have prior art; none is claimed as newly invented here.

Version 0.2.0 extends the numerical study to measured-sky estimators and a CAMB primordial-power hypothesis. A novelty claim would require a dedicated search and independent review; these additions use established mathematical tools and are presented as an independently reproducible study.

## Added for the measured-sky and transfer calculations

| Primary source | Reading depth | Role and boundary |
|---|---|---|
| [Lewis, Challinor & Lasenby: Efficient computation of CMB anisotropies](https://arxiv.org/abs/astro-ph/9911177), 2000 | Abstract and current CAMB API documentation | Credit for CAMB; transfer calculation from a specified primordial spectrum. The code uses a flat background, not the paper's closed-universe example as a claimed fit. |
| [Contaldi, Peloso, Kofman & Linde: Suppressing the lower multipoles](https://arxiv.org/abs/astro-ph/0303636), 2003 | Abstract and inference discussion in the abstract | Prior art for primordial low-power hypotheses; motivates checking parameter-search cost. Our smooth test spectrum is not a reproduction of their inflaton dynamics or WMAP likelihood. |
| [Hivon et al.: MASTER](https://arxiv.org/abs/astro-ph/0105302), 2002 | Abstract and method context | Establishes pseudo-spectrum masking methodology. Our finite-band correlation division is not a MASTER coupling-matrix inversion. |
| [Probing foreground residuals in cleaned CMB temperature maps from Planck](https://link.springer.com/article/10.1140/epjc/s10052-025-15246-y), 2025 | Selected full-text data/preprocessing sections | Documents 5 arcmin PR3 SMICA beam, harmonic beam/pixel transformation and confidence mask. Our CMB-only null does not reproduce their foreground study. |

Software documentation checked: [CAMB result units and transfer reuse](https://camb.readthedocs.io/en/latest/results.html), [primordial spectrum interpolation](https://camb.readthedocs.io/en/latest/initialpower.html), [healpy equal-area transforms](https://healpy.readthedocs.io/en/stable/generated/healpy.sphtfunc.map2alm.html), [harmonic smoothing](https://healpy.readthedocs.io/en/stable/generated/healpy.sphtfunc.smoothing.html), and [SciencePlots style registration](https://github.com/garrettj403/SciencePlots). These are implementation references, not evidence for an anomaly's physical cause.
