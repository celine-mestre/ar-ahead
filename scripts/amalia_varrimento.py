"""Passo 3 — varrimento mediático com o Amália, a partir do corpus do Radar de Notícias (nunca da memória do modelo).
Para cada matéria "Imediato" validada:
  1. procura no arquivo do Radar (arquivo.json, 7 dias; meses/AAAA-MM.jsonl.gz para trás) as notícias que casam com o assunto;
  2. pede ao Amália, por notícia REAL, a síntese, o impacto para a sessão e a natureza;
  3. pede um enquadramento de um parágrafo, só com base nessas notícias;
  4. escreve a ficha no formato de agenda.json['fichas'] — cada entrada com data, fonte e ligação verdadeiras.
Os «Pontos de atenção» (verificação de números) NÃO são gerados: ficam para a Ana Luísa, que confronta as fontes primárias."""
import json, pathlib, re, sys, gzip, datetime, urllib.request
from amalia import perguntar, json_da_resposta

RADAR = 'https://raw.githubusercontent.com/upe-sggov/radar-noticias/main/'   # repositório público do Radar
dados = json.loads(pathlib.Path('dados/agenda.json').read_text(encoding='utf-8'))

def corpus(dias=60):
    arts = json.loads(urllib.request.urlopen(RADAR + 'arquivo.json', timeout=60).read())
    hoje = datetime.date.today()
    for m in {(hoje - datetime.timedelta(days=i)).strftime('%Y-%m') for i in range(0, dias, 28)}:
        try:
            with gzip.open(urllib.request.urlopen(RADAR + f'meses/{m}.jsonl.gz', timeout=60)) as f:
                arts += [json.loads(l) for l in f]
        except Exception: pass
    vistos, out = set(), []
    for a in arts:                                   # campos do Radar: titulo, fonte, ligacao, data, texto/resumo
        if a.get('ligacao') in vistos: continue
        vistos.add(a.get('ligacao')); out.append(a)
    return out

def casa(art, termos):
    t = (art.get('titulo', '') + ' ' + art.get('resumo', '')).lower()
    return sum(1 for k in termos if k in t)

def ficha(item, arts):
    termos = [t for t in re.split(r'[\s,;:()«»"]+', item['tema'].lower()) if len(t) > 4][:8]
    cand = sorted((a for a in arts if casa(a, termos) >= 2), key=lambda a: a.get('data', ''))[-15:]
    if not cand: return None
    fundo = []
    for a in cand:
        r = json_da_resposta(perguntar(
            "Analista da DSSD. Responde só com JSON em português europeu. Não acrescentes factos que não estejam no texto.",
            f"""Matéria na agenda da AR: {item['tema']} ({item['data']}). Resumo: {item['resumo']}
Notícia ({a.get('fonte')}, {a.get('data')}): {a.get('titulo')}
{(a.get('resumo') or '')[:1500]}
Devolve {{"sintese": "2 a 3 frases factuais", "impacto": "1 a 2 frases: como pode ser usada na sessão e por quem", "natureza": "critica"|"relevante"|"positivo"|"contexto"}}""", 350))
        if not r: continue
        fundo.append({'data': a.get('data'), 'fonte': a.get('fonte'), 'url': a.get('ligacao'), 'sintese': r.get('sintese', ''), 'impacto': r.get('impacto', ''), 'natureza': r.get('natureza', 'contexto'),
                      'naturezaLabel': {'critica': 'Crítica / muito relevante', 'relevante': 'Muito relevante', 'positivo': 'Contextual / positivo', 'contexto': 'Contextual'}.get(r.get('natureza'), 'Contextual')})
    enq = perguntar("Analista da DSSD. Português europeu, um parágrafo, sem listas, só com base nas notícias dadas.",
                    "Escreve o enquadramento para a sessão parlamentar «" + item['tema'] + "» a partir destas sínteses:\n" + '\n'.join(f"- {f['data']} {f['fonte']}: {f['sintese']}" for f in fundo), 300)
    return {'titulo': item['tema'], 'meta': f"{item.get('tipoLabel','')} · {item['dataLabel']}, {item.get('hora','')} · UO de referência: {' · '.join(item['uo'])}",
            'enquadramento': enq.strip(), 'atencaoTitulo': 'Pontos de atenção (verificação de números)', 'atencao': [], 'blocos': [], 'tabelas': [], 'fundo': fundo, 'gerado_por': 'Amália — a rever'}

arts = corpus()
novas = 0
for it in dados['destaques'] + dados['agenda']:
    if it['pertinencia'] != 'Imediato' or it.get('varrimento'): continue
    chave = re.sub(r'[^a-z0-9]+', '-', it['tema'].lower())[:40]
    f = ficha(it, arts)
    if f: dados['fichas'][chave] = f; it['varrimento'] = chave; novas += 1
pathlib.Path('dados/agenda.json').write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding='utf-8')
print(novas, 'fichas geradas pelo Amália, marcadas «a rever»')
