# Research releases

## 0.3.0 - 9 November 2026

- Added fixed-power conditional harmonic sampling and Haar-uniform rotations of the measured pattern, alongside a fresh Gaussian comparison: 18,432 realizations across independent reference, calibration and held-out sets.
- Added finite-grid simultaneous correlation envelopes, held-out coverage and analytic projected-variance closure under each ensemble.
- Executed 5,120 paired post-smoothing dipole-modulation injections to quantify hemisphere-test power, false alarms and unsigned direction recovery.
- Added ten tests of harmonic moments, Haar isotropy, rotation conservation, envelope coverage, binomial counting, thresholds and injection response; 28 tests total.
- Added a second Colab-compatible notebook with 13 executed code cells and saved real-data outputs. Local execution is disclosed.
- Expanded the report with four research sections, equations, SciencePlots figures and author/project/page footers; updated README, website, methods, literature and reproducibility exports.

These are distinct conditional randomization hypotheses, not additional independent sky measurements. The study retains its explicit idealized-null and foreground limitations and makes no new-physics discovery claim.

## Website and executed notebook - 4 November 2026

- Published the project website from this repository at `https://biswajit1999.github.io/cmb-anomaly-lab/`.
- Added a Colab-compatible teaching notebook with 40 cells, including 19 genuinely executed code cells and real Planck outputs; local execution is disclosed.
- Rendered full-sky and confidence-masked SMICA maps in a custom blue-orange palette and updated the report cover.
- Added readable HTML versions of the notebook, methods, literature and results, plus a repository-owned GitHub Pages deployment workflow.
- Replaced the README's rejected `operatorname` variance macro with `mathrm`, including the generator so the fix persists.

## 0.2.0 - 4 November 2026

Completed the measured-sky and primordial-model extension of the study.

- Native-resolution SMICA harmonic extraction, 5 degree beam and pixel-window processing, confidence mask and retained-sky nuisance projection.
- Cut-sky correlation, variance, mask-dependent pseudo-parity and a 24-axis hemisphere search; 8,192 primary skies with independent reference/calibration streams and three processing variants.
- Analytic Gaussian variance closure, explicit pixel-pair and dense-covariance tests, numerical convergence checks, and 2,048 additional validation skies.
- CAMB propagation of a primordial suppression family to TT/TE/EE; 161 distinct models, 100,000-spectrum parameter-search calibration, conditional polarization predictions and an increased-accuracy check.
- SciencePlots figures with raster previews and vector PDF exports; a 16-page report with rendered mathematical equations and author/project/page footers.
- Research-oriented README, expanded methods and 20-paper reading guide, updated citation and reproducible environment snapshot.

The map correlation has local p approximately 0.008 under the stated CMB-only null. Its baseline four-diagnostic family has p approximately 0.031. The tested primordial alternative gives only a weak fit gain (calibrated p approximately 0.265). No physical-origin discovery or project-wide global significance is claimed.

## 0.1.0 - 1 November 2026

Initial public release: official Planck spectra and map retrieval, full-sky Gaussian spectral statistics, 200,000 primary spectra plus 100,000 independent validation spectra, dependence/conditioning/search studies, measured-sky display, ten numerical tests and an illustrated research report.
