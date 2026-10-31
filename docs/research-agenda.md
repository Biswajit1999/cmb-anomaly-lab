# Hypothesis ledger and next experiments

These are research hypotheses, not discoveries. The first project tests consequences of the statistical model; it does not derive a new fundamental theory.

## H1. Much of the spectrum-based low correlation shares information with C2

**Operational prediction:** the lower-tail rank of S1/2 becomes less unusual when the Gaussian reference is conditioned on the observed quadrupole. **Implemented:** the conditional p moves from approximately 0.075 to 0.484. **Interpretation:** supports shared statistical dependence for this estimator. It does not explain C2, prove that all anomalies share a cause, or resolve cut-sky behavior. Covariance and conditioning are established approaches in prior work.

## H2. Correlation suppression involves cancellations, not just less total power

**Operational prediction:** replacing a single low multipole can raise or lower S because off-diagonal terms of K couple powers. **Implemented:** analytic derivative, exact counterfactual C2 optimum, and all single-multipole replacements. With other measured multipoles fixed, the optimum C2 is about 231.75 microkelvin squared, compared with the observed 236.56.

This proximity is an interesting **post-result observation**, not evidence for fine-tuning or new physics. The published quadrupole uncertainty is large compared with their difference. The optimum depends on the same data, bandlimit, statistic, and estimator. There is no calibrated novelty or discovery claim. A more useful next experiment would propagate joint posterior map uncertainty and ask whether a prespecified cancellation statistic remains informative after conditioning on C2 and variance.

## H3. Apparent additional clues weaken under explicit search calibration

**Operational prediction:** the selected parity-cutoff result has a larger p when the cutoff search is performed on each simulated spectrum. **Implemented:** the complete 10-29 cutoff scan and an independent calibration ensemble. **Falsifiable extension:** freeze the statistic and evaluate a separate observable, such as a properly conditioned polarization prediction. Do not label a second release of the same temperature sky as a new sample.

## Competing physical explanations

| Mechanism | Mathematical connection | Discriminating work needed |
|---|---|---|
| A chance realization of Gaussian LCDM | Independent Gaussian harmonic modes; chi-square power fluctuations | Matched map-estimator simulations and joint calibrated tests |
| Modified primordial long-wavelength power | C-ell = 4 pi integral d ln k P_R(k) Delta_T,ell(k)^2 | Boltzmann predictions for TT, TE, EE; evidence with priors; include all parameter-fitting costs |
| Residual Galactic or local foregrounds | Observed sky = CMB + residual + noise | Frequency dependence, independent cleaning pipelines, mask tests, realistic foreground simulations |
| Nontrivial topology or anisotropic initial conditions | Changed mode spectrum and/or off-diagonal harmonic covariance | Directional phase observables, matched-circle or covariance tests with calibrated orientation searches |
| A causal-coherence or other proposed mechanism | A specified primordial covariance and transfer to observables | Reproduce proponents' equations; identify a new quantitative prediction; compare competing likelihoods |

An arbitrary multiplicative cutoff imposed directly on C-ell is only a phenomenological toy. It is not automatically a consistent inflationary model. A physical primordial modification must be propagated through transfer functions and polarization predictions. No mechanism in this table is established by the current run.

## Concrete next milestone: map-and-mask closure

1. Freeze the estimator and cuts in a versioned protocol before looking at new diagnostic results.
2. Process SMICA, Commander, NILC and SEVEM with their documented beams and appropriate common masks. Use harmonic smoothing before resolution degradation; track pixel windows.
3. Fit/remove monopole and dipole on exactly the retained sky, and apply the identical operation to every simulated map. Do not equate a masked pseudo-spectrum with an unbiased full-sky estimate.
4. Measure angular-bin pair correlations or a justified pseudo-spectrum/mask-correlation estimator. Test closure on simulations with known input covariance.
5. Repeat with foreground and noise realizations or Planck FFP/NPIPE simulations. Treat the small available end-to-end ensemble as a limit on tail resolution.
6. Report full-sky and cut-sky results side by side. A disagreement is information about the estimator and sky region, not permission to choose the smallest p.
7. Extend to polarization only after using the joint TT/TE/EE covariance and measurement noise. Conditioning on temperature is essential; TE couples the observables.

The present download and map renderer are ready for this work, but a validated masked-sky inference pipeline has **not** been implemented or run in version 0.1.0. Neither cold-spot wavelets nor quadrupole-octopole alignment are claimed as measured here.

## What would justify claiming a discovery?

A mechanism must give a quantitative, reproducible prediction that differs from competing models; the measured discrepancy must survive matched data processing, nuisance uncertainty, and the actual search procedure; and the claim must withstand independent scientific review. The current outputs are a research starting point and numerical reproduction, not that endpoint.
