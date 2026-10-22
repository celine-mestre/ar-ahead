"""Cobertura mediática de TODAS as matérias, sem IA: procura no arquivo do Radar de Notícias (OCS acompanhados,
últimos 60 dias, incluindo notícias não marcadas) as notícias sobre o assunto de cada matéria e grava em cada uma
x['cobertura'] = {n, dias, ultimas:[{data, fonte, titulo, url}]}. É também o «cesto» de notícias que o Amália usa nas fichas.
Uso: python scripts/cobertura.py [--local pasta_com_ficheiros_do_radar]"""
import json, gzip, re, sys, io, pathlib, datetime, unicodedata, urllib.request

RADAR = 'https://raw.githubusercontent.com/upe-sggov/radar-noticias/main/'
ESTRANGEIROS = ('.br', '.cv', '.ao', '.mz', '.gw', '.st', '.tl', '.mo', '.es', '.fr', '.it', '.de', '.uk', '.com.br')
DIAS = 60
VAZIAS = set('''comissao comissoes parlamentar parlamentares audicao audicoes reuniao apreciacao votacao votacoes requerimento
requerimentos projeto projetos proposta propostas resolucao discussao relatorio relatorios parecer pareceres plenario
grupo trabalho governo ministro ministra secretario secretaria estado assuntos sobre outros informacoes deputado deputada
relator relatora prazo envio sessao legislativa iniciativa iniciativas apresentacao nomeacao distribuicao direitos
liberdades garantias atividades plano orcamento comissao'''.split())

def norm(s): return ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower()) if unicodedata.category(c) != 'Mn')

def ler(nome, local):
    if local: return (pathlib.Path(local) / nome).read_bytes()
    return urllib.request.urlopen(RADAR + nome, timeout=120).read()

def corpus(local=None):
    arts = []
    for nome in ('corpus.json', 'arquivo.json'):
        try: arts += json.loads(ler(nome, local))['noticias']
        except Exception as e: print('aviso:', nome, e)
    hoje = datetime.date.today()
    meses = sorted({(hoje - datetime.timedelta(days=i)).strftime('%Y-%m') for i in range(0, DIAS + 1, 10)})
    for m in meses:
        try:
            with gzip.open(io.BytesIO(ler(f'meses/{m}.jsonl.gz', local)), 'rt', encoding='utf-8') as f:
                arts += [json.loads(l) for l in f if l.strip()]
        except Exception as e: print('aviso:', m, e)
    limite = (hoje - datetime.timedelta(days=DIAS)).isoformat()
    vistos, out = set(), []
    for a in arts:
        k = (a.get('ligacao') or '', norm(a.get('titulo'))[:90] + '|' + (a.get('fonte') or ''))
        if (a.get('data') or '')[:10] < limite or k[0] in vistos or k[1] in vistos: continue
        dom, fonte = (a.get('dominio') or ''), (a.get('fonte') or '')
        if '(' in fonte or dom.endswith(ESTRANGEIROS) or 'brasil' in dom: continue   # só OCS nacionais
        vistos.update(k); t = norm((a.get('titulo') or '') + ' ' + (a.get('resumo') or ''))
        a['_t'] = t; a['_w'] = set(re.findall(r'[a-z0-9]+', t)); out.append(a)
    return out

def termos(x):
    """Termos de pesquisa a partir do ASSUNTO (tema, assunto do Amália e início do resumo):
    palavras significativas e expressões de 2 palavras seguidas."""
    base = ' '.join(filter(None, [(x.get('amalia') or {}).get('assunto'), x.get('tema'), (x.get('resumo') or '')[:160]]))
    ws = [w for w in re.findall(r'[a-z0-9]+', norm(base)) if len(w) >= 4 and w not in VAZIAS]
    sig = list(dict.fromkeys(ws))[:12]
    pares = list(dict.fromkeys(f'{a} {b}' for a, b in zip(ws, ws[1:])))[:10]
    return sig, pares

def procurar(x, arts):
    exps = [norm(e).strip() for e in (x.get('expressoes') or []) if e and e.strip()]
    if exps:   # expressões de pesquisa definidas (pelo Amália ou pela Ana Luísa): muito mais precisas
        rx = re.compile(r'\b(' + '|'.join(re.escape(e) for e in exps) + r')\b')
        res = [a for a in arts if rx.search(a['_t'])]
        res.sort(key=lambda a: a.get('data', ''), reverse=True)
        return res
    sig, pares = termos(x)
    if len(sig) < 2: return []
    res, sigs = [], set(sig)
    for a in arts:
        s = len(sigs & a['_w'])
        if s < 2: continue
        p = sum(1 for e in pares if e in a['_t'])
        if p >= 1:                       # exige uma expressão do assunto, não só palavras soltas
            res.append((p * 3 + s, a))
    res.sort(key=lambda r: (r[0], r[1].get('data', '')), reverse=True)
    return [a for _, a in res]

if __name__ == '__main__':
    local = sys.argv[sys.argv.index('--local') + 1] if '--local' in sys.argv else None
    p = pathlib.Path('dados/agenda.json'); d = json.loads(p.read_text(encoding='utf-8'))
    arts = corpus(local)
    print(len(arts), 'notícias no cesto (últimos', DIAS, 'dias)')
    for x in d['destaques'] + d['agenda']:
        if x.get('retirado'): continue
        r = procurar(x, arts)
        x['cobertura'] = {'n': len(r), 'dias': DIAS, 'metodo': 'expressoes' if x.get('expressoes') else 'palavras', 'ultimas': [{'data': a.get('data', '')[:10], 'fonte': a.get('fonte'), 'titulo': a.get('titulo'), 'url': a.get('ligacao')} for a in sorted(r[:12], key=lambda a: a.get('data', ''), reverse=True)[:3]],
                          '_ligacoes': [a.get('ligacao') for a in r[:12]]}
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in d['destaques'] + d['agenda']:
        if 'cobertura' in x: print(f"{x['cobertura']['n']:>4}  {x['pertinencia'][:3]}  {x['tema'][:70]}")
