# Beyond low power: conditional morphology, orientation and detection power

Author: **Biswajit Jana** · 8 November 2026 · Exploratory research extension

The original map study compares SMICA with an isotropic Gaussian theory. This extension asks which aspects of the observed sky the comparison uses. It separates three hypotheses and tests the sensitivity of the hemisphere statistic with injected signals. These are established statistical ideas applied in this repository, not a claim of a new cosmological mechanism.

## Three distinct ensembles

| Ensemble | What is held fixed? | What varies? | Question |
|---|---|---|---|
| Gaussian theory | Best-fit theoretical spectrum | Powers and harmonic directions | How unusual is the measured statistic under the ideal CMB-only theory? |
| Measured powers fixed | Every measured full-sky power, ell=2–128 | Independent harmonic directions at each ell | Does the cut-sky morphology add unusual structure beyond those powers? |
| Measured pattern rotated | The complete harmonic pattern, including relative multipole geometry | One Haar-uniform global rotation | Is the pattern's orientation relative to the fixed mask and finite axis grid unusual? |

The latter two are conditional randomization experiments. They are not new data, independent cosmologies, or adjustments to the unconditional p-value. We do not combine their probabilities or select the smallest as a discovery statistic.

## Conditional harmonic sampling

For a real temperature field, collect the independent real coefficients at each multipole:

$$\mathbf u_\ell=(a_{\ell0},\sqrt{2}\,\Re a_{\ell1},\sqrt{2}\,\Im a_{\ell1},\ldots),\qquad d_\ell=2\ell+1.$$

Under the isotropic Gaussian model this vector is spherical. Conditional on its length, its direction is uniform on the sphere in d dimensions. We therefore draw a standard normal vector and normalize its length:

$$\mathbf u_\ell^*=\sqrt{(2\ell+1)\widehat C_\ell}\frac{\mathbf z_\ell}{\|\mathbf z_\ell\|},\qquad \mathbf z_\ell\sim\mathcal N(0,I).$$

The code implements this through HEALPix's compressed complex coefficients and `alm2cl`, retaining the correct m=0 versus m>0 weights. This randomizes relative amplitudes as well as phases. Merely drawing independent complex phases would **not** sample the conditional Gaussian direction distribution. Every realization is checked for power preservation.

Useful exact checks are E[u_i²]=C and E[u_i⁴]=3d C²/(d+2). Unit tests check these moments and the monopole/dipole zeros. Conditioning removes the random lengths from the ensemble; it does not estimate their uncertainty or explain why the measured powers are small.

## Haar-uniform rotations

