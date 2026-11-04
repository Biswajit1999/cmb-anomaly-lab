# A primordial-power hypothesis tested with CAMB

**Author: Biswajit Jana. Version 0.2.0, 4 November 2026.**

Executable: [analyze_primordial.py](../scripts/analyze_primordial.py). [Configuration](../config/primordial_analysis.json), [numerical results](../results/primordial/results.json), [model grid](../results/primordial/model_grid.csv), [TT/TE/EE predictions](../results/primordial/predictions.csv).

## Physical question

Could a suppression of primordial long-wavelength curvature perturbations explain the low-temperature multipoles better than the baseline spectrum? This is an established question, not a new theory introduced by this repository. [Contaldi, Peloso, Kofman & Linde (2003)](https://arxiv.org/abs/astro-ph/0303636) discuss mechanisms and the sensitivity of cutoff inference to statistical assumptions. Our smooth two-parameter shape is a phenomenological test family; we do not identify it with their inflationary dynamics.

## From primordial perturbations to temperature and polarization

Take a dimensionless curvature spectrum

$$\mathcal P_\mathcal R(k)=A_s(k/k_*)^{n_s-1}[1-A\exp(-(k/k_c)^2)],\quad k_*=0.05\,{\rm Mpc}^{-1},\quad 0\le A\le1.$$

The null is A=0. A=1 suppresses the longest wavelengths quadratically; short wavelengths approach the baseline. Positivity is enforced. The code evaluates the small-k expression with `expm1` to avoid cancellation.

Linear transfer gives

$$C_\ell^{XY}=4\pi\int d\ln k\,\mathcal P_\mathcal R(k)\Delta_\ell^X(k)\Delta_\ell^Y(k),\quad X,Y\in\{T,E\}.$$

We compute these transfer functions with [CAMB](https://camb.readthedocs.io/en/latest/), based on [Lewis, Challinor & Lasenby (2000)](https://arxiv.org/abs/astro-ph/9911177). CAMB is asked for raw C-ell in microkelvin squared, not its default D-ell output. The background is fixed near Planck 2018: H0=67.36, omega_b h²=0.02237, omega_c h²=0.12, tau=0.0544, As=2.1e-9, ns=0.9649, summed neutrino mass 0.06 eV, zero curvature. Helium and other settings follow CAMB defaults; the package version is recorded.

We use unlensed scalar spectra and a fixed background. The TT fit is restricted to ell=2–29, where the missing lensing correction is small, but it is not silently identified with the official best-fit model. The maximum baseline fractional difference from the official TT spectrum is recorded. The high-ell sky, polarization likelihood and background parameters are not fitted.

Unlensed scalar transfer is linear in primordial power. Therefore, at each kc we compute A=0 and A=1 and interpolate C-ell linearly in A. This is an exact consequence of the transfer integral in this model, not an arbitrary interpolation of an inflationary solution. The spline of primordial power uses 5,000 logarithmic k samples from 1e-7 to 10 Mpc^-1.

## Parameter search and an honest significance calculation

The grid has A=0,0.1,...,1 and 16 log-spaced cutoff scales from 3e-5 to 8e-4 Mpc^-1. The null is repeated at each cutoff in storage but represents one model, giving **161 distinct models**. Duplication does not change the maximum.

For ideal Gaussian full-sky temperature powers, constants cancel from the likelihood ratio:

$$2\Delta\ln\mathcal L=\sum_{\ell=2}^{29}(2\ell+1)\left[\ln\frac{C^0_\ell}{C_\ell}+\widehat C_\ell\left(\frac{1}{C^0_\ell}-\frac{1}{C_\ell}\right)\right].$$

When this expression is evaluated on published Planck point estimates, it is an **idealized likelihood proxy**. It is not the Commander/plik likelihood and does not include its estimator covariance or nuisance parameters.

We maximize this score on each of 100,000 independently generated baseline spectra. The upper-tail probability of the observed maximum includes the same finite grid search. We do not use Wilks' theorem: the amplitude sits on a boundary under the null and kc is unidentified there. We do not quote a Bayes factor, a posterior probability of the null or a confidence region for the optimum. The retrospective choice of the model family is not included in this calibration.

## Executed finding

The best grid model has A=1 and kc approximately 2.68e-4 Mpc^-1. Its 2 Delta ln L is about **1.026**, with search-calibrated **p≈0.265**. The amplitude sits at a boundary of the allowed grid. These data and assumptions do not provide compelling support for this alternative. A lower S statistic alone is not a reason to prefer a model; the complete fitted bandpowers and the fitting freedom must be counted.

Doubling CAMB accuracy changes the best model's score by about 0.0004 and its low-ell TT power by less than 0.08%. This checks numerical accuracy at the selected model; it is not a marginalization over cosmological uncertainty or a full convergence study of every model shape.

## Conditional polarization predictions

In a Gaussian isotropic model, the joint T/E covariance of each independent real harmonic degree of freedom is

$$\Sigma_\ell=\begin{pmatrix}C_\ell^{TT}&C_\ell^{TE}\\ C_\ell^{TE}&C_\ell^{EE}\end{pmatrix}.$$

Conditioning gives

$$\mathbb E[a^E_{\ell m}\mid a^T_{\ell m}]=\frac{C_\ell^{TE}}{C_\ell^{TT}}a^T_{\ell m},\qquad {\rm Var}(a^E_{\ell m}\mid a^T_{\ell m})=C_\ell^{EE}-\frac{(C_\ell^{TE})^2}{C_\ell^{TT}}.$$

Consequently,

$$\mathbb E[\widehat C_\ell^{EE}\mid\widehat C_\ell^{TT}]=C_\ell^{EE}-\frac{(C_\ell^{TE})^2}{C_\ell^{TT}}+\left(\frac{C_\ell^{TE}}{C_\ell^{TT}}\right)^2\widehat C_\ell^{TT}.$$

The exported curves use published TT power as an exact plug-in value. They are **predictions**, not measured EE, uncertainty bands or a validation of the fitted model. A real test must propagate temperature uncertainty and polarization noise/masking/foregrounds. The same primordial spectrum predicts TT, TE and EE together; they cannot be tuned independently or treated as wholly independent evidence.
