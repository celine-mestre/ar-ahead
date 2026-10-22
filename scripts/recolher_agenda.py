"""Passo 1 — recolha diária da Agenda Parlamentar a partir dos DADOS ABERTOS da Assembleia da República.

Fonte: parlamento.pt › Cidadania › Dados abertos › Agenda Parlamentar › XVII Legislatura › AgendaParlamentar_json.txt
(lista JSON com as reuniões publicadas: Plenário, comissões, grupos de trabalho, etc.; janela móvel a partir de ontem).
Se o endereço direto deixar de funcionar, o script vai à página da pasta e procura de novo a ligação do ficheiro.

Semana-alvo: de segunda a quinta, a semana em curso; de sexta a domingo, a semana seguinte.
Saída: dados/agenda_bruta.json  →  usado por triar.py e montar_edicao.py
Uso: python scripts/recolher_agenda.py [--ficheiro AgendaParlamentar_json.txt] [--semana AAAA-MM-DD]
"""
import json, pathlib, datetime, sys, urllib.request, re, html

URL_AGENDA = "https://app.parlamento.pt/webutils/docs/doc.txt?path=fxkkyG0F2jR%2fL3LMNV0qF1JgWJiaoLvU23RDQflJ4%2fXJwdHaW2uvdFy0D%2bA%2bm7td49uC1M4ipPpx1vOby%2bHpFQjqjUHgC9CR%2fL%2fKZi39QqN%2b8%2bviTj9iPLgwgqj%2b8xe52jxlznSrRwrzeRTK8zv5V8Uu5HBOgvGtaGL%2b1bJWgzGLkV2IqcEYbT7Hpue%2b5vHy5wfR%2bRNZNy9jnEKvaTkW4up7NVxEoZABcdfGv7VRhZ53cHQ1%2fzb1MLTmD9jvqO1kyJ7ePsgv%2bmxt7WeTAPdOiKHCtBSe6DMqL2qcxRHiJsQBIFZcMTamQL95puZga%2bodwh238749aRuSE8hLot%2f6ObkB2VAiDuGX%2fbNlySmM3auUIULk1UWwgozCVOo29y1uySEBmBnvLjk7%2fyMRSSWPDA%3d%3d&fich=AgendaParlamentar_json.txt&Inline=true"
URL_PASTA = "https://www.parlamento.pt/Cidadania/Paginas/DABoletimInformativo.aspx?t=57465a4a5353424d5a576470633278686448567959513d3d"
SECCOES = ('Plenário', 'Comissões Parlamentares', 'Grupo de Trabalho', 'Conferência de Líderes', 'Comissão Permanente')   # o resto (visitas, audiências dos grupos parlamentares, agenda do Presidente) fica de fora

def semana_alvo(hoje=None):
    """De segunda a quinta: a semana em curso. De sexta a domingo: a semana seguinte."""
    hoje = hoje or datetime.date.today()
    seg = hoje - datetime.timedelta(days=hoje.weekday())
    if hoje.weekday() >= 4:
        seg += datetime.timedelta(days=7)
    return seg, seg + datetime.timedelta(days=6)

def descarregar(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AR Ahead; SGGov/DSSD/UPE)'})
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode('utf-8-sig')

def obter():
    try:
        return json.loads(descarregar(URL_AGENDA))
    except Exception as e:
        print('Endereço direto falhou (', e, ') — a procurar a ligação na página dos dados abertos')
        pag = descarregar(URL_PASTA)
        m = re.search(r'href="([^"]*fich=AgendaParlamentar_json\.txt[^"]*)"', pag)
        if not m: raise SystemExit('Ligação do AgendaParlamentar_json.txt não encontrada na página dos dados abertos.')
        return json.loads(descarregar(html.unescape(m.group(1))))

def texto(h):
    t = html.unescape(html.unescape(h or ''))
    t = re.sub(r'<br\s*/?>|</p>|</li>', '\n', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'[ \t​]+', ' ', re.sub(r'\n\s*\n+', '\n', t)).strip()

def hora(x, txt):
    if x.get('Section') == 'Plenário':                      # no Plenário, a hora certa vem na ordem do dia
        m = re.search(r'\b(\d{1,2})H(\d{2})\b', txt)
        if m: return f"{int(m.group(1))}h{m.group(2)}"
    t = x.get('EventStartTime') or ''
    return f"{int(t[:2])}h{t[3:5]}" if re.match(r'\d{2}:\d{2}', t) else ''

def tema(x, txt):
    if x.get('Section') == 'Plenário':
        t = re.sub(r'ORDEM DO DIA|\(sujeito a altera\w+\)|\b\d{1,2}H\d{2}\b|^\s*\d+\s*-\s*', ' ', txt)
        t = re.sub(r'^\d+\s*-\s*', '', re.sub(r'\s+', ' ', t).strip())
        t = re.split(r'\s(?:Proposta|Projeto|Debate na Generalidade|GOV \d|\d+\s*-)\s', t)[0]
        return ('Plenário — ' + t.strip(' -:'))[:120] if t.strip() else 'Plenário'
    return (x.get('OrgDes') or x.get('Title') or '').split(' | ')[0].strip()

def normalizar(bruto, ini, fim):
    saida = []
    for x in bruto:
        if x.get('Section') not in SECCOES: continue
        try: data = datetime.datetime.strptime(x['EventStartDate'], '%d/%m/%Y').date()
        except Exception: continue
        if not (ini <= data <= fim): continue
        txt = texto(x.get('InternetText'))
        saida.append({
            'id_ar': x.get('Id'), 'data': data.isoformat(), 'hora': hora(x, txt),
            'tema': tema(x, txt), 'orgao': (x.get('OrgDes') or x.get('Title') or '').split(' | ')[0].strip(),
            'interveniente': '', 'tipo': [x.get('Section')], 'tipoLabel': ' · '.join(filter(None, [x.get('Section'), x.get('Subtitle'), x.get('Local')])),
            'resumo': txt[:300], 'ordemTrabalhos': txt, 'ligacao': x.get('Link') or '',
        })
    return saida

if __name__ == '__main__':
    args = sys.argv[1:]
    hoje = datetime.date.fromisoformat(args[args.index('--semana') + 1]) if '--semana' in args else None
    ini, fim = semana_alvo(hoje)
    bruto = json.loads(pathlib.Path(args[args.index('--ficheiro') + 1]).read_text(encoding='utf-8-sig')) if '--ficheiro' in args else obter()
    itens = normalizar(bruto, ini, fim)
    pathlib.Path('dados').mkdir(exist_ok=True)
    pathlib.Path('dados/agenda_bruta.json').write_text(json.dumps({'inicio': ini.isoformat(), 'fim': fim.isoformat(), 'recolha': datetime.datetime.now().isoformat(timespec='minutes'), 'fonte': 'Dados abertos da Assembleia da República — AgendaParlamentar_json.txt', 'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(bruto)} registos na fonte; {len(itens)} para a semana de {ini} a {fim}')
