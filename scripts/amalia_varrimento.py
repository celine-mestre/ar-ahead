"""Fichas de varrimento geradas pelo Amália, por níveis, SEMPRE a partir de notícias reais do Radar de Notícias
(nunca da memória do modelo):
  Imediato   → ficha completa: até 10 notícias com síntese, impacto e natureza + enquadramento de um parágrafo;
  Vigilância → ficha curta: até 5 notícias com síntese e natureza + enquadramento de duas frases;
  Registo    → sem ficha (fica a contagem de cobertura, calculada por cobertura.py).
Uma chamada ao modelo por ficha (lote), para caber no tempo do GitHub Actions. Sem notícias → ficha que o diz, sem IA.
Os «Pontos de atenção» (verificação de números na fonte primária) NÃO são gerados: são trabalho humano."""
import json, pathlib, re, sys
from amalia import perguntar, json_da_resposta
from cobertura import corpus, procurar

NIVEL = {'Imediato': ('completa', 10), 'Vigilância': ('curta', 5)}
ROT = {'critica': 'Crítica / muito relevante', 'relevante': 'Muito relevante', 'positivo': 'Contextual / positivo', 'contexto': 'Contextual'}
SIS = "Analista da DSSD (Secretaria-Geral do Governo). Português europeu. Responde só com JSON. Não acrescentes factos que não estejam nas notícias dadas."

def ficha(x, arts):
    nivel, maxn = NIVEL[x['pertinencia']]
    nots = sorted(procurar(x, arts)[:maxn * 2], key=lambda a: a.get('data', ''), reverse=True)[:maxn]
    nots.sort(key=lambda a: a.get('data', ''))
    meta = f"{x.get('tipoLabel','')} · {x['dataLabel']}{', ' + x['hora'] if x.get('hora') else ''} · UO de referência: {' · '.join(x['uo']) or '—'}"
    f = {'titulo': x['tema'], 'meta': meta, 'nivel': nivel, 'gerado_por': 'Amália — a rever', 'atencao': [], 'blocos': [], 'tabelas': [], 'fundo': []}
    if not nots:
        f['enquadramento'] = f"Sem notícias sobre esta matéria nos órgãos de comunicação social nacionais acompanhados pelo Radar de Notícias nos últimos 60 dias (expressões usadas: {', '.join(x.get('expressoes') or ['palavras do assunto'])})."
        return f
    lista = '\n'.join(f"{i+1}. [{a.get('data','')[:10]} · {a.get('fonte')}] {a.get('titulo')} — {(a.get('resumo') or '')[:350]}" for i, a in enumerate(nots))
    pedido_imp = ', "impacto": "1 frase: como pode ser usada na sessão e por quem"' if nivel == 'completa' else ''
    enq = 'um parágrafo (4 a 6 frases)' if nivel == 'completa' else 'duas frases'
    r = json_da_resposta(perguntar(SIS, f"""Matéria na agenda da Assembleia da República: {x['tema']} ({x['dataLabel']} {x.get('hora','')}).
Resumo: {x.get('resumo','')[:400]}
Notícias numeradas:
{lista}

Devolve {{"enquadramento": "{enq}, só com base nestas notícias", "noticias": [{{"n": 1, "sintese": "1 a 2 frases factuais"{pedido_imp}, "natureza": "critica"|"relevante"|"positivo"|"contexto"}}, ...]}}
Inclui todas as notícias, pela mesma numeração. Se uma notícia não for sobre esta matéria, devolve para ela "natureza": "fora".""", 1600 if nivel == 'completa' else 700)) or {}
    por_n = {int(n.get('n', 0)): n for n in (r.get('noticias') or []) if isinstance(n, dict) and str(n.get('n', '')).isdigit()}
    for i, a in enumerate(nots, 1):
        n = por_n.get(i, {})
        if n.get('natureza') == 'fora': continue
        nat = n.get('natureza') if n.get('natureza') in ROT else 'contexto'
        f['fundo'].append({'data': a.get('data', '')[:10], 'fonte': a.get('fonte'), 'url': a.get('ligacao'), 'sintese': n.get('sintese') or a.get('titulo'),
                           'impacto': n.get('impacto', '') if nivel == 'completa' else '', 'natureza': nat, 'naturezaLabel': ROT[nat]})
    f['enquadramento'] = (r.get('enquadramento') or '').strip() or f"{len(f['fundo'])} notícias encontradas no Radar de Notícias; enquadramento por gerar."
    return f

if __name__ == '__main__':
    p = pathlib.Path('dados/agenda.json'); d = json.loads(p.read_text(encoding='utf-8'))
    local = sys.argv[sys.argv.index('--local') + 1] if '--local' in sys.argv else None
    alvo = [x for x in d['destaques'] + d['agenda'] if x['pertinencia'] in NIVEL and not x.get('varrimento') and not x.get('retirado')]
    if not alvo: print('Nada a fazer.'); sys.exit(0)
    arts = corpus(local)
    for x in alvo:
        chave = re.sub(r'[^a-z0-9]+', '-', (x['data'] + '-' + x['tema']).lower())[:50].strip('-')
        d['fichas'][chave] = ficha(x, arts); x['varrimento'] = chave
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')   # grava a cada ficha: se o tempo acabar, nada se perde
        print('ficha', d['fichas'][chave]['nivel'], len(d['fichas'][chave]['fundo']), 'notícias ·', x['tema'][:60])
