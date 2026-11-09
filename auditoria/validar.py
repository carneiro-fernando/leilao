from pathlib import Path
import hashlib,json,re
R=Path.cwd();errors=[]
inv=json.loads(Path('auditoria/inventario_original.json').read_text())
for x in inv:
 p=Path(x['arquivo'])
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=x['sha256']:errors.append('Original alterado: '+str(p))
for p in Path('memoria').glob('*.md'):
 limit=60 if p.name=='00_indice.md' else 300
 if len(p.read_text().splitlines())>limit:errors.append('Limite: '+str(p))
assert len(Path('AGENTS.md').read_text().splitlines())<=120
created=json.loads(Path('auditoria/arquivos_criados.json').read_text())
for f in created:
 p=Path(f)
 if p.suffix!='.md':continue
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('http:','https:','#')):continue
  target=target.split('#')[0].strip('<>')
  if not (p.parent/target).exists():errors.append('Link inexistente: '+f+' -> '+target)
for f,n in [('Edital',12),('Carros_lista',12),('comprovacao_de_propriedade',18),('Resolucao_SGGD',2),('Resolucao_Contran',3)]:
 t=Path('fontes/md/'+f+'.md').read_text();assert len(re.findall(r'<!-- p\. \d+ -->',t))==n
assert len(list(Path('lotes').glob('*.md')))==14
assert len(re.findall(r'^\| I-\d+',Path('fontes/md/Carros_lista_tabela.md').read_text(),re.M))==543
assert len(re.findall(r'^\| V-\d+',Path('fontes/md/comprovacao_de_propriedade_tabela.md').read_text(),re.M))==600
report={'data':'2026-11-08','originais_verificados':len(inv),'originais_inalterados':not any('Original' in e for e in errors),'fichas':14,'linhas_anexo_I':543,'posicoes_anexo_V':600,'links_e_limites':not errors,'erros':errors}
with Path('auditoria/validacao.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
print(json.dumps(report,ensure_ascii=False,indent=2))
