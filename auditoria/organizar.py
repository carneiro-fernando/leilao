from pathlib import Path
import json,re,csv,hashlib,difflib,collections
from pypdf import PdfReader
R=Path.cwd(); D='2026-11-08'; created=[]
def put(p,t):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(t.rstrip()+'\n')
 created.append(str(p))
def read(p):return Path(p).read_text()
def pages(t):
 a=re.split(r'=== PÁGINA (\d+) ===\n',t);return [(int(a[i]),a[i+1].strip()) for i in range(1,len(a),2)]
def clean(t):
 t=re.sub(r'026[,\.]\s*\*{3}[ .]*\*{3}-00','[dado pessoal omitido]',t)
 return t
meta={'Edital':('Edital do leilão 003/2026','edital','SGGD/DMI','003/2026','não verificado'), 'Carros_lista':('Anexo I — veículos com documentação','lista de lotes','SGGD/DMI','003/2026','não verificado'),'comprovacao_de_propriedade':('Anexo V — comprovação de propriedade','tabela','SGGD/DMI','003/2026','não verificado'),'Resolucao_SGGD':('Resolução SGGD 28/2024','norma','SGGD','28/2024','2024-08-06'),'Resolucao_Contran':('Resolução CONTRAN 1.025/2026','norma','CONTRAN','1.025/2026','2026-06-30')}
av=next(Path('.').glob('aviso*.pdf'));meta[av.stem]=('Aviso de licitação 003/2026','aviso','SGGD/DMI','003/2026','2026-10-20')
source_text={}
for stem,(title,typ,org,num,date) in meta.items():
 pdf=PdfReader(stem+'.pdf');method='texto' if stem=='Resolucao_Contran' else 'OCR'
 # Existing OCR has page anchors; preserve it rather than rerun old scripts that overwrite files.
 t=read('tmp/analise/'+stem+'.txt');source_text[stem]=t
 assert len(pages(t))==len(pdf.pages)
 conf='alta' if method=='texto' else ('baixa' if typ in ['tabela','lista de lotes'] else 'media')
 front='---\n'+''.join(k+': '+json.dumps(v,ensure_ascii=False)+'\n' for k,v in dict(titulo=title,tipo=typ,orgao=org,numero=num,data_publicacao=date,paginas=len(pdf.pages),origem=stem+'.pdf',metodo=method,convertido_em=D,confianca=conf).items())+'---\n\n'
 note='> Extração documental; não certifica vigência atual. '+('OCR preexistente reutilizado, com conferência amostral nesta sessão. Não houve revisão visual integral. ' if method=='OCR' else 'Texto extraível do PDF, comparado com a extração preexistente. ')
 note+='Dados pessoais, inclusive CPF parcialmente mascarado, omitidos quando identificados. Falhas de OCR e tabelas: ver auditoria/conversao.md.\n\n'
 body=''
 for n,pt in pages(t):
  pt=clean(pt); pt=re.sub(r'(?<!\n)(CAPÍTULO [IVX]+)',r'\n\1',pt)
  ls=pt.splitlines();out=[]
  for l in ls:
   if re.match(r'^(CAPÍTULO [IVX]+|Seção [IVX]+)$',l):l='## '+l
   elif stem=='Edital' and re.match(r'^\d+\. [A-ZÁÉÍÓÚÇÃÕ ]{5,}$',l):l='## '+l
   out.append(l)
  body+=f'<!-- p. {n} -->\n\n'+ '\n'.join(out)+'\n\n'
 put('fontes/md/'+stem+'.md',front+note+body)
# Structured, explicitly uncertain table preserving every raw row alongside separable fields.
rows=json.loads(read('tmp/analise/lotes_rows.json'))
head='# Anexo I — tabela de recuperação\n\nFonte: Carros_lista.pdf; OCR herdado em tmp/analise/lotes_rows.json. Data: '+D+'. Confiança baixa.\nCada linha física está preservada. ID de busca não é lote. Campos não recuperados: [ilegível]. Texto bruto permite auditar junções; não inferir ausência de defeitos.\n\n'
prev=None
for idx,r in enumerate(rows,1):
 if r['page']!=prev:
  prev=r['page'];head+=f'\n<!-- p. {prev} -->\n\n| ID | lote | marca/modelo | ano | placa | chassi | motor | preço mínimo | observação | células OCR originais |\n|---|---|---|---|---|---|---|---|---|---|\n'
 c=r['cells'];lot=c[0] if re.fullmatch(r'\d{1,3}',c[0]) else '[ilegível]';plate=c[1] if re.fullmatch('[A-Z]{3}[0-9][A-Z0-9][0-9]{2}',c[1]) else '[ilegível]'
 ch=re.match(r'^([A-Z0-9]{17})(?:\s+(.*))?$',c[2]);chassi=ch[1] if ch else '[ilegível]';model=c[3] or (ch[2] if ch and ch[2] else '[ilegível]')
 price=re.match(r'^(R\$\s*[\d.,]+)(?:\s+(.*))?$',c[10]); val=price[1] if price else '[ilegível]';obs=' '.join(x for x in [(price[2] if price else ''),c[11]] if x) or 'não verificado'
 # Visually verified first two rows, no edits to original OCR.
 if idx==1:lot='2';plate='EEF1718';chassi='93W245G3392030029';model='FIAT/DUCATO MAXICARGO';val='R$ 6.500,00';obs='MOTOR E CAMBIO FALTANDO PARTES E PEÇAS'
 if idx==2:lot='4';plate='DJP2753';chassi='9BG138GJ09C404587';model='GM/S10 COLINA D';val='R$ 13.800,00'
 vals=[f'I-{idx:04}',lot,model,c[4] or '[ilegível]',plate,chassi,('M1A324012' if idx==2 else c[8]) or '[ilegível]',val,obs,' / '.join(c)]
 head+='| '+' | '.join(v.replace('|','/').replace('\n',' ') for v in vals)+' |\n'
