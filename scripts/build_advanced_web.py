"""Insert a result-driven advanced research section into the existing static site."""
from pathlib import Path
import json
import re
root=Path(__file__).resolve().parents[1]
r=json.loads((root/'results/conditional/results.json').read_text())
labels={'gaussian':'Gaussian theory','fixed_power':'Measured powers fixed','rotation':'Measured pattern rotated'}
rows=''.join(f'<tr><th scope="row">{labels[n]}</th><td>{e["statistics"]["cut_sky_s_half"]["p"]:.4f}</td><td>{e["statistics"]["hemisphere_max_contrast"]["p"]:.4f}</td><td>{e["simultaneous_band"]["independent_validation_coverage"]["rate"]:.1%}</td></tr>' for n,e in r['ensembles'].items())
section=f'''<!-- ADVANCED-START -->
<section id="advanced" class="advanced-section wrap" aria-labelledby="advanced-title">
<div class="section-label">03 / RESEARCH EXTENSION · 8 NOVEMBER 2026</div>
<div class="editorial-grid"><div><h2 id="advanced-title">Power is only part<br>of the pattern.</h2><p>Hold every angular power fixed. Rearrange the harmonic structure. Then rotate the complete measured sky relative to the Galactic mask.</p><p>Three controlled experiments separate questions that a single anomaly probability cannot answer.</p></div><div><h3>13 more executed Python cells</h3><p>The advanced notebook runs 18,432 null and randomized skies, followed by 5,120 paired signal injections. Saved outputs include measured and randomized maps, simultaneous correlation envelopes and detection-power curves.</p><div class="link-stack"><a class="button primary" href="notebooks/Planck_CMB_Advanced_Inference.html">Read the advanced notebook →</a><a class="text-link" href="https://colab.research.google.com/github/Biswajit1999/cmb-anomaly-lab/blob/main/notebooks/Planck_CMB_Advanced_Inference.ipynb">Run the advanced notebook in Colab ↗</a></div><p class="note">All 13 cells executed locally with real Planck inputs. The notebook is Colab compatible.</p></div></div>
<figure class="science-figure"><img src="results/conditional/figures/conditional_tails.png" width="2160" height="1152" loading="lazy" alt="Comparison of four CMB statistics under Gaussian, fixed measured power and globally rotated sky ensembles"><figcaption>Each ensemble answers a different question. Error bars measure Monte Carlo counting uncertainty. These probabilities are not pooled into a discovery significance.</figcaption></figure>
<div class="table-scroll" tabindex="0" role="region" aria-label="Conditional analysis results"><table class="research-table"><caption>Independent calibration and held-out validation</caption><thead><tr><th scope="col">Null ensemble</th><th scope="col">Correlation S lower-tail p</th><th scope="col">Hemisphere upper-tail p</th><th scope="col">Held-out envelope coverage</th></tr></thead><tbody>{rows}</tbody></table></div>
<div class="editorial-grid"><div><h3>Can the test detect an injected signal?</h3><p>Five toy dipole-modulation amplitudes are tested against a threshold fixed by independent Gaussian skies. Detection power and direction recovery reveal what a nondetection can—and cannot—tell us.</p><a href="results/conditional/SUMMARY.html">Read the results and injection curves →</a></div><div><h3>Where the inference stops</h3><p>These experiments use processed full-sky coefficients. Foreground uncertainty and mixing across mask boundaries remain. The modulation is injected after smoothing; it is not a fitted primordial amplitude.</p><a href="docs/conditional-methods.html">Read the derivations and limitations →</a></div></div>
<p class="note">Three independent held-out sets check the 95% simultaneous prediction envelopes on 121 specified angles. <a href="results/conditional/validation.json">Validation record</a> · <a href="results/cmb_conditional_research_outputs.zip" download>Download numerical outputs</a></p>
</section>
<!-- ADVANCED-END -->'''
path=root/'index.html'; text=path.read_text(encoding='utf-8')
if '<!-- ADVANCED-START -->' in text:
    text=re.sub(r'<!-- ADVANCED-START -->.*?<!-- ADVANCED-END -->',lambda _:section,text,flags=re.S)
else:
    text=text.replace('<section class="methods-section',section+'\n\n<section class="methods-section')
text=text.replace('"dateModified":"2026-11-04"','"dateModified":"2026-11-08"')
text=text.replace('<dt>18</dt><dd>numerical tests passed','<dt>28</dt><dd>numerical tests passed')
text=text.replace('<dt>20</dt><dd>primary papers','<dt>21</dt><dd>primary papers')
text=text.replace('03 / FROM ANGULAR MODES','04 / FROM ANGULAR MODES').replace('04 / THE RESEARCH LIBRARY','05 / THE RESEARCH LIBRARY')
text=text.replace('16 pages · equations, figures, sources','Expanded report · equations, figures, sources')
text=text.replace('The Python notebook takes you','The introductory Python notebook takes you')
if 'href="#advanced">Advanced' not in text:
    text=text.replace('<a href="#findings">Findings</a>','<a href="#findings">Findings</a><a href="#advanced">Advanced</a>')
path.write_text(text,encoding='utf-8')
print('Updated website from executed conditional results')
