"""Check execution evidence and all local website document/resource links."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
root=Path(__file__).resolve().parents[1]
nb=json.loads((root/'notebooks/Planck_CMB_Research_Lab.ipynb').read_text())
cells=[c for c in nb['cells'] if c['cell_type']=='code']
assert [c['execution_count'] for c in cells]==list(range(1,20))
assert not [o for c in cells for o in c['outputs'] if o['output_type']=='error']
images=sum('image/png' in o.get('data',{}) for c in cells for o in c['outputs'])
assert images>=8, 'Expected executed map and research-figure outputs'
assert nb['metadata']['authors'][0]['name']=='Biswajit Jana'
advanced=json.loads((root/'notebooks/Planck_CMB_Advanced_Inference.ipynb').read_text())
advanced_cells=[c for c in advanced['cells'] if c['cell_type']=='code']
assert [c['execution_count'] for c in advanced_cells]==list(range(1,14))
assert not [o for c in advanced_cells for o in c['outputs'] if o['output_type']=='error']
assert advanced['metadata']['authors'][0]['name']=='Biswajit Jana'
assert sum('image/png' in o.get('data',{}) for c in advanced_cells for o in c['outputs'])>=4
assert '\\operatorname' not in (root/'README.md').read_text(encoding='utf-8')
class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in {'href','src'} and value: self.links.append(value)
missing=[]; count=0
for path in (root/'_site').rglob('*.html'):
    parser=Links(); parser.feed(path.read_text(encoding='utf-8'))
    for link in parser.links:
        u=urlsplit(link)
        if u.scheme or u.netloc or not u.path: continue
        target=(path.parent/unquote(u.path)).resolve()
        count+=1
        if not target.exists(): missing.append((str(path.relative_to(root)),link))
assert not missing, missing
print(json.dumps({'executed_cells':len(cells),'advanced_executed_cells':len(advanced_cells),'embedded_output_images':images,'local_links_checked':count,'missing_links':0,'readme_macro_check':'passed'}))
