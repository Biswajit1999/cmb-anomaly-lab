# Mathematical and statistical methods

Author: Biswajit Jana. Scope: temperature-only, rotationally invariant statistics of published Planck spectrum estimates.

## 1. From sky temperature to angular power

Write the mean-subtracted temperature as

$$\Delta T(\hat n)=\sum_{\ell m}a_{\ell m}Y_{\ell m}(\hat n),\qquad
\widehat C_\ell=\frac{1}{2\ell+1}\sum_{m=-\ell}^{\ell}|a_{\ell m}|^2.$$

For a real sky, negative-m coefficients are constrained by the reality condition. An isotropic Gaussian model has covariance

$$\langle a_{\ell m}a^*_{\ell' m'}\rangle=C_\ell\delta_{\ell\ell'}\delta_{mm'}.$$

For an ideal full sky with no noise,

$$\frac{(2\ell+1)\widehat C_\ell}{C_\ell}\sim\chi^2_{2\ell+1},\qquad
\mathrm{Var}(\widehat C_\ell)=\frac{2C_\ell^2}{2\ell+1}.$$

This is the exact distribution sampled by the code, rather than an approximate Gaussian error bar. It expresses cosmic variance: even a perfect telescope sees only one realization. The theoretical C-ell is fixed to the official Planck best-fit TT spectrum. Multipoles 0 and 1 are excluded everywhere.

The archive supplies

$$D_\ell=\frac{\ell(\ell+1)}{2\pi}C_\ell,$$

so the loader converts D-ell to C-ell before correlation or variance calculations. Temperature units are microkelvin; C-ell and D-ell have units microkelvin squared. Negative high-ell measured estimates, if present, are not clipped. The theory spectrum must be positive.

## 2. Four fixed statistics

**Quadrupole:** the measured C2. Its lower-tail probability can also be computed exactly as the chi-square CDF at 5 times observed C2 / theory C2. This independently checks the simulation code.

**Large-angle correlation:** at bandlimit L,

$$C(x)=\frac{1}{4\pi}\sum_{\ell=2}^{L}(2\ell+1)\widehat C_\ell P_\ell(x),\quad x=\cos\theta,$$

$$S_x=\int_{-1}^{x}C(u)^2du=\mathbf C^T K(x)\mathbf C,$$

