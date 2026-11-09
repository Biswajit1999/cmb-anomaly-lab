"""Render research Markdown as readable website pages using notebook Markdown."""
from pathlib import Path
import re
import nbformat
from nbconvert import HTMLExporter
root=Path(__file__).resolve().parents[1]
files=[*sorted((root/'docs').glob('*.md')),root/'AUTHORS.md',root/'data/README.md',
       root/'results/baseline/SUMMARY.md',root/'results/masked_sky/SUMMARY.md',root/'results/conditional/SUMMARY.md']
destinations={p.resolve():p.with_suffix('.html') for p in files}
exporter=HTMLExporter(template_name='lab')
for path in files:
    source=path.read_text(encoding='utf-8')
    def links(match):
        label,url=match.groups()
        if url.startswith(('http','#','mailto:')): return match.group(0)
        target=(path.parent/url.split('#')[0]).resolve()
        if target in destinations: url=url.replace('.md','.html')
        return f'[{label}]({url})'
    source=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',links,source)
    home='../'*len(path.relative_to(root).parts[:-1])+'index.html'
    nb=nbformat.v4.new_notebook(cells=[nbformat.v4.new_markdown_cell(f'[CMB Anomaly Lab · Biswajit Jana]({home})\n\n'+source)])
    html,_=exporter.from_notebook_node(nb)
    html=html.replace('<title>Notebook</title>',f'<title>{source.splitlines()[0].lstrip("# ")} | Biswajit Jana</title>')
    path.with_suffix('.html').write_text(html,encoding='utf-8')
print(f'Rendered {len(files)} research documents')
