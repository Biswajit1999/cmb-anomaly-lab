# Cosmic Microwave Background Analysis · CMB Anomaly Lab

### Planck data, large-angle anomalies, mathematical physics and reproducible Python

[![Numerical validation](https://github.com/Biswajit1999/cmb-anomaly-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/Biswajit1999/cmb-anomaly-lab/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/Code-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](pyproject.toml)
[![Research release](https://img.shields.io/badge/Research-v0.2.0-287f91.svg)](CITATION.cff)

**Author: [Biswajit Jana](https://github.com/Biswajit1999)** · Updated 4 November 2026 · Independent, open research

Why does the oldest observable light contain so little correlation at large angular separations? Do low quadrupole power, odd/even imbalance and hemispherical differences tell us several things, or repeat information from the same few modes? Would suppressing primordial long-wavelength power actually improve the fit once the model search is counted?

This repository investigates these questions using **official Planck PR3 numerical measurements**, spherical harmonics, Gaussian sky simulations, explicit search calibration and **CAMB Boltzmann transfer calculations**. It provides a study path for students and inspectable methods, numerical outputs and limitations for researchers.

**Research status:** completed, reproducible exploratory study under specified idealized models. The results do not establish a new physical mechanism. This is independently authored software and analysis, not an official Planck analysis or an affiliated collaboration product. AI coding and drafting assistance is disclosed in [AUTHORS.md](AUTHORS.md).

![Measured Planck SMICA temperature with confidence masking](results/maps/planck_temperature.png)

*Measured component-separated temperature anisotropy, ESA / Planck Collaboration; distributed by NASA/IPAC IRSA. Colours show temperature deviations, not individual galaxies. Grey regions are excluded by the displayed confidence mask.*

## Start here

| Your purpose | Read or run |
|---|---|
| Learn what the CMB image measures | [Physical introduction](#what-the-cmb-image-measures) and [study path](#a-study-path-through-the-project) |
| Read the scientific work | **[Illustrated research PDF](reports/cmb-anomaly-lab.pdf)** · [same report in Markdown](reports/research-report.md) |
| Inspect equations and assumptions | [Spectral methods](docs/methods.md) · [map estimators and closure](docs/map-methods.md) · [primordial transfer model](docs/primordial-model.md) |
| Examine the actual outputs | [Spectral results](results/baseline/SUMMARY.md) · [measured-sky results](results/masked_sky/SUMMARY.md) · [primordial model results](results/primordial/results.json) |
| Reproduce everything | [Installation and commands](#reproduce-the-study) · [versioned protocols](config/) · [source data provenance](data/manifest.json) |
| Study the literature | [Annotated primary-source reading guide](docs/literature-review.md) · [hypotheses and conclusions](docs/research-agenda.md) |
| Reuse or cite the work | [Citation and credit](#citation-and-credit) · [CITATION.cff](CITATION.cff) |

## What the CMB image measures

The cosmic microwave background is nearly uniform thermal radiation. The maps studied here show tiny **temperature anisotropies** around its mean. Most of the primary temperature pattern was imprinted when photons last scattered in the early universe; subsequent propagation also changes it.

A hot or cold pixel is not a one-to-one density measurement. Intrinsic photon perturbations, gravitational redshifts, velocities and integrated propagation effects all contribute. Connecting the sky to primordial curvature perturbations requires transfer physics.

We expand the field into angular modes:

$$T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n),\qquad \widehat C_\ell=\frac{1}{2\ell+1}\sum_m|a_{\ell m}|^2.$$

Low multipoles represent broad sky patterns; high multipoles represent finer angular structure. Since we observe only one cosmic sky, even a perfect instrument leaves **cosmic variance**:

$$\frac{(2\ell+1)\widehat C_\ell}{C_\ell}\sim\chi^2_{2\ell+1},\qquad \operatorname{Var}(\widehat C_\ell)=\frac{2C_\ell^2}{2\ell+1}.$$

The sky map, the measured power-spectrum estimates and a theoretical spectrum are different objects. The code keeps their provenance and roles explicit. Processed Planck products are original scientific measurements for this analysis; we do not claim to have reduced raw detector time streams.

## Five questions, connected experiments

| Question | Implemented experiment | Interpretation |
|---|---|---|
| Why is the quadrupole weak? | Exact chi-square benchmark; conditional simulations | Measures rarity and shared information, not a cause |
| Why are large-angle correlations small? | Spectral Legendre reconstruction and a separately calibrated masked SMICA estimator | Exposes estimator and sky-cut dependence |
| Is odd/even power imbalance unusual? | Full-sky parity proxy, cutoff search and masked pseudo-parity | Distinguishes fixed tests, selected tests and mask-dependent power |
| Is large-scale power distributed asymmetrically? | Total variance and a 24-axis hemisphere search on measured and simulated skies | Adds a phase-sensitive diagnostic with its direction-search cost |
| Does an explicit primordial alternative do better? | CAMB TT/TE/EE transfer, finite parameter search and 100,000-sky calibration | Tests a physical power-spectrum hypothesis and its polarization consequences |

The first four diagnostics are also studied jointly rather than multiplying their nominal p-values. Low correlations and low variance can partly reflect the same quadrupole.

## Results from the measured sky

The map experiment uses **4,096 reference skies and 4,096 independent calibration skies**. Each is analysed under three processing choices. Native SMICA harmonics are extracted before resolution reduction; the baseline has a 5 degree beam, NSIDE=32 and a 0.95 mask-fraction threshold. Monopole and dipole are fitted on the retained pixels for every observed or simulated sky.

| Baseline map diagnostic | Observed | Tail probability | 95% Monte Carlo interval |
|---|---:|---:|---:|
| Large-angle correlation, $S^W_{1/2}$ | 2036.8 | 0.00805 | 0.00535–0.01101 |
| Masked temperature variance | 1590.5 | 0.04369 | 0.03742–0.05016 |
| Mask-dependent even/odd power | 0.7624 | 0.01855 | 0.01443–0.02290 |
| Maximum hemisphere contrast (24-axis search) | 0.31085 | 0.08055 | 0.07218–0.08907 |

S has units microkelvin to the fourth; variance has units microkelvin squared; the other statistics are dimensionless. The first three probabilities are lower tails; the contrast uses an upper tail **after** maximizing across the declared directions.

The baseline four-diagnostic family gives **p=0.0315**. Including all twelve columns across the baseline, stricter mask and broader beam gives **p=0.0310**. These are calibrations of those declared families, not a universal correction for every statistic previously tried in cosmology.

![Cut-sky correlation from measured SMICA and matched Gaussian maps](results/masked_sky/figures/cut_sky_correlation.png)

*SciencePlots figure. Shading gives pointwise simulation ranges, not a simultaneous confidence band. The finite-band mask-normalized correlation estimator and its projection are defined in [map methods](docs/map-methods.md).*

The separate spectrum experiment contains **100,000 reference and 100,000 calibration spectra**. Its quadrupole p≈0.047, spectral S1/2 p≈0.075 and fixed parity p≈0.010 describe a different estimator from the map table. Conditioning on the measured quadrupole changes spectral S1/2 p from **0.0752 to 0.4842**. The difference between spectrum and cut-sky results is scientifically relevant; choosing the smallest result without its processing context is not justified.

## A physical model tested, including an unexciting answer

We modify the primordial curvature spectrum through a positive suppression shape:

$$\mathcal P_\mathcal R(k)=A_s(k/k_*)^{n_s-1}[1-Ae^{-(k/k_c)^2}],\quad 0\le A\le1.$$

CAMB propagates it through the same transfer physics for temperature and polarization:

$$C_\ell^{XY}=4\pi\int d\ln k\,\mathcal P_\mathcal R(k)\Delta_\ell^X(k)\Delta_\ell^Y(k),\quad X,Y\in\{T,E\}.$$

The best of **161 distinct grid models** improves the ideal low-ell TT likelihood proxy by only **2 ΔlnL≈1.026**. Repeating the full grid search on **100,000 null spectra** gives **p≈0.265**. This study finds **no compelling preference for this suppression model**. Its fitted parameters are not presented as measured inflationary parameters or as Bayesian evidence.

![CAMB primordial model fit and calibrated parameter search](results/primordial/figures/primordial_search.png)

The model also produces EE and TE predictions. We export the Gaussian EE expectation conditioned on the observed TT power, because polarization is correlated with temperature. **No measured polarization likelihood is analysed here.** See the [derivation and assumptions](docs/primordial-model.md) and [prediction table](results/primordial/predictions.csv).

## Reproduce the study

Python 3.10 or later. Linux, macOS or WSL is recommended for the full HEALPix/CAMB stack. The small published spectrum files are versioned; the original SMICA FITS download is about 2 GB and excluded from Git.

```bash
git clone https://github.com/Biswajit1999/cmb-anomaly-lab.git
cd cmb-anomaly-lab
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,maps,physics,report]'
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2

python scripts/download_data.py --with-map
python -m pytest -q
cmb-lab
python scripts/validate_run.py
python scripts/render_planck_map.py
python scripts/analyze_maps.py
python scripts/analyze_primordial.py
python scripts/validate_extensions.py
python scripts/build_readme.py
python scripts/build_report.py
```

For a quick spectral smoke check, use `cmb-lab --quick`; it writes to `results/quick` and preserves the full results. `analyze_maps.py --quick` uses 32 skies per batch and still needs the real map; it is only an execution check, not a useful significance estimate.

In Windows PowerShell the activation command is `.venv\Scripts\Activate.ps1`; environment variables use `$env:OMP_NUM_THREADS='2'` and `$env:OPENBLAS_NUM_THREADS='2'`. Use WSL if HEALPix or CAMB wheels are unavailable for your native Python platform.

An executed-environment version snapshot is in [requirements-lock.txt](requirements-lock.txt). Source hashes, input hashes, package versions, seeds, search grids and sample counts are recorded alongside results. Intermediate `.npz` caches are ignored; scripts recreate them. The PDF and README are generated from the executed JSON outputs.

## Validation and numerical limits

- **18 numerical tests:** analytic distributions, quadrature, projection invariance, pixel-pair addition theorem, dense-covariance closure, harmonic sampling, likelihood algebra and conditional polarization identities.
- **100,000 additional spectra** with an independent seed reproduce the primary spectral probabilities; see [validation](results/validation.json).
- **2,048 additional maps** independently check baseline map tail probabilities; see [extension validation](results/extension_validation.json).
- **Analytic variance closure:** the baseline map ensemble mean differs from its prediction by 0.36 Monte Carlo standard errors.
- **Numerical sensitivity:** doubled integration nodes, correlation-bandlimit and pixel-quadrature checks; doubled CAMB accuracy at the selected model.
- **Scientific figures:** SciencePlots `science`, `no-latex` and `bright` styles; PNG previews and vector PDF plot exports. Equations use Matplotlib mathtext, so a system LaTeX install is not required.

Simulation counting intervals are not the entire uncertainty budget. The map null includes the mask and nuisance-mode projection but omits realistic instrument noise, residual foregrounds, component-separation uncertainty and cosmological-parameter uncertainty. The spectral and CAMB likelihood calculations use published TT points with idealized full-sky sampling assumptions. The hard-mask correlation has a declared finite harmonic bandlimit. The code does not claim an official Planck anomaly significance.

The analyses are retrospective and literature motivated. Different releases and instruments observe the same cosmic sky. A low p-value is not the probability that a theory is false. Spectral power suppression alone does not establish anisotropy. The spectral, map and physical-model results are **not combined into a project-wide discovery claim**.

## A study path through the project

1. **Radiation and perturbations:** distinguish a blackbody mean temperature from temperature anisotropies; learn why density, velocity and gravitational terms contribute.
2. **Angular statistics:** derive spherical harmonics, C-ell versus D-ell, cosmic variance and Legendre correlation. Work through [spectral methods](docs/methods.md) and the analytic tests.
3. **Observed skies:** follow the FITS units, HEALPix ordering, beam/pixel windows, masking and nuisance projection in [map methods](docs/map-methods.md).
4. **Inference:** compare local tails, conditional ensembles, finite searches and analytic closure. Read the [results](results/masked_sky/SUMMARY.md) alongside their assumptions.
5. **Physical alternatives:** trace primordial P(k) through transfer functions and inspect the [CAMB model test](docs/primordial-model.md). Explain why fitting TT implies correlated polarization predictions.
6. **Critical reading:** compare the arguments in [the annotated literature guide](docs/literature-review.md); distinguish known methods, reproduced numerical findings and genuinely untested hypotheses.

## Project structure

```text
config/              Versioned spectral, map and primordial protocols
data/                Official small spectra, download manifest and interpretation
src/cmb_lab/         Statistics, masked-sky operators, primordial model, plots
scripts/             Executable analyses, independent checks, README/PDF builders
tests/               Mathematical and numerical validation
results/baseline/    Spectrum ensembles, dependence and search results
results/masked_sky/  Measured map statistics, calibration CSV and figures
results/primordial/  CAMB parameter grid, polarization predictions and figures
reports/             Illustrated PDF, Markdown report and rendered equations
docs/                Derivations, literature, hypothesis ledger
```

## Citation and credit

Use the GitHub **Cite this repository** action or [CITATION.cff](CITATION.cff). A concise software citation is:

> Jana, Biswajit (2026). *CMB Anomaly Lab: Reproducible Planck Large-Angle Temperature Experiments*, version 0.2.0. https://github.com/Biswajit1999/cmb-anomaly-lab

Cite **ESA / the Planck Collaboration** for measurements, **NASA/IPAC IRSA** for distribution, **HEALPix/healpy** for spherical-map calculations, **CAMB** for transfer functions and **SciencePlots** for figure styling. Primary scientific references and reading-depth labels are in the [literature guide](docs/literature-review.md).

The MIT license covers original project code and prose. Third-party data and software retain their own terms. Please report reproducibility issues with the command, package versions, configuration and relevant numerical output through [GitHub Issues](https://github.com/Biswajit1999/cmb-anomaly-lab/issues). Scientific corrections and independently checked reproductions are welcome.
