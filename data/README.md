# What the inputs are

The files in `raw/` come directly from the [NASA/IPAC IRSA Planck PR3 archive](https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/). `manifest.json` records source URLs, retrieval times, exact sizes, and SHA-256 fingerprints. These fingerprints establish consistency with the retrieved files; they are not publisher-signed certificates.

1. **COM_PowerSpect_CMB-TT-full_R3.01.txt:** published unbinned temperature power-spectrum estimates. Columns are ell, D-ell, lower error, upper error. D-ell is ell(ell+1)C-ell/(2 pi), in microkelvin squared. These are processed measurement estimates, not independent detector samples.
2. **COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt:** best-fit theoretical spectra. Column 1 is ell; column 2 is TT D-ell in microkelvin squared. Other columns are not used. This is a model prediction, not a second observation.
3. **COM_CMB_IQU-smica_2048_R3.00_full.fits:** original PR3 SMICA map product from the [CMB map archive](https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html). Required for the map experiment, optional for the spectrum-only experiment. `I_STOKES` is used for temperature analysis/display and `TMASK` for confidence masking. FITS header units and ordering are inspected; kelvin becomes microkelvin by multiplication by 10^6. The separately labelled inpainted columns are not used; this does not imply the released component-separation product has no upstream inpainting or cleaning assumptions.

Low multipoles and high multipoles in the published spectrum come from different estimation regimes. Combining their point estimates does not preserve the full data likelihood. Accordingly, reported significance is explicitly a full-sky Gaussian reference approximation. The largest default multipole is 64; sensitivity checks extend to 128. The low-variance and parity bands end at 29.

Map pixel averaging to NSIDE 256 is solely a display operation. It is not a harmonic estimator, does not preserve every small-scale mode, and is never used for the main Monte Carlo statistics.

The v0.2.0 map analysis takes a separate path: native-resolution harmonic extraction through ell=128, documented beam and pixel windows, synthesis at NSIDE=32, confidence masking and a retained-sky monopole/dipole fit. Both observed and Gaussian simulated maps receive the same output processing. The mask retains pixels whose native confidence fraction is at least 0.95, with a 0.99 variant. See [map methods](../docs/map-methods.md).

The CAMB extension computes its own TT/TE/EE spectra at a fixed near-Planck cosmology. It reports the difference from the archived best fit; its model spectra and polarization predictions are not new measured data.

The archive offers newer NPIPE/PR4 products as well. PR3 was selected here for a compact, stable, well-documented combination of a public spectrum, best-fit theory, and map. The reading guide covers subsequent work; this repository does not imply PR3 is the latest available processing.

## Reuse

Credit ESA and the Planck Collaboration and the NASA/IPAC Infrared Science Archive. The repository's MIT license does not transfer ownership of these scientific products. Original Planck papers are linked in the reading guide. Large FITS products and regenerated Monte Carlo arrays are excluded from Git; the small original text spectra and their hashes are included for offline reproduction.
