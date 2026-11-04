# Measured SMICA map analysis

Matched finite-band map estimators under an ideal Gaussian CMB-only null; not Planck end-to-end likelihood significances.

| Variant | Statistic | Observed | Tail p | 95% MC interval |
|---|---|---:|---:|---|
| baseline | cut_sky_s_half | 2036.81 | 0.00805 | 0.00535 - 0.01101 |
| baseline | masked_variance | 1590.52 | 0.04369 | 0.03742 - 0.05016 |
| baseline | pseudo_parity | 0.762403 | 0.01855 | 0.01443 - 0.02290 |
| baseline | hemisphere_max_contrast | 0.310849 | 0.08055 | 0.07218 - 0.08907 |
| stricter_mask | cut_sky_s_half | 1985.11 | 0.00659 | 0.00415 - 0.00929 |
| stricter_mask | masked_variance | 1582.49 | 0.04174 | 0.03560 - 0.04807 |
| stricter_mask | pseudo_parity | 0.774671 | 0.02441 | 0.01969 - 0.02935 |
| stricter_mask | hemisphere_max_contrast | 0.312029 | 0.08055 | 0.07218 - 0.08907 |
| broader_smoothing | cut_sky_s_half | 1767.85 | 0.00610 | 0.00376 - 0.00871 |
| broader_smoothing | masked_variance | 1217.25 | 0.05370 | 0.04678 - 0.06080 |
| broader_smoothing | pseudo_parity | 0.729427 | 0.02075 | 0.01639 - 0.02533 |
| broader_smoothing | hemisphere_max_contrast | 0.355647 | 0.09617 | 0.08710 - 0.10538 |

Twelve-column family calibration: 0.03100. This covers these variants, not historical statistic selection.

The hemisphere statistic includes the complete finite direction search on every realization. The pseudo-parity statistic is a mask-dependent diagnostic, not a full-sky power estimate.
