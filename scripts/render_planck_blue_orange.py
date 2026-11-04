"""Render measured PR3 SMICA in an ESA-inspired blue/cream/orange palette.

Author: Biswajit Jana. The palette is our visualization, not an ESA image copy.
Full-sky display does not imply foreground-clean confidence in every pixel.
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import healpy as hp
from astropy.io import fits
from cmb_lab.data import sha256
from cmb_lab.plots import style


def read_display(root, nside=512):
    record=json.loads((root/'data/manifest.json').read_text())['smica']
    path=root/record['path']
    if sha256(path)!=record['sha256']:
        raise ValueError('Measured FITS file checksum mismatch')
    with fits.open(path,memmap=True) as h:
        if h[1].columns['I_STOKES'].unit!='K_CMB':
            raise ValueError('Unexpected temperature unit')
        order=h[1].header['ORDERING']
        sky=hp.ud_grade(h[1].data['I_STOKES'].ravel(),nside,order_in=order,order_out='RING')*1e6
        fraction=hp.ud_grade(h[1].data['TMASK'].ravel().astype(float),nside,order_in=order,order_out='RING')
    return sky,fraction,record


def render(root, sky, fraction, record):
    style()
    cmap=LinearSegmentedColormap.from_list('cmb_blue_orange',
        ['#083478','#147cc1','#69c8e8','#f4f3ca','#ffd365','#ed972f','#a74714'],N=256)
    out=root/'results/maps'; out.mkdir(parents=True,exist_ok=True)
    for masked,name,title in [(False,'planck_fullsky','Planck 2018 | measured SMICA temperature'),
                              (True,'planck_blue_orange_masked','Planck 2018 | confidence-masked temperature')]:
        field=hp.ma(sky)
        field.mask=(fraction<.95) if masked else (~np.isfinite(sky))
        fig=plt.figure(figsize=(12,6.2))
        hp.mollview(field,fig=fig.number,min=-300,max=300,cmap=cmap,badcolor='#d7dfe5',
                    title=title,unit=r'$\Delta T$ [$\mu$K]',coord='G',xsize=1600)
        note='Grey: temperature confidence mask.' if masked else 'Full-sky display; confidence exclusions are shown in the companion map.'
        fig.text(.5,-.075,'Biswajit Jana | CMB Anomaly Lab\nESA / Planck Collaboration measurements | Galactic coordinates\n'+note,
                 ha='center',fontsize=9)
        fig.savefig(out/f'{name}.png',dpi=180,bbox_inches='tight')
        fig.savefig(out/f'{name}.pdf',bbox_inches='tight')
        plt.close(fig)
    provenance={'author':'Biswajit Jana','source_sha256':record['sha256'],'source_url':record['url'],
        'display_nside':hp.npix2nside(len(sky)),'units':'microkelvin','limits':[-300,300],
        'coordinate_system':'Galactic','palette':'custom blue-cream-orange, inspired by Planck outreach images',
        'processing':'native pixel averaging for visualization only; not the map-statistics estimator',
        'full_sky_is_unmasked_display':True,'confidence_mask_min_fraction':.95}
    (out/'blue_orange_provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    return out


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    sky,fraction,record=read_display(root)
    render(root,sky,fraction,record)
    print('Rendered full-sky and masked blue-orange maps from verified Planck measurements.')