$$a_{\ell m}^{R}=\sum_{m'}D^\ell_{mm'}(R)a_{\ell m'},\qquad d\mu(R)=\frac{d\alpha\,d\gamma\,d(\cos\beta)}{8\pi^2}.$$

We draw both azimuthal Euler angles uniformly on [0,2π), and cos(beta) uniformly on [-1,1]. Drawing beta uniformly would overrepresent polar orientations. `healpy.rotate_alm` uses Wigner matrices in harmonic space, avoiding pixel-interpolation artifacts. A global rotation preserves all powers **and** the relative geometry between multipoles, whereas independent conditional directions preserve only the powers. The observed mask remains fixed. Tests check power conservation and isotropic angular moments.

## Matched estimator and provenance

All three ensembles use the existing [map estimator](map-methods.md): native-resolution harmonic extraction, ell≤128, a 5-degree beam and NSIDE=32 pixel window, mask fraction≥0.95, retained-pixel monopole/dipole projection, correlation bandlimit 95 and the same 24-axis hemisphere search. The four one-sided diagnostics and their four-test family calibration are retained unchanged. The input file is SHA-256 verified before cached harmonics are used. Source hashes and package versions are recorded in [results](../results/conditional/results.json).

The **processed full-sky** SMICA coefficients determine the conditional powers and rotation template. They include information inside excluded regions. Global harmonic filtering before masking also mixes information across mask boundaries. These are explicitly not estimators that only use uncontaminated raw pixels. Foreground cleaning, noise, mask selection and cosmological-parameter uncertainties remain outside these idealized nulls.

## Simultaneous correlation envelopes

Pointwise 95% ranges do not generally cover an entire curve 95% of the time. We fit a mean and standard deviation using only 1,024 reference curves and define

$$M(C)=\max_{\theta\in\{60^\circ,61^\circ,\ldots,180^\circ\}}\left|\frac{C(\theta)-\mu_{\rm ref}(\theta)}{s_{\rm ref}(\theta)}\right|.$$

An independent set of 4,096 calibration curves provides the order-statistic cutoff with rank ceil((n+1)×0.95). A new curve is outside if its score is strictly greater. This gives a finite-sample marginal prediction guarantee under exchangeability, conditional on the reference fit and idealized null, with conservative handling of ties. A further 1,024 held-out curves measure coverage and supply binomial counting intervals. The guarantee concerns the **121 sampled angles**, not the continuum or the ensemble mean.

This is a two-sided maximum-deviation test. A low integral of squared correlation and a large standardized departure from the null mean are different events; their p-values need not agree. The four-diagnostic family does not include this separate envelope test. We do not report an overall project-wide significance.

## Injection and recovery

$$T_A(\hat n)=[1+A(\hat n\cdot\hat p)]T_{\rm smoothed}(\hat n).$$

We inject A=0,0.05,0.10,0.20,0.30 into 1,024 independent Gaussian skies, reusing the same underlying skies across amplitudes to reduce comparison noise. A fixed illustrative Galactic axis (225°,−27°) was chosen before these trials; it is neither fitted here nor claimed as a measured direction. The threshold for the maximum hemisphere contrast is fixed from the independent Gaussian calibration ensemble at a nominal 5% false-alarm level. Every injection repeats the full mask, projection and axis search.

Modulation is applied **after smoothing**, so this is a test of sensitivity to a beam-scale toy signal, not a forward model of primordial modulation. We report detection fraction with exact binomial intervals and unsigned axis error arccos(|d·p|) for all trials, not only detections. Amplitude rows are paired and hence statistically correlated. A weak test can fail to reject even a nonzero signal: a nondetection is not an exclusion limit on A.

## Reading and methodological context

- [Planck 2018 VII](https://arxiv.org/abs/1906.02552): broad temperature/polarization isotropy context. Abstract and relevant search excerpts consulted; the full 61-page analysis is not claimed to have been re-reviewed for this extension. Our CMB-only simulations are not Planck end-to-end simulations.
- [Efstathiou, Ma and Hanson (2010)](https://arxiv.org/abs/0911.5399): estimator dependence and sensitivity to sky cuts; methods and discussion consulted. This motivates distinguishing measured full-sky powers from a masked correlation statistic. Their reconstruction approach is not implemented here.
- [Akrami et al. (2014)](https://arxiv.org/abs/1402.0870): sections 1–3 and the dipole-modulation definition consulted. Their local-disc variance dipole estimator and observational simulation treatment differ from our finite hemisphere search. We use modulation to test our own statistic, not to reproduce their reported significance.
- [healpy rotation documentation](https://healpy.readthedocs.io/en/1.20.1/generated/healpy.rotator.rotate_alm.html): API and harmonic rotation convention consulted.

All these method choices are retrospective and literature motivated. Fixing a configuration before a new simulation run is useful for reproducibility but is not preregistration before observing the sky.

## Reproduction

```bash
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
python scripts/analyze_conditional.py
python scripts/validate_conditional.py
```

The full run generates **18,432 null/randomization realizations** plus **5,120 paired injected maps**. CSV tables are published; intermediate compressed ensembles are recreated by the script. `--quick` writes only to `results/quick/conditional` and checks execution, not scientific precision.
