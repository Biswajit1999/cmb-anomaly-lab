"""Execute every notebook code cell and export a read-only HTML companion."""
from pathlib import Path
import os
import json
import subprocess
import argparse
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

root=Path(__file__).resolve().parents[1]
args=argparse.ArgumentParser(description=__doc__)
args.add_argument('--export-only',action='store_true',help='Preserve saved execution; rebuild HTML and verify outputs')
args.add_argument('--notebook',default='Planck_CMB_Research_Lab',choices=['Planck_CMB_Research_Lab','Planck_CMB_Advanced_Inference'])
args=args.parse_args()
path=root/'notebooks'/f'{args.notebook}.ipynb'
nb=nbformat.read(path,as_version=4)
def progress(cell,cell_index,**kwargs):
    if cell.cell_type=='code': print(f'Executing cell {cell_index+1}/{len(nb.cells)}',flush=True)
if not args.export_only:
    pinned=nb.metadata.research.source_revision
    head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    work=root
    if head!=pinned:
        work=root/'tmp'/f'notebook-runtime-{pinned[:12]}'
        if not (work/'.git').exists():
            subprocess.run(['git','clone','--quiet','--no-hardlinks',str(root),str(work)],check=True)
        subprocess.run(['git','-C',str(work),'checkout','--quiet',pinned],check=True)
        source=root/'data/raw/COM_CMB_IQU-smica_2048_R3.00_full.fits'
        target=work/'data/raw'/source.name
        if source.exists() and not target.exists():
            try: target.symlink_to(source)
            except OSError: pass  # The notebook downloader retrieves it when symlinks are unavailable.
    os.environ['CMB_WORKSPACE']=str(work)
    client=NotebookClient(nb,timeout=1800,kernel_name='python3',resources={'metadata':{'path':str(root)}},on_cell_start=progress)
    try:
        client.execute()
    finally:
        nbformat.write(nb,path)
code_cells=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type=='error' for c in code_cells for o in c.outputs)
exporter=HTMLExporter(template_name='lab')
body,_=exporter.from_notebook_node(nb)
body=body.replace('<title>Notebook</title>',f'<title>{args.notebook.replace("_"," ")} | Biswajit Jana</title>')
# FileLink renders an execution-host absolute path; publish a portable link instead.
body=body.replace(str(root/'results/cmb_conditional_research_outputs.zip'),'../results/cmb_conditional_research_outputs.zip')
if args.notebook=='Planck_CMB_Advanced_Inference':
    body=body.replace('href="results.json"','href="../results/conditional/results.json"')
path.with_suffix('.html').write_text(body,encoding='utf-8')
audit={'author':'Biswajit Jana','code_cells':len(code_cells),'executed_code_cells':len(code_cells),
       'errors':0,'execution_environment':'Local Python kernel; notebook is Google Colab compatible',
       'counts':[c.execution_count for c in code_cells]}
audit['source_revision']=nb.metadata.research.source_revision
audit_name='execution_audit.json' if args.notebook=='Planck_CMB_Research_Lab' else 'advanced_execution_audit.json'
(root/'notebooks'/audit_name).write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit),flush=True)
