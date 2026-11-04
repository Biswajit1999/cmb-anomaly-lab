# Measured Planck sky: estimators, closure and limits

**Author: Biswajit Jana. Version 0.2.0, 4 November 2026.**

This experiment is executed in [analyze_maps.py](../scripts/analyze_maps.py), with reusable operators in [map_statistics.py](../src/cmb_lab/map_statistics.py). The [configuration](../config/map_analysis.json), [results](../results/masked_sky/results.json), [summary](../results/masked_sky/SUMMARY.md) and calibration-statistic CSV are versioned. It is a matched **CMB-only Gaussian null**, not an end-to-end simulation of Planck foreground cleaning and instrumentation.

## 1. Native-resolution data and harmonic processing

The input is the released SMICA PR3 full-mission temperature map, not a photograph or a synthetic reconstruction from the published TT spectrum. The FITS file contains I_STOKES in K_CMB, NSIDE=2048 and NESTED pixel ordering. The script checks the source hash and units, converts to microkelvin and RING ordering, and extracts harmonics through L=128 **before reducing resolution**. Equal-area quadrature (`map2alm`, `iter=0`) defines this numerical operator explicitly.

The output coefficients are

$$a^{\mathrm{out}}_{\ell m}=a^{\mathrm{in}}_{\ell m}\frac{b^{\mathrm{out}}_\ell p^{\mathrm{out}}_\ell}{b^{\mathrm{in}}_\ell p^{\mathrm{in}}_\ell},\qquad b_\ell=\exp[-\ell(\ell+1)\sigma_b^2/2],\quad\sigma_b=\frac{\mathrm{FWHM}}{\sqrt{8\ln2}}.$$

