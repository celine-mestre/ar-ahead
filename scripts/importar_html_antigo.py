import sys, json, re, pathlib
from bs4 import BeautifulSoup
html = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'lxml')

def txt(el):
    if el is None: return ''
    return re.sub(r'\s+', ' ', el.get_text(' ', strip=True)).strip()

def links(td):
    out = []
    for a in td.select('a[href^="http"]'):
        out.append({'titulo': txt(a), 'url': a['href']})
    return out

def row(tr, com_varr):
    tds = tr.find_all('td', recursive=False)
    d = tr.attrs
    hora = tr.select_one('.hora')
    resumo_td = tds[6]
    # resumo curto + texto completo (ordem de trabalhos)
    mais = resumo_td.select_one('.mais')
    completo = txt(resumo_td)
    completo = re.sub(r'\s*Ver mais\s*$', '', completo)
    if mais:
        curto = completo.replace(txt(mais), '').strip(' ·')
    else:
        curto = completo
    item = {
        'tema': d.get('data-f-tema', ''),
        'data': d.get('data-f-data', ''),
        'dataLabel': d.get('data-f-datal', ''),
        'hora': txt(hora),
        'periodo': d.get('data-f-periodo', ''),
        'interveniente': d.get('data-f-interv', '') or txt(tds[2]),
        'tipo': [t for t in d.get('data-f-tipo', '').split('|') if t],
        'tipoLabel': txt(tds[3]),
        'uo': [u for u in d.get('data-f-uo', '').split('|') if u and u != 'Sem UO atribuída'],
        'pertinencia': d.get('data-f-pert', ''),
        'resumo': curto,
        'ordemTrabalhos': completo if mais else '',
    }
    if com_varr:
        ir = tr.select_one('a[data-ir]')
        item['varrimento'] = ir['data-ir'] if ir else None
        item['ligacoes'] = links(tds[8])
    return item

destaques = [row(tr, True) for tr in soup.select('#t-semana tbody tr') if tr.get('data-f-tema')]
agenda = [row(tr, False) for tr in soup.select('#agenda tbody tr') if tr.get('data-f-tema')]

fichas = {}
for sec in soup.select('section.painel'):
    sid = sec['id']
    if sid == 's-semana': continue
    key = sid[2:]
    f = {'titulo': txt(sec.find('h2')), 'meta': txt(sec.select_one('p.meta')), 'enquadramento': txt(sec.select_one('p.enq')), 'atencao': [], 'blocos': [], 'fundo': [], 'tabelas': []}
    at = sec.select_one('.atencao')
    if at:
        f['atencaoTitulo'] = txt(at.find('h3'))
        for li in at.select('li'):
            s = li.find('strong')
            f['atencao'].append({'titulo': txt(s).rstrip(': ') if s else '', 'texto': txt(li).replace(txt(s), '', 1).strip() if s else txt(li)})
    # blocos h3 + p / tabelas simples (fora de .atencao e do fundo)
    for h3 in sec.find_all('h3'):
        if h3.find_parent(class_='atencao'): continue
        t = txt(h3)
        if t.startswith('Fundo mediático'): continue
        paras = []
        for sib in h3.find_next_siblings():
            if sib.name == 'h3': break
            if sib.name == 'p': paras.append(txt(sib))
            if sib.name == 'ul': paras.extend('• ' + txt(li) for li in sib.find_all('li'))
            if sib.name == 'table' or (sib.name == 'div' and sib.find('table')):
                tb = sib if sib.name == 'table' else sib.find('table')
                if 'fundo' in tb.get('class', []): break
                f['tabelas'].append({'titulo': t, 'cabecalho': [txt(th) for th in tb.select('thead th')], 'linhas': [[txt(td) for td in tr.find_all('td')] for tr in tb.select('tbody tr')]})
        if paras: f['blocos'].append({'titulo': t, 'paragrafos': paras})
    for tr in sec.select('table.fundo tbody tr'):
        tds = tr.find_all('td')
        a = tds[1].find('a')
        f['fundo'].append({'data': txt(tds[0]), 'fonte': txt(tds[1]), 'url': a['href'] if a else None, 'sintese': txt(tds[2]), 'impacto': txt(tds[3]), 'natureza': tr.get('data-nat', ''), 'naturezaLabel': txt(tds[4])})
    fichas[key] = f

data = {
    'produto': 'AR Preview', 'tagline': 'a semana na Assembleia da República',
    'edicao': {'numero': 1, 'ano': 2026, 'semana': '19 a 25 de outubro de 2026', 'inicio': '2026-10-19', 'fim': '2026-10-25', 'fecho': '2026-10-19', 'fechoLabel': '19 de outubro de 2026'},
    'unidades': {'UPE': 'Unidade de Pesquisa e Estatísticas', 'DACDP': 'Divisão de Apoio à Coordenação e Decisão Política', 'DAPL': 'Divisão de Apoio ao Processo Legislativo', 'UnIT': 'Unidade de Integridade e Transparência', 'DCIRI': 'Divisão de Cooperação Institucional e Relações Internacionais'},
    'destaques': destaques, 'agenda': agenda, 'fichas': fichas,
    'disclaimer': txt(soup.select_one('p.disc')),
    'metodologia': [txt(li) for li in soup.select('#metodologia ul.pontos li')],
    'pedidos': 'O varrimento mediático das matérias sem ficha carece de pedido prévio, através da Chefe da Unidade de Pesquisa e Estatísticas.',
}
pathlib.Path(sys.argv[2]).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(destaques), len(agenda), list(fichas), sum(len(f['fundo']) for f in fichas.values()))