put('fontes/md/Carros_lista_tabela.md',head)
# Retain existing reconstruction of property records, with physical page anchors.
legacy=read('contexto_memoria_leilao_003_2026.md')
prop=legacy.split('## 10. Base de comprovação de propriedade — Anexo V [D05]')[1].split('## 11.')[0]
prop=re.sub(r'### D05 — página (\d+) / página SEI \d+',lambda m:f'<!-- p. {m[1]} -->',prop)
put('fontes/md/comprovacao_de_propriedade_tabela.md','# Anexo V — tabela de recuperação\n\nFonte: comprovacao_de_propriedade.pdf; reconstrução herdada da seção 10 da memória antiga. '+D+'. Confiança baixa.\n600 posições físicas; posição não é número do lote. Campos agregados não foram desmembrados por adivinhação. ∅ substituído por [ilegível], sem afirmar ausência no PDF.\n'+prop.replace('∅','[ilegível]'))
put('AGENTS.md','''# Entrada única — Meu carro leilão

## Papel e comunicação
Atue como consultor sênior de leilões de veículos oficiais de SP (SGGD/DMI), em português claro, direto e sem promessas de condição mecânica ou regularização.
RF é o nome usado pelo usuário para veículos da frota estadual vendidos pela SGGD/DMI.
Separe fato documental, hipótese, decisão do usuário e análise histórica. Nunca invente: use “não verificado”; trecho ilegível: [ilegível].

## Leitura com contexto mínimo
1. Leia este AGENTS.md e memoria/00_indice.md no início de cada chat.
2. Abra somente a memória temática necessária; para um veículo, memoria/50_lotes.md e sua ficha em lotes/.
3. Busque o item ou marcador de página em fontes/md/. Não carregue fontes inteiras nem a memória antiga por padrão.
4. Confirme identificadores, valores e OCR duvidoso no PDF. Fotos não comprovam funcionamento.
5. Chat e Work precisam receber acesso a esta pasta e a instrução de ler AGENTS.md; não presumir leitura automática fora deste ambiente.

## Escrita e integridade
Trabalhe apenas nesta pasta. PDFs e arquivos preexistentes nesta reorganização são somente leitura: não apagar, mover ou sobrescrever.
Novos arquivos podem ser adicionados. Atualizações futuras da nova memória devem preservar histórico e seguir o protocolo abaixo.
Para alterar um fato já existente em memoria/, mostre o diff e peça aprovação antes da escrita. Adições sem alteração de fatos não exigem confirmação.
Registre toda informação com fonte, local (item/página ou seção/linha), data e confiança (alta/media/baixa).
Classifique como fato estável (norma), fato volátil (edital/taxa/prazo), decisão ou hipótese. Hipótese não vira fato sem fonte.
Não registrar CPF, RG, endereços pessoais, senhas, orçamento privado ou lance máximo. Não copiar dados pessoais de documentos ou páginas. Dados públicos dos veículos não identificam o usuário.
Não executar os scripts antigos sem revisar seus destinos: vários sobrescrevem os derivados existentes.

## Conflitos e validade
Hierarquia: lei > norma infralegal > edital > prática. Documento mais novo e específico prevalece dentro do mesmo nível e âmbito aplicável; não presumir que afaste norma superior.
Preserve o registro anterior com “substituído por”, sem apagar, após aprovação quando houver alteração factual.
Fatos voláteis: “revalidar em” a cada novo edital e antes de lance/pagamento; cotações em cada consulta.
Normas: revalidar em seis meses (base desta sessão: 2027-05-08), ou antes se a vigência ainda for incerta.
Fato vencido ou incerto exige reverificação antes de uso decisório. O título “edital vigente” indica o edital de referência local, não certificação de inexistência de erratas.
Leiloeiro e plataforma mudam por edital. Não importar regras de editais anteriores.

## Fechamento e compactação
Use templates/fechamento_sessao.md ao concluir sessão relevante; registre decisões, lotes e pendências, e mostre o diff da memória.
memoria/70_log_sessoes.md é append-only: acrescente de uma a três linhas por sessão.
Ao ultrapassar 200 linhas, copie o log integral para memoria/arquivo/ com data, confira integridade e proponha resumo de até 20 linhas; preserve o original e solicite aprovação se mudar fatos.
Índice até 60 linhas; cada arquivo ativo de memoria/ até 300 linhas. Divida por assunto antes de exceder.

## Mapa
- memoria/00_indice.md: roteador da memória.
- memoria/10_projeto.md: objetivo, escopo e definições.
- memoria/20_regras_edital_vigente.md: regras documentais do 003/2026.
- memoria/30_base_legal.md: normas, alcance e estado de verificação.
- memoria/40_decisoes.md: escolhas e histórico, sem presumir decisões de compra.
- memoria/50_lotes.md e lotes/: 14 fichas e referências.
- memoria/60_pendencias.md: OCR, documentos ausentes e dúvidas.
- memoria/70_log_sessoes.md e memoria/arquivo/: sessões e arquivo.
- fontes/md/: seis fontes paginadas e duas tabelas de recuperação.
- auditoria/inventario.md: utilidade de cada arquivo original.
- auditoria/conversao.md: contagens, amostras e limites.
- auditoria/reorganizacao.diff: adições desta sessão à memória.
- templates/: análise de lote e fechamento.
- PDFs, CSVs, Markdown antigos, evidencias/ e tmp/analise/: acervo preservado; localização original mantida.
''')
put('memoria/10_projeto.md','''# Projeto

Atualizado em: 2026-11-08. Origem das definições: conversa com o usuário / prompt anexado, OBJETIVO e PASSOS 3–4. Confiança alta sobre a instrução.

Objetivo: apoiar análise de leilões de veículos oficiais de SP e permitir retomada entre chats por arquivos locais, com leitura mínima e fontes rastreáveis.
Escopo atual: edital 003/2026, seis PDFs (48 páginas), 14 veículos já triados e evidências locais.
RF: denominação do usuário para veículos da frota estadual vendidos pela SGGD/DMI.
Comitente: SGGD/DMI (Estado de SP). Leiloeiro e plataforma variam por edital. Classificação: fato de contexto, origem conversa com o usuário; para este edital, conferir preâmbulo, p. 1.
Preferências: português claro, objetivo, sem invenções; fontes com página/item; incertezas explícitas; preservação dos originais e privacidade.
Fora do escopo desta organização: dar lances, realizar pagamentos, enviar mensagens, certificar funcionamento ou propriedade, emitir conclusão jurídica definitiva e armazenar lance máximo/dados pessoais.
A memória antiga contém informação útil, mas extensa e com OCR defeituoso. Foi preservada como acervo, não como entrada padrão.
Revalidar edital antes de qualquer decisão e a cada novo certame. A organização atual não equivale a atualização dos lances nem consulta de erratas.
''')
rules=[('Identidade','SGGD/DMI; leiloeiro José Eduardo de Abreu Sodré Santoro; plataforma www.sodresantoro.com.br.','preâmbulo','1'),('Sessão','12/11/2026, 10h–16h, horário de Brasília; possibilidade de continuidade em dias úteis.','preâmbulo','1–2'),('Categorias','543 conservados com documentação e 57 sucatas sem documentação; 600 lotes declarados.','1.1, alíneas c–d','2'),('Estado e exclusão','Venda no estado e sem garantia; DMI pode excluir lotes até abertura.','1.1.a, 1.3','2'),('Débitos','DMI responde por multas de infrações até a data do leilão; licenciamento atualizado conforme calendário.','1.4–1.5','2'),('Custos do comprador','Transferência, retirada, carregamento, transporte, tributos e demais encargos descritos; redação menciona DPVAT e IPVA proporcional. Aplicabilidade atual de tributos não revalidada.','1.6','2'),('Visita','10 e 11/11/2026, 9h–12h e 14h–17h; sem agendamento; vedado ligar motores, desmontar ou manusear.','1.8','2–3'),('Pagamento e comissão','À vista, 100% do lance mais 5%, em até 48 horas da convocação após fase recursal.','2.2.1–2.2.2; 5.7','3, 7'),('Taxa','R$ 22,89 para reconhecimento de firma de veículos com documentação; não inclui todos os custos.','2.2.3','3'),('Participação','Interessados que cumpram condições; cadastro prévio gratuito; impedimentos listados no item 3.4.','3.1–3.4','3–4'),('Sucatas','Exigem atividade de comércio de peças usadas, credenciamento DETRAN-SP e requisitos de regularidade descritos.','3.3','3–4'),('Proposta','Inicial até data/hora de abertura; lances no sistema.','4.1','4'),('CRV','DMI entrega ao leiloeiro em até 5 dias úteis do recolhimento e correta prestação de contas; leiloeiro devolve preenchido em até 15 dias úteis do recebimento.','6.3–6.4','7'),('Nota e assinatura','Nota de venda em até 5 dias após pagamentos; DMI providencia assinatura/firma; entrega ao arrematante compete ao leiloeiro. Prazo final global não definido nesses itens.','6.4–6.7','7–8'),('Titular','Documentos em nome do vencedor; vedada substituição.','6.8','8'),('Retirada','Condicionada à prestação de contas e nota; caminhões/vans: 23–24/11; carros/caminhonetes/motos: 25/11–18/12, dias úteis; agendamento pela plataforma.','7.1–7.2.4','8'),('Atraso','Retirada menciona 20 dias úteis; conciliar marco com janelas; armazenagem/remoção e possível novo leilão.','7.2–7.5','8–9'),('Sanções','20% do lance por não pagamento; 0,1% ao dia por atraso de retirada; demais sanções nos itens 8.1–8.6. Base/limite diário a esclarecer.','8.1–8.6','9'),('Esclarecimentos','Até 3 dias úteis antes da abertura; não suspendem automaticamente o certame. Não converter em data absoluta sem conferir calendário e erratas.','9.1–9.4','9–10'),('Anexos','Anexo IV cita expressamente CONTRAN 1.025/2026; isso não resolve por si só o alcance à frota oficial.','10.7.d','10')]
put('memoria/20_regras_edital_vigente.md','# Edital de referência — 003/2026\n\nAtualizado: '+D+'. Classificação: fatos voláteis documentais. Fonte de todas as linhas: [Edital convertido](../fontes/md/Edital.md), item/página abaixo. Confiança media (OCR); item 10.7.d conferido visualmente.\nRevalidar em: cada novo edital e antes de lance, pagamento ou retirada. Erratas posteriores: não verificado nesta sessão.\n\n| Tema | Regra documental | Item | Página física |\n|---|---|---|---|\n'+''.join('| '+' | '.join(r)+' |\n' for r in rules))
put('memoria/30_base_legal.md','''# Base legal documental

Atualizado: 2026-11-08. Classificação: fatos estáveis documentais; efeitos atuais dependem de verificação oficial. “Verificado em” abaixo é conferência do arquivo local, não pesquisa de consolidação normativa. Revalidar em: 2027-05-08, ou antes de uso se incerta.

| Norma | Dispositivo | Resumo | Vigência | Fonte | Verificado em | Confiança |
|---|---|---|---|---|---|---|
| SGGD 28/2024 | arts. 1–2 | Institui e organiza comissão executiva para alienação da frota oficial. | incerta (alterações posteriores não consultadas) | fontes/md/Resolucao_SGGD.md, p. 1 | 2026-11-08 | media, OCR |
| SGGD 28/2024 | art. 3 | Delega assinatura do CRV/ATPV à presidência da comissão. | incerta | mesma fonte, p. 2; imagem conferida | 2026-11-08 | alta documental |
| SGGD 28/2024 | art. 5 | Entrada em vigor na publicação; revoga SGP 09/2015. | incerta quanto a alterações posteriores | mesma fonte, p. 2 | 2026-11-08 | alta documental |
| CONTRAN 1.025/2026 | art. 1 | Trata de remoção e leilão de veículos recolhidos. | incerta quanto à situação atual e alcance neste certame | fontes/md/Resolucao_Contran.md, p. 1 | 2026-11-08 | alta documental |
| CONTRAN 1.025/2026 | arts. 45–46 | Revoga 623/2016 e prevê vigência na publicação. | incerta quanto a alterações posteriores | mesma fonte, p. 3; imagem conferida | 2026-11-08 | alta documental |
| CONTRAN 623/2016 | revogação pelo art. 45 da 1.025/2026 | Revogação expressa confirmada no PDF fornecido. | revogada conforme documento local; efeitos atuais não revalidados | mesma fonte, p. 3 | 2026-11-08 | alta documental |
| Lei 14.133/2021 | remissões do edital | Referência licitatória do certame. | incerta nesta revisão | fontes/md/Edital.md, p. 1 e itens 8–9; texto legal integral ausente | não verificado | baixa |
| Decreto SP 68.422/2024 | preâmbulo e item 5.7 | Referência estadual ao procedimento eletrônico. | incerta nesta revisão | fontes/md/Edital.md, pp. 1, 7; texto legal integral ausente | não verificado | baixa |

Origem inicial das duas questões CONTRAN: conversa com o usuário, PASSO 3. A citação como anexo e a revogação foram confirmadas localmente; a aplicação à alienação de veículos oficiais permanece não verificada. Não importar automaticamente prazos dessa resolução para substituir o edital.
''')
put('memoria/40_decisoes.md','''# Decisões

| Data | Decisão | Motivo / fonte e local | Status | Confiança |
|---|---|---|---|---|
| 2026-11-08 | Reorganizar por novas camadas, mantendo todos os originais nos mesmos locais. | Instrução do usuário, prompt anexado, REGRAS DE EXECUÇÃO. | Executada | alta |
| 2026-11-08 | AGENTS.md passa a ser a entrada; memória antiga continua acessível como acervo. | Objetivo de retomada com pouco contexto, PASSOS 3–4. | Executada | alta |
| 2026-11-08 | Manter ranking antigo como triagem histórica de baixa confiança. | comparacao_preliminar_carros.md, “Ranking para priorizar vistoria”. | Importado; não é decisão de compra | alta sobre origem, baixa sobre condição |
| 2026-11-08 | Preservar correção histórica do link do lote 522 sem alterar CSV. | comparacao_preliminar_carros.md, “Correção do lote 522”; evidencias/carros_interesse_original.csv. | Registro histórico, página oficial não revalidada | media |

Decisão de arrematar qualquer lote: não verificado. Não armazenar teto de lance.
''')
# Import sections verbatim, with historical qualification and repaired relative image paths.
comp=read('comparacao_preliminar_carros.md');matches=list(re.finditer(r'^### Lote (\d+) .+$',comp,re.M));csvrows={int(r['Lote']):r for r in csv.DictReader(Path('carros_conferencia.csv').open())}
lotindex=[]
for i,m in enumerate(matches):
 lot=int(m[1]);end=matches[i+1].start() if i+1<len(matches) else comp.find('\n## ',m.end());end=len(comp) if end<0 else end
 sec=comp[m.start():end].strip().replace('(evidencias/','(../evidencias/')
 group=re.search(r'\*\*Grupo ([ABC])',sec)[1];cr=csvrows[lot]
 body=f'''# Lote {lot:04d} — edital 003/2026

Atualizado em: {D}. Classificação: hipótese/análise histórica e fatos voláteis do catálogo.
Fonte: comparacao_preliminar_carros.md, seção “Lote {lot:04d}”, linha {comp[:m.start()].count(chr(10))+1}; carros_conferencia.csv, registro Lote {lot:04d}.
Confiança: baixa para priorização/estado mecânico; conferência documental anterior não refeita integralmente.
Revalidar em: próxima consulta ao catálogo, antes da visita e antes de qualquer lance.
Veredito: grupo {group} de prioridade de vistoria; nenhuma aprovação de compra.
Custo total: não verificado. Valores abaixo são registros históricos, não cotação atual nem teto de lance.
Evidências: [galeria](../evidencias/{lot}/galeria.png), [origens](../evidencias/{lot}/fontes.json), [descrição](../evidencias/{lot}/descricao.json).
Anexo I: [fonte](../fontes/md/Carros_lista.md), p. {cr['Página PDF Anexo I']}; conferir identidade no original.

## Análise anterior preservada

{sec}

## Próxima verificação
Confirmar identidade, documentação, condição observável e orçamento de reparos; atualizar apenas com fonte e data. Relatos do CSV não são diagnósticos. Não presumir testes de motor/manuseio permitidos.
'''
 put(f'lotes/003_2026_{lot:04d}.md',body);lotindex.append(f'| 003/2026 | [{lot:04d}](../lotes/003_2026_{lot:04d}.md) | Grupo {group}; triagem histórica | não verificado | {D} |')
