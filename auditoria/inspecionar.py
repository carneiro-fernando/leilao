from pathlib import Path
from pypdf import PdfReader
from PIL import Image
import json,hashlib,re
root=Path.cwd(); rows=[]
for p in sorted(root.rglob('*')):
 if not p.is_file() or p.relative_to(root).parts[0] in ['auditoria','memoria','fontes','lotes','templates']: continue
 b=p.read_bytes(); x={'arquivo':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'tipo':p.suffix,'paginas':None,'texto_extraivel':'não se aplica'}
 if p.suffix=='.pdf':
  pdf=PdfReader(p); ts=[pg.extract_text() or '' for pg in pdf.pages]; x.update(paginas=len(ts),caracteres_por_pagina=[len(t.strip()) for t in ts],texto_extraivel='sim' if all(len(t.strip())>100 for t in ts) else 'não / insuficiente; OCR necessário')
 elif p.suffix in ['.png','.webp']:
  with Image.open(p) as im: x['dimensoes']=list(im.size); im.verify()
 elif p.suffix in ['.md','.txt','.swift','.py','.csv','.html','.json']:
  t=b.decode('utf-8');x['linhas']=len(t.splitlines());x['texto_extraivel']='sim' if t else 'vazio'
  if p.suffix=='.json':
   j=json.loads(t);x['estrutura']=f'{type(j).__name__}: {len(j)} elementos'
 rows.append(x)
Path('auditoria/inventario_original.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
print('Arquivos originais:',len(rows))
for x in rows:
 if x['tipo']=='.pdf':print(x['arquivo'],x['paginas'],x['texto_extraivel'],x['caracteres_por_pagina'])