$$K_{\ell\ell'}(x)=\frac{(2\ell+1)(2\ell'+1)}{16\pi^2}\int_{-1}^{x}P_\ell(u)P_{\ell'}(u)du.$$

The default is x = 1/2, corresponding to separations at least 60 degrees, and L = 64. K is computed by Gauss-Legendre quadrature with L+1 nodes. The integrand is a polynomial of degree at most 2L, so the quadrature is exact up to floating-point arithmetic. S has units microkelvin to the fourth. Independent adaptive quadrature and full-sphere Legendre orthogonality validate the implementation.

**Parity:** let E and O denote the even and odd multipoles in 2 through Lp. Define

$$R_{L_p}=\frac{|E|^{-1}\sum_{\ell\in E}D_\ell}{|O|^{-1}\sum_{\ell\in O}D_\ell}.$$

The baseline Lp is 29. The mean convention prevents unequal numbers of even and odd terms from introducing a trivial count bias when scanning cutoffs. A value below unity means lower mean even power. The simulation, not unity alone, defines the lower-tail probability because LCDM is not exactly flat in D-ell.

**Band-limited variance:**

$$V_{2:29}=\frac{1}{4\pi}\sum_{\ell=2}^{29}(2\ell+1)\widehat C_\ell.$$

This is a full-sky unsmoothed band variance. It is not the variance of a masked, smoothed NSIDE=16 map and does not test hemispherical asymmetry.

## 3. Counting uncertainty and search calibration

For a lower-tail statistic, count k simulations with statistic no larger than observed among N draws. Report (k+1)/(N+1), with a 95% Clopper-Pearson interval for the underlying binomial rate. The interval concerns simulation counting only. It does not include instrument, foreground, estimator, cosmological-parameter, or literature-selection uncertainty. No zero-event result is reported as zero probability.

Two independent SeedSequence child streams produce 100,000 reference and 100,000 calibration spectra. For each statistic, the reference ensemble defines its empirical CDF. For a specified family, take the smallest CDF value across statistics. Compare this observed minimum with minima formed for the independent calibration ensemble. Correlations between tests are retained automatically.

The four-test family contains the four fixed diagnostics. The parity scan uses integer cutoffs 10 through 29. The angular scan uses separations 45, 50, ..., 90 degrees. The combined family has 34 columns: four fixed metrics, twenty parity cutoffs, ten angular thresholds. Some columns duplicate fixed metrics; identical columns do not create extra independent trials. Monte Carlo intervals for family results are conditional on the finite reference ensemble. A repeated seed run checks stability but is not combined with the main result.

Adding more candidate tests can lower the calibrated p if the observed minimum also becomes more extreme. Therefore the 34-test result is not required to exceed the four-test result: they answer different questions. Each corrected result should be compared with its own local minimum.

The choice of families was motivated by existing anomalies. No correction here counts the unknown complete history of CMB searches. Sensitivity cutoffs, conditional tests, and algebraic counterfactuals are diagnostics and are not included as discoveries in this family correction.

## 4. Dependence, conditioning, and cancellation

Bulk Spearman correlations do not establish independence in rare tails. We also tabulate pairwise co-occurrence below marginal 1%, 5%, and 10% thresholds and divide these joint rates by the products of their empirical marginal rates. These ratios are descriptive and become noisy for rare events. We count the all-four lower rectangle as a separate event probability; it is **not** a calibrated omnibus p-value, so we never convert it to a discovery sigma.

To ask how much information S adds beyond C2, replace C2 in each calibration spectrum by the measured C2 and retain all other independently drawn multipoles. Under the ideal Gaussian model, this samples the conditional distribution at that value. It is a plug-in diagnostic that ignores measurement uncertainty in C2 and removes its probability cost; it cannot explain the low quadrupole itself.

Because S is quadratic, holding all multipoles except C2 fixed gives

$$\frac{\partial S}{\partial C_2}=2(K\mathbf C)_2,\qquad
C_2^*=-\frac{\sum_{\ell>2}K_{2\ell}C_\ell}{K_{22}}.$$

The physical nonnegative optimum is max(0, C2-star). The code also replaces each observed multipole individually by its theory value and records the change in S. These are transparent algebraic sensitivity checks. The effects are not additive because cross terms couple multipoles. A near-optimal value is not by itself surprising evidence: its significance, estimator uncertainty, and selection procedure would need separate calibration.

## 5. Relationship to the measured-sky extension

The published TT point estimates do not have the same distribution as ideal full-sky C-ell draws. An observational analysis must send simulations through the same map cleaning, beam, pixelization, mask, monopole/dipole removal, and correlation estimator as the data. Noise and foreground uncertainty must be propagated. Estimator changes cannot be treated as independent skies; neither can PR3 and PR4 or WMAP and Planck observations of the same cosmic realization.

Power-spectrum-only statistics contain no phase or directional information. Any nonnegative C-ell sequence defines an isotropic Gaussian covariance. Thus a deficit relative to a specific LCDM spectrum is not sufficient to demonstrate statistical anisotropy. Alignment, hemispherical, or off-diagonal covariance tests require map phases.

These methodological distinctions are discussed in the [literature review](literature-review.md), especially Efstathiou et al., Muir et al., the Planck likelihood paper, and the 2026 exchange.

Version 0.2.0 separately implements measured SMICA map statistics with a matched mask, beam/pixel window and nuisance projection. See [map methods](map-methods.md) for the finite-band estimator, direction-search calibration, numerical closure and the distinction between a Gaussian CMB-only null and a full observational simulation. The [CAMB experiment](primordial-model.md) extends the study to a primordial hypothesis and joint temperature/polarization predictions. The different experiments are not multiplied into one global discovery probability.