put('memoria/50_lotes.md','# Lotes analisados\n\nFonte: comparacao_preliminar_carros.md, seções por lote; data '+D+'. Confiança baixa. Grupos A/B/C são prioridade de vistoria, não recomendação de compra. Revalidar na próxima consulta e antes de lance.\n\n| Edital | Lote | Veredito | Custo total | Data |\n|---|---|---|---|---|\n'+'\n'.join(lotindex))
put('memoria/60_pendencias.md','''# Pendências

Atualizado: 2026-11-08. Itens abaixo são pendências/hipóteses, não fatos confirmados; confiança baixa quando não indicado. Revalidar antes de uso decisório.

| ID | Estado | Questão / próxima ação | Fonte e local |
|---|---|---|---|
| P01 | aberta | Aplicabilidade da CONTRAN 1.025/2026 à alienação de frota oficial: obter esclarecimento formal e verificar fonte oficial vigente. | conversa com o usuário; CONTRAN art. 1, p. 1; edital 10.7.d, p. 10 |
| P02 | confirmada localmente | Edital cita CONTRAN 1.025/2026 como Anexo IV. Conferência visual desta sessão; confiança alta documental. | Edital.pdf, p. 10, 10.7.d |
| P03 | confirmada localmente | Art. 45 revoga CONTRAN 623/2016. Confiança alta documental; vigência atual não pesquisada. | Resolucao_Contran.pdf, p. 3 |
| P04 | aberta | Obter Anexo II: 57 sucatas declaradas, relação individual ausente. | Edital 1.1.d, p. 2; inventário |
| P05 | aberta | OCR integral não certificado: campos unidos, ausentes e rodapés corrompidos. Revisar tabelas antes de qualquer uso de identificação/valor. | auditoria/conversao.md; fontes/md/*_tabela.md |
| P06 | aberta | 543 linhas e 600 posições não comprovam números de lote únicos nem correspondência completa. Não inferir lote pela posição. | tmp/analise/lotes_rows.json; memória antiga, seções 9–10 |
| P07 | aberta | Conferência visual integral de artigos, subitens e 1.143 linhas tabulares ainda não realizada. Amostragem não certifica integralidade. | auditoria/conversao.md |
| P08 | aberta | Atualizar lances, exclusões, erratas e calendário antes de agir. Consulta oficial atual não realizada nesta organização. | edital preâmbulo e 1.3; carros_interesse.csv |
| P09 | aberta | Conciliar 20 dias úteis de retirada com janelas por categoria; confirmar base/limite da multa diária. | edital 7.2, p. 8 e 8.1.c, p. 9 |
| P10 | aberta | Confirmar prazo final de CRV/ATPV-e e custos/solução em impedimento de transferência. | edital 6.3–6.7, pp. 7–8 |
| P11 | aberta | Verificar identidade física, débitos, motor, restrições e reparos dos 14 veículos; obter fotografias melhores. | lotes/; comparacao_preliminar_carros.md |
| P12 | aberta | Relatos de piso furado nos lotes 123 e 463 não comprovados; podem alterar triagem. | seções correspondentes da comparação anterior |
| P13 | aberta | Comprovar publicação completa e prazos por fontes oficiais, sem importar como nova verificação a pesquisa citada na memória antiga. | memória antiga, seção 6 |
| P14 | aberta | Definir quais veículos seguem para vistoria, sem registrar orçamento privado ou teto de lance. | decisão do usuário ainda não verificada |

Privacidade: a nova transcrição omite o CPF parcialmente mascarado encontrado no preâmbulo; originais preservados. Menções genéricas a documentos exigidos não contêm dados do usuário.
''')
put('templates/analise_lote.md','''# Lote [número] — edital [número]

Data: [AAAA-MM-DD]; classificação: [fato volátil / hipótese]; confiança: [alta/media/baixa]; revalidar em: [marco].
Fonte e local: [arquivo/URL, página, item ou linha].
Identidade: [marca/modelo, ano, placa/chassi públicos; não verificado se ausente].
Categoria documental: [não verificado].
Evidências observadas: [fonte, foto/página e limite].
Relatos não comprovados: [separar de observações].
Documentação, débitos e motor: [não verificado].
Custos públicos e estimativas: [valor, fonte, data e premissa]; custo total: [não verificado].
Não gravar lance máximo, dados pessoais ou orçamento privado.
Veredito: [condicional, motivo e confiança]; não transformar hipótese em diagnóstico.
Pendências e próxima ação: [ação e fonte necessária].
Decisão do usuário: [não verificado].
''')
put('templates/fechamento_sessao.md','''# Fechamento — [data]

- Escopo e fontes/local consultados: [arquivos e itens/páginas].
- Fatos novos: [classe, fonte/local, data, confiança, revalidar em].
- Decisões: [decisão, motivo, status; sem dados privados].
- Lotes: [fichas atualizadas ou nenhum].
- Pendências: [abertas/resolvidas e evidência].
- Próxima ação: [uma ação concreta].
- Diff: [mostrar adições/alterações da memória; alteração de fato existente requer aprovação prévia].
- Log: [acrescentar 1–3 linhas em memoria/70_log_sessoes.md].
''')
put('memoria/70_log_sessoes.md','# Log de sessões — append-only\n\n2026-11-08 — Reorganização aditiva: 206 arquivos originais inventariados, seis PDFs (48 páginas), oito derivados em fontes/md/ e 14 fichas históricas; originais preservados.\n2026-11-08 — Conferidos localmente edital 10.7.d e CONTRAN art. 45; aplicação à frota, OCR integral e atualização oficial permanecem pendentes. Diff: auditoria/reorganizacao.diff.\n2026-11-08 — Próxima ação: resolver pendências documentais prioritárias e revisar o OCR dos lotes selecionados antes de decisão.\n')
# Human-readable file-by-file inventory.
inv=json.loads(read('auditoria/inventario_original.json'))
def purpose(x):
 p=Path(x['arquivo']);n=p.name
 if n=='.DS_Store':return 'Metadados do Finder; sem utilidade para a memória; preservados.'
 if p.suffix=='.pdf':return 'Fonte documental original, somente leitura; conversão paginada em fontes/md/.'
 if n=='contexto_memoria_leilao_003_2026.md':return 'Memória monolítica anterior; histórico e tabelas; não carregar por padrão.'
 if n=='comparacao_preliminar_carros.md':return 'Análise histórica dos 14 veículos; origem das fichas por lote.'
 if n=='Condições de venda.md':return 'Transcrição auxiliar do edital; não substitui PDF nem sua paginação.'
 if n=='carros_interesse.csv':return 'Seleção e comentários históricos do usuário; valores desatualizados.'
 if n=='carros_conferencia.csv':return 'Cruzamento anterior de identidade, valores e páginas dos 14 lotes.'
 if n=='carros_interesse_original.csv':return 'Cópia histórica anterior à correção do link do lote 522.'
 if p.parts[0]=='evidencias':
  lot=p.parts[1];roles={'pagina.html':'captura HTML do catálogo alternativo; conteúdo remoto não confiável','texto.txt':'texto extraído do catálogo','fontes.json':'URLs de origem e imagens','descricao.json':'metadados e descrição documental do catálogo','galeria.png':'montagem de seis fotos reduzidas; triagem histórica'}
  return f'Lote {lot}: '+roles.get(n,'fotografia reduzida de referência; não comprova funcionamento')+'.'
 if p.suffix in ['.swift','.py']:
  roles={'extrair.swift':'extração PDFKit','ocr.swift':'OCR português com Vision','rotacao.swift':'OCR de páginas giradas','tabelas.swift':'extração de observações OCR','colunas.swift':'OCR por coluna','faixas.swift':'OCR por faixas','linhas.swift':'detecção de linhas físicas das tabelas','montar_tabelas.py':'reconstrução de 543 linhas do Anexo I','gerar_memoria.py':'geração da memória antiga e tabela de propriedade'}
  return 'Ferramenta anterior: '+roles.get(n,'processamento auxiliar')+'; revisar antes de executar, pois pode sobrescrever derivados.'
 if p.suffix=='.json':return 'Intermediário de OCR/geometria ou linhas reconstruídas; suporte à auditoria, não fonte primária.'
 if p.suffix=='.png':return 'Renderização da primeira página para OCR/conferência; original PDF prevalece.'
 if x['bytes']==0:return 'Saída textual vazia de rotina OCR; informação correspondente pode estar no JSON; não usar como fonte.'
 return 'Texto OCR/extrator anterior com páginas; base de conversão, requer confronto com PDF.'
