import json,re,collections
from pathlib import Path
p=Path('tmp/analise')
allrows=[]
a=json.loads((p/'Carros_lista_strips.json').read_text())
for meta in json.loads((p/'Carros_lista_lines.json').read_text()):
 page=meta['page'];h=meta['height'];lines=meta['lines'];obs=[o for o in a if o['page']==page]
 edges=[.048,.067,.103,.183,.294,.333,.413,.516,.554,.64,.693,.767,.951]
 for upper,lower in zip(lines[1:-1],lines[2:]):
  cells=[]
  for c in range(12):
   tokens=[o for o in obs if upper<= (1-o['y'])*h <lower and edges[c]-.002<=o['x']<edges[c+1]-.002]
   tokens.sort(key=lambda o:(-round(o['y']/0.002),o['x']))
   cells.append(' '.join(o['text'] for o in tokens).replace('|','/'))
  allrows.append({'page':page,'cells':cells})
(p/'lotes_rows.json').write_text(json.dumps(allrows,ensure_ascii=False,indent=2))
print(len(allrows));print(*allrows[:4],sep='\n');print(*allrows[-7:],sep='\n')
