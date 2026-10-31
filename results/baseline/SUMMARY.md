# Computed results

Generated from the official PR3 TT estimates; all p-values below use an idealized full-sky Gaussian reference. They are not official Planck likelihood results.

| Diagnostic | Observed | Lower-tail p | 95% Monte Carlo interval |
|---|---:|---:|---:|
| quadrupole | 236.557 | 0.04699 | 0.04568 - 0.04831 |
| s_half | 6767.53 | 0.07521 | 0.07357 - 0.07685 |
| parity_2_29 | 0.762881 | 0.01011 | 0.00949 - 0.01074 |
| variance_2_29 | 2074.52 | 0.10353 | 0.10164 - 0.10542 |

Four-test minimum-p family calibration: **0.03792**.
All declared fixed/scan tests: **0.03013**.
Parity cutoff scan (10-29), corrected: **0.01327**.
Angular threshold scan (45-90 degrees), corrected: **0.11577**.

These corrections cover only the declared finite families, not all historical choices or all follow-up diagnostics.

## Holding the quadrupole fixed

- s_half: conditional p = 0.48423.
- parity_2_29: conditional p = 0.02989.
- variance_2_29: conditional p = 0.40245.

Conditioning is a diagnostic. It removes the probability cost of the low quadrupole, assumes its published estimate is exact, and does not establish a physical cause.

## Resolution of the experiment

Reference spectra: 100,000; independent calibration spectra: 100,000.
The conditional ensemble reuses the calibration skies with C2 replaced. Zero observed events never imply zero probability. See results.json for exact counts, confidence intervals, source hashes, and software versions.
