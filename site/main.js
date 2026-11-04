const image = document.querySelector('#sky-image');
const caption = document.querySelector('#sky-caption');
const maps = {
  full: {src:'results/maps/planck_fullsky.png',alt:'Blue-orange Mollweide map of the measured Planck PR3 SMICA temperature sky in Galactic coordinates',caption:'Full-sky display of measured SMICA temperatures. Some pixels are excluded from the statistical analysis; select Confidence mask to see them. The custom blue-orange palette represents temperature, from −300 to +300 μK.'},
  masked: {src:'results/maps/planck_blue_orange_masked.png',alt:'Measured Planck temperature sky with confidence-excluded pixels shown in grey',caption:'Grey pixels have a retained native confidence fraction below 0.95. This display uses NSIDE 512; the quantitative map experiment uses a separate native-harmonic processing path and NSIDE 32.'}
};
document.querySelectorAll('[data-map]').forEach(button => button.addEventListener('click', () => {
  const selected = maps[button.dataset.map];
  image.src = selected.src; image.alt = selected.alt; caption.textContent = selected.caption;
  document.querySelectorAll('[data-map]').forEach(item => item.setAttribute('aria-pressed',String(item===button)));
}));
