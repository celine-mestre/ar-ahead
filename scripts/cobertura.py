"""Cobertura mediática de TODAS as matérias, sem IA: procura no arquivo do Radar de Notícias (OCS nacionais acompanhados
pelo Radar, últimos 60 dias, incluindo notícias não marcadas) as notícias sobre o assunto de cada matéria e grava em cada uma
x['cobertura'] = {n7, n7ant, n, dias, ref, metodo, ultimas:[{data, fonte, titulo, url}]}:
  n7 = notícias nos últimos 7 dias; n7ant = nos 7 dias anteriores (tendência); n = total em 60 dias.
É também o «cesto» de notícias que o Amália usa nas fichas.
Uso: python scripts/cobertura.py [--local pasta_com_ficheiros_do_radar]"""
import json, gzip, re, sys, io, pathlib, datetime, unicodedata, urllib.request

RADAR = 'https://raw.githubusercontent.com/upe-sggov/radar-noticias/main/'
ESTRANGEIROS = ('.br', '.cv', '.ao', '.mz', '.gw', '.st', '.tl', '.mo', '.es', '.fr', '.it', '.de', '.uk', '.com.br')
DIAS = 60
VAZIAS = set('''comissao comissoes parlamentar parlamentares audicao audicoes reuniao apreciacao votacao votacoes requerimento
requerimentos projeto projetos proposta propostas resolucao discussao relatorio relatorios parecer pareceres plenario
grupo trabalho trabalhos governo ministro ministra secretario secretaria estado assuntos sobre outros informacoes deputado
deputada relator relatora prazo prazos envio sessao legislativa iniciativa iniciativas apresentacao nomeacao distribuicao
direitos liberdades garantias atividades plano orcamento ordem sinalizada sinalizado
para pela pelo pelas pelos como mais entre desde este esta estes estas esse essa isso isto seus suas nossa nosso
quando onde qual quais cada todo toda todos todas outra outro outras tambem ainda apos ante contra durante segundo
janeiro fevereiro marco abril maio junho julho agosto setembro outubro novembro dezembro
segunda terca quarta quinta sexta sabado domingo hoje ontem amanha semana data datas numero alteracao alteracoes
continuacao debate generalidade especialidade encerramento'''.split())

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
    """Termos de pesquisa a partir do ASSUNTO (tema e assunto do Amália; o resumo fica de fora):
    palavras significativas e expressões de 2 palavras seguidas."""
    base = ' '.join(filter(None, [(x.get('amalia') or {}).get('assunto'), x.get('tema')]))
    ws = [w for w in re.findall(r'[a-z0-9]+', norm(base)) if len(w) >= 4 and w not in VAZIAS and not w.isdigit()]
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
    if len(sig) < 2 or not pares: return []
    res, sigs = [], set(sig)
    for a in arts:
        s = len(sigs & a['_w'])
        if s < 2: continue
        p = sum(1 for e in pares if e in a['_t'])
        if p >= 1 and s >= min(3, len(sigs)):   # exige uma expressão do assunto e quase todas as palavras
            res.append((p * 3 + s, a))
    res.sort(key=lambda r: (r[0], r[1].get('data', '')), reverse=True)
    return [a for _, a in res]

if __name__ == '__main__':
    local = sys.argv[sys.argv.index('--local') + 1] if '--local' in sys.argv else None
    p = pathlib.Path('dados/agenda.json'); d = json.loads(p.read_text(encoding='utf-8'))
    arts = corpus(local)
    print(len(arts), 'notícias no cesto (últimos', DIAS, 'dias)')
    hoje = datetime.date.today()
    c7, c14 = (hoje - datetime.timedelta(days=7)).isoformat(), (hoje - datetime.timedelta(days=14)).isoformat()
    for x in d['destaques'] + d['agenda']:
        if x.get('retirado'): continue
        r = procurar(x, arts)
        n7 = sum(1 for a in r if (a.get('data') or '')[:10] > c7)
        n7ant = sum(1 for a in r if c14 < (a.get('data') or '')[:10] <= c7)
        x['cobertura'] = {'n': len(r), 'n7': n7, 'n7ant': n7ant, 'dias': DIAS, 'ref': hoje.isoformat(), 'metodo': 'expressoes' if x.get('expressoes') else 'palavras', 'ultimas': [{'data': a.get('data', '')[:10], 'fonte': a.get('fonte'), 'titulo': a.get('titulo'), 'url': a.get('ligacao')} for a in sorted(r[:12], key=lambda a: a.get('data', ''), reverse=True)[:3]],
                          '_ligacoes': [a.get('ligacao') for a in r[:12]]}
    # nota de metodologia (substitui a versão anterior, se existir)
    NOTA = ('Cobertura mediática: contagem das notícias dos órgãos de comunicação social nacionais acompanhados pelo Radar de Notícias '
            'da UPE cujo título ou resumo refere o assunto (pelas expressões de pesquisa da matéria ou, na sua falta, pelas palavras do assunto, '
            'contagem indicativa). Mostra-se o número dos últimos 7 dias, a comparação com os 7 dias anteriores e o total em 60 dias. '
            'As notícias listadas são as mais recentes, não necessariamente as mais relevantes; a análise está nas fichas de varrimento.')
    d['metodologia'] = [m for m in d.get('metodologia', []) if not m.startswith('Cobertura mediática:')] + [NOTA]
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in d['destaques'] + d['agenda']:
        if 'cobertura' in x: print(f"{x['cobertura'].get('n7', 0):>4} /{x['cobertura']['n']:>5}  {x['pertinencia'][:3]}  {x['tema'][:70]}")