We adopt the 5 arcmin SMICA temperature beam, the tabulated HEALPix pixel windows, and an output 5 degree beam at NSIDE=32. This convention follows published harmonic-resolution processing of PR3 SMICA; it is not a reconstruction of a detector-specific beam. At the retained low multipoles the native pixel correction is very small. See [PR3 map processing](https://link.springer.com/article/10.1140/epjc/s10052-025-15246-y) and the [healpy transform documentation](https://healpy.readthedocs.io/en/stable/generated/healpy.sphtfunc.map2alm.html).

The confidence mask is degraded by averaging child pixels, retaining output pixels with native retained fraction at least 0.95. The output order is explicitly RING. Full-sky monopole/dipole coefficients are zeroed; the retained sky is then fitted again. Subtracting an arbitrary global monopole/dipole before the second fit has no effect on the final projected residual in exact arithmetic.

The input bandlimit, finite quadrature, pixelization and mask are part of the estimator. A hard mask creates power above the correlation bandlimit; no claim is made that a bandlimited masked map equals the original unmasked sky. Smoothing can spread foreground contamination outside a hard confidence mask. Mask and smoothing variants measure sensitivity, not a complete bound on foreground bias.

## 2. Projection of nuisance modes

On the retained pixels, let X have columns (1,nx,ny,nz). Fit the four nuisance coefficients by ordinary least squares:

$$\widehat{\boldsymbol\beta}=(X^TX)^{-1}X^T\mathbf t,\qquad\mathbf r=P\mathbf t,\qquad P=I-X(X^TX)^{-1}X^T.$$

The implementation uses a pseudoinverse for numerical stability. It places residuals into a full-sky vector with zero outside the mask. **The exact same fit is repeated for each simulation**, so mask-induced coupling and the removal of low modes enter the null distribution. We do not subtract a dipole estimated from the data from all simulations.

## 3. Finite-band pair-normalized correlation

Define the pseudo-spectrum of the masked residual and the spectrum of the mask:

$$\widetilde C_\ell=\frac{1}{2\ell+1}\sum_m|\widetilde a_{\ell m}|^2,\qquad W_\ell=\frac{1}{2\ell+1}\sum_m|w_{\ell m}|^2.$$

The correlation estimator is

$$\widehat C_W(x)=\frac{\sum_{\ell=0}^{95}(2\ell+1)\widetilde C_\ell P_\ell(x)}{\sum_{\ell=0}^{95}(2\ell+1)W_\ell P_\ell(x)},\qquad S^W_{1/2}=\int_{-1}^{1/2}\widehat C_W(x)^2\,dx.$$

The denominator accounts for the angular distribution of available pairs. We require it to stay positive throughout the integration domain. We include masked ell=0,1 rather than discarding them by assumption. Equal-area transforms make the addition theorem an independent check:

$$\widetilde C_\ell=\frac{\Omega_{\rm pix}^2}{4\pi}\sum_{ij}r_i r_j P_\ell(\hat n_i\cdot\hat n_j).$$

The ratio is not a polynomial, so the L+1-node exactness argument for a full-sky S integral does not apply. We use 192 quadrature nodes and explicitly repeat the measured integral with 384 nodes. This tests integration convergence, not convergence to an infinite-band pair estimator. The tests compare harmonic powers with direct pixel-pair sums on a small sky.

The familiar expectation `masked correlation = mask correlation × true correlation` requires care after fitting nuisance modes. Projection changes that expectation. We calibrate the **projected estimator** directly rather than claiming division by the mask restores an unbiased cosmological C(theta). MASTER illustrates why masking couples multipoles; this project does not implement a MASTER deconvolution. [Hivon et al.](https://arxiv.org/abs/astro-ph/0105302)

## 4. Variance, pseudo-parity and the direction search

The masked variance is `mean(r²)`. Pseudo-parity is the mean even/odd D-ell ratio for ell=2–29 computed from the masked residual pseudo-spectrum. It is explicitly **not** a full-sky parity measurement.

For each of 24 unoriented HEALPix axes at axis NSIDE=2, split the retained pixels into two hemispheres and compute their variances about their respective means. The directional statistic is

$$A_{\max}=\max_{\hat d\in\mathcal D}\frac{|V_+(\hat d)-V_-(\hat d)|}{V_+(\hat d)+V_-(\hat d)}.$$

Antipodal axes are duplicates for this absolute contrast and are counted only once. The direction scan is repeated on every null map. It is a **coarse finite search**, not a continuous all-directions optimization or the Planck local-variance pipeline. The maximizing data axis has no standalone direction significance.

## 5. Simulation and search calibration

We draw independent real Gaussian m=0 modes with variance C-ell and complex m>0 modes with real and imaginary variance C-ell/2. We synthesize the corresponding real field with healpy. The fixed cosmology is the archived Planck TT best fit. Beam and pixel factors multiply simulated harmonic amplitudes before synthesis.

The seed spawns independent reference and calibration streams, each containing 4,096 skies. Each sky is processed with the baseline mask/beam and two variants: mask threshold 0.99, or 8 degree smoothing. The variants reuse the same sky realization so dependence is preserved.

All four test columns are oriented to lower tails by negating the upper-tail contrast. Reference ranks define the most unusual column. Independent calibration skies undergo the same search to obtain a minimum-p family probability. We report the baseline four-column family and the twelve-column family spanning the three variants. These are separate from the spectral and primordial-model families. **There is no single globally calibrated discovery probability for the entire project.**

For each local tail, p=(k+1)/(N+1), with a Clopper-Pearson 95% binomial interval for the event rate. Family intervals condition on the finite reference ensemble and do not include reference-rank uncertainty. Near the smallest probabilities, simulation counts and intervals matter more than extra decimal places.

## 6. Analytic closure without a dense production covariance

Let Sigma be the Gaussian pixel covariance of the smoothed sky. Since P is symmetric and idempotent,

$$\mathbb E[V_W]=\frac{1}{N_W}\mathrm{tr}(P\Sigma P)=C(0)-\frac{1}{N_W}\mathrm{tr}[(X^TX)^{-1}X^T\Sigma X].$$

We apply Sigma to the four template vectors using spherical-harmonic convolution, avoiding a 12,288 × 12,288 dense matrix. A separate test constructs a dense small-sky covariance from the Legendre addition theorem and verifies the trace identity. The production simulation mean is compared with the analytic value in units of its Monte Carlo standard error.

This verifies the implemented Gaussian operator. It cannot verify missing observational foregrounds, noise or component-separation systematics. Native high-resolution extraction, output quadrature and mask-edge discretization are additional numerical choices; their sensitivity is reported where measured, not asserted to be zero.
