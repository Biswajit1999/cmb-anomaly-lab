"""Package explicit public artifacts for GitHub Pages; omit raw FITS and caches."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
dest=root/'_site'; dest.mkdir(exist_ok=True)
for name in ['index.html','CITATION.cff','AUTHORS.md','AUTHORS.html','LICENSE','README.md','sitemap.xml','robots.txt']:
    shutil.copy2(root/name,dest/name)
for folder in ['site','reports','notebooks','docs','config','results','scripts','src','tests']:
    for path in (root/folder).rglob('*'):
        if not path.is_file() or 'quick' in path.parts or path.suffix not in {'.html','.css','.js','.json','.md','.png','.pdf','.csv','.ipynb','.py','.zip'}:
            continue
        target=dest/path.relative_to(root); target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
(dest/'data').mkdir(exist_ok=True)
shutil.copy2(root/'data/manifest.json',dest/'data/manifest.json')
for path in (root/'data').glob('README.*'):
    shutil.copy2(path,dest/'data'/path.name)
(dest/'.nojekyll').touch()
print('Packaged static research website in _site')