t='# Inventário arquivo por arquivo\n\nData: '+D+'. 206 arquivos originais lidos; tipo, tamanho, estrutura/decodificação e hash inspecionados. Imagens verificadas como arquivos, sem nova avaliação mecânica de todas as fotos; PDFs inspecionados quanto a páginas/texto e amostrados visualmente.\nHashes e dimensões: inventario_original.json. Nenhum original foi removido ou alterado.\n\n| Arquivo | Tipo | Páginas | Texto extraível | Utilidade / destino lógico |\n|---|---|---|---|---|\n'
for x in inv:t+='| '+x['arquivo']+' | '+(x['tipo'] or 'metadado')+' | '+str(x['paginas'] or '—')+' | '+x['texto_extraivel']+' | '+purpose(x)+' |\n'
put('auditoria/inventario.md',t)
# Conversion audit counts.
audit='# Auditoria da conversão\n\nData: '+D+'. Escopo local; nenhuma certificação jurídica ou atualização de catálogo.\n\n| Fonte | Páginas PDF | Marcadores | Método |\n|---|---|---|---|\n'
for stem in meta:audit+=f'| {stem}.pdf | {len(PdfReader(stem+".pdf").pages)} | {len(pages(source_text[stem]))} | '+('texto' if stem=='Resolucao_Contran' else 'OCR português preexistente reutilizado')+' |\n'
arts=re.findall(r'^Art\.\s*(\d+)',source_text['Resolucao_Contran'],re.M);sggd=re.findall(r'^Artigo\s*(\d+)',source_text['Resolucao_SGGD'],re.M);items=re.findall(r'^(\d+\.\d+(?:\.\d+)*)(?:\.|\s)',source_text['Edital'],re.M)
audit+=f'''\n## Contagens e alcance
- 48 páginas físicas e 48 marcadores nas seis transcrições; PDFs sem camada textual: 45 páginas. CONTRAN: 3 páginas com texto extraível.
- CONTRAN: {len(arts)} inícios de artigo; números únicos {len(set(arts))}, sequência 1–46: {set(map(int,arts))==set(range(1,47))}.
- SGGD: {len(sggd)} artigos, sequência 1–5: {set(map(int,sggd))==set(range(1,6))}.
- Edital: {len(items)} inícios numéricos de itens/subitens detectados no OCR; não equivale à certificação de alíneas ou completude visual. Comparação integral com PDF: não verificado.
- Anexo I: {len(rows)} linhas reconstruídas; total coincide com 543 declarado no edital 1.1.d e cabeçalho do Anexo I. Não comprova unicidade dos lotes.
- Anexo V: {len(re.findall(r'^\| V-\d+',prop,re.M))} posições tabulares herdadas; não são 600 identificadores validados. Páginas 6 e 9 tiveram correção de rotação na análise anterior.

## Conferências visuais desta sessão
| Amostra | Fonte/local | Resultado |
|---|---|---|
| 1 | Carros_lista.pdf, p. 1, lote 2 | Placa EEF1718, chassi 93W245G3392030029, FIAT/DUCATO MAXICARGO e R$ 6.500,00 conferidos na imagem. OCR antigo omitia lote e unia modelo/chassi/preço/observação. Nova tabela corrigida apenas nessa linha. |
| 2 | Carros_lista.pdf, p. 1, lote 4 | Placa DJP2753, chassi 9BG138GJ09C404587, GM/S10 COLINA D, motor M1A324012 e R$ 13.800,00 conferidos; motor aparecia junto à cor no OCR. Nova tabela corrigida. |
| 3 | Edital.pdf, p. 10, 10.7.d | Anexo IV é a CONTRAN 1.025/2026 de 26/06/2026, confirmado. |
| 4 | Resolucao_Contran.pdf, p. 3, arts. 45–46 | Revogação da 623/2016 e vigência na publicação confirmadas. |
| 5 | Resolucao_SGGD.pdf, p. 2, arts. 3 e 5 | Delegação para assinatura e revogação da SGP 09/2015 confirmadas. |
| 6 | comprovacao_de_propriedade.pdf, p. 1, lote 2 | Placa EEF1718 e chassi 93W245G3392030029 coincidem visualmente com Anexo I. |

Imagens da conferência: arquivos amostra_*.png e *.pdf.png nesta pasta.

## Divergências e limitações preservadas
- Os cinco OCRs já existiam e foram reutilizados, não refeitos nesta sessão. Ferramenta original: Vision pt-BR, identificada em tmp/analise/ocr.swift; textos/tabulações não são transcrições certificadas.
- Campos unidos ou mal reconhecidos não foram adivinhados. A tabela do Anexo I conserva todas as células originais em coluna própria, além dos campos separáveis. [ilegível] significa falha de recuperação, não ausência no original.
- A transcrição textual mantém erros do OCR herdado para rastreabilidade; ainda não há revisão humana de todos os rodapés e caracteres. No Anexo V, os campos agregados foram mantidos, sem inventar separação.
- Duas correções visuais são registradas acima somente no novo derivado estruturado; os dados originais continuam intactos.
- Um CPF parcialmente mascarado do preâmbulo foi omitido na nova transcrição. Essa omissão explícita atende à privacidade e é exceção à reprodução literal.
- Hierarquia de capítulos/seções e numeração preservadas quando reconhecíveis; a integralidade visual de listas, artigos e itens não foi certificada.
- Anexo II ausente; somente 543 dos 600 lotes declarados têm lista detalhada neste acervo.
- Não revalidamos nesta organização vigência normativa, erratas, lances, restrições ou estado físico. As fichas mantêm limites da análise histórica.
'''
put('auditoria/conversao.md',audit)
index=[('10_projeto.md','Objetivo, RF, escopo e preferências; ler ao retomar o projeto'),('20_regras_edital_vigente.md','Regras do 003/2026 com página/item; ler para prazos e custos'),('30_base_legal.md','Normas e vigência incerta; ler para questões normativas'),('40_decisoes.md','Decisões e histórico; ler antes de mudar rumo'),('50_lotes.md','Índice das 14 fichas; ler para escolher veículo'),('60_pendencias.md','Incertezas e verificações pendentes; ler antes de decidir'),('70_log_sessoes.md','Últimas sessões; ler para retomada')]
it='# Índice de memória\n\nEntrada única: ../AGENTS.md. Atualização: '+D+'. Não carregar todo o acervo.\n\n'
for f,s in index:it+=f'- [{f}]({f}): {s}; atualizado {D}.\n'
for f in sorted(Path('lotes').glob('*.md')):it+=f'- [{f.name}](../{f}): análise histórica individual; ler somente para este lote; atualizado {D}.\n'
for f in sorted(Path('fontes/md').glob('*.md')):it+=f'- [{f.name}](../{f}): fonte/derivado paginado; buscar trecho para evidência, não carregar integralmente; atualizado {D}.\n'
for f,s in [('auditoria/inventario.md','utilidade de cada original'),('auditoria/conversao.md','contagens, amostras e falhas'),('auditoria/inventario_original.json','hashes e metadados dos originais'),('auditoria/reorganizacao.diff','adições à memória nesta sessão'),('templates/analise_lote.md','modelo de ficha'),('templates/fechamento_sessao.md','modelo de encerramento')]:it+=f'- [{f}](../{f}): {s}; ler quando necessário; atualizado {D}.\n'
it+='- memoria/arquivo/: destino reservado para logs compactados; ainda sem arquivos.\n- Acervo anterior: PDFs e Markdown/CSV na raiz, evidencias/ e tmp/analise/; preservados e detalhados no inventário.\n'
put('memoria/00_indice.md',it)
diff=''
for f in created:
 if f=='AGENTS.md' or f.startswith(('memoria/','lotes/','templates/')):diff+=''.join(difflib.unified_diff([],read(f).splitlines(True),fromfile='/dev/null',tofile=f))
put('auditoria/reorganizacao.diff',diff)
put('auditoria/arquivos_criados.json',json.dumps(created,ensure_ascii=False,indent=2))
print('Criados:',len(created));print('Artigos CONTRAN',len(arts),'SGGD',len(sggd),'Itens edital',len(items));print('Índice',len(it.splitlines()),'linhas')
