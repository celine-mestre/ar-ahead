"""Corpo do email de segunda-feira: resumo por unidade orgânica, gerado do mesmo dados/agenda.json que a página.
As matérias transversais aparecem uma só vez, no topo. Cada matéria tem ligação para a Assembleia da República
(página própria quando a AR a indica; senão, a agenda parlamentar) e, se tiver ficha, para o varrimento no AR Preview.
Logótipo da SGGov servido pela própria página (docs/logo-sggov.png); os emails não aceitam imagens embebidas em base64.
HTML simples com estilos em linha (compatível com o Outlook).
Uso: PAGINA_URL=https://… python scripts/email_resumo.py dados/agenda.json > email.html"""
import json, sys, html, os
d = json.loads(open(sys.argv[1], encoding='utf-8').read())
url = os.environ.get('PAGINA_URL', '').strip()
if url and not url.endswith('/'): url += '/'
AGENDA_AR = 'https://agenda.parlamento.pt/'
ed = d['edicao']
todos = [x for x in d['destaques'] + d['agenda'] if not x.get('retirado') and x['pertinencia'] in ('Imediato', 'Vigilância')]
todos.sort(key=lambda x: (x['data'], x.get('hora') or '99'))
e = html.escape
F = "font-family:Arial,Helvetica,sans-serif;"
LIG = "color:#2B5683;text-decoration:underline"

def ligacao_ar(x):
    """Página da AR para a matéria: a indicada pela AR (comissão, plenário, iniciativa); senão, a agenda parlamentar.
    Prazos acrescentados à mão não têm ligação à agenda."""
    for l in (x.get('ligacoes') or []):
        if 'parlamento.pt' in (l.get('url') or ''): return l['url']
    if x.get('ligacao'): return x['ligacao']
    return None if x.get('manual') else AGENDA_AR

def linha(x):
    cor = '#D02117' if x['pertinencia'] == 'Imediato' else '#BE9C54'
    ar = ligacao_ar(x)
    tema = f'<a href="{e(ar)}" style="color:#171715;text-decoration:none">{e(x["tema"])}</a>' if ar else e(x['tema'])
    extras = []
    if ar: extras.append(f'<a href="{e(ar)}" style="{LIG}">ver na AR</a>')
    if x.get('varrimento') and url: extras.append(f'<a href="{e(url)}#{e(x["varrimento"])}" style="{LIG}">varrimento</a>')
    elif x.get('varrimento'): extras.append('com varrimento')
    novo = ' <span style="background:#fff4c2;color:#6b5200;font-size:11px;padding:0 4px">novo</span>' if x.get('novo') else ''
    mais = f'<br><span style="{F}font-size:11.5px;color:#666">{" · ".join(extras)}</span>' if extras else ''
    return (f'<tr><td style="{F}font-size:12px;color:#555;padding:4px 10px 4px 0;white-space:nowrap;vertical-align:top">{e(x["dataLabel"])}{" · " + e(x["hora"]) if x.get("hora") else ""}</td>'
            f'<td style="{F}font-size:13px;padding:4px 0;vertical-align:top"><span style="color:{cor};font-size:14px">&#9679;</span> {tema}{novo}{mais}</td></tr>')

def bloco(titulo, itens):
    if not itens: return ''
    return (f'<tr><td style="{F}font-size:13px;font-weight:bold;color:#2B5683;padding:14px 0 4px;border-bottom:1px solid #e3e6ea">{e(titulo)}</td></tr>'
            f'<tr><td><table cellpadding="0" cellspacing="0" style="width:100%">{"".join(linha(x) for x in itens)}</table></td></tr>')

transv = [x for x in todos if 'Transversal' in x['uo']]
nomes = d.get('unidades', {})
corpo = bloco('Transversal (todas as unidades)', transv)
for uo in ('DACDP', 'DAPL', 'UPE', 'DCIRI'):
    corpo += bloco(f'{uo} — {nomes.get(uo, "")}', [x for x in todos if uo in x['uo'] and 'Transversal' not in x['uo']])
if not corpo:
    corpo = f'<tr><td style="{F}font-size:13px;color:#555;padding:12px 0">Sem matérias imediatas ou em vigilância à data desta edição.</td></tr>'
n_ime = sum(1 for x in todos if x['pertinencia'] == 'Imediato'); n_vig = len(todos) - n_ime
quando = ed.get('atualizadoLabel') or ed.get('fechoLabel', '')
n_ed = f'edição n.º {ed["numero"]}' + (' (piloto)' if ed.get('estado') == 'piloto' else '')

logo = (f'<td style="width:46px;padding:0 12px 0 0;vertical-align:middle"><div style="background:#ffffff;border-radius:50%;width:46px;height:46px;text-align:center;line-height:46px">'
        f'<img src="{e(url)}logo-sggov.png" width="38" height="38" alt="SGGov" style="display:inline-block;vertical-align:middle;border:0;width:38px;height:38px"></div></td>') if url else ''
b_preview = (f'<a href="{e(url)}" style="{F}display:inline-block;background:#FFD200;color:#171715;text-decoration:none;font-weight:bold;font-size:13px;padding:9px 16px;border-radius:6px;margin:0 8px 6px 0">Abrir o AR Preview</a>') if url else ''
b_ar = (f'<a href="{AGENDA_AR}" style="{F}display:inline-block;background:#ffffff;color:#2B5683;text-decoration:none;font-weight:bold;font-size:13px;padding:8px 15px;border-radius:6px;border:1px solid #2B5683;margin:0 0 6px">Agenda parlamentar no site da AR</a>')

print(f'''<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<table cellpadding="0" cellspacing="0" style="width:100%;max-width:680px;border:1px solid #e3e6ea">
<tr><td style="background:#1a3f6f;border-bottom:3px solid #D02117;padding:14px 18px">
  <table cellpadding="0" cellspacing="0"><tr>{logo}<td style="vertical-align:middle">
    <div style="{F}color:#dfe6ee;font-size:10.5px;letter-spacing:.06em">SECRETARIA-GERAL DO GOVERNO · DSSD</div>
    <div style="{F}color:#fff;font-size:20px;font-weight:bold;margin-top:2px">AR Preview</div>
  </td></tr></table>
  <div style="{F}color:#FFD200;font-size:14px;font-weight:bold;margin-top:8px">{e(ed["semana"])}</div>
  <div style="{F}color:#dfe6ee;font-size:11.5px;margin-top:4px">A semana na Assembleia da República · {n_ed} · atualizada a {e(quando)}</div>
</td></tr>
<tr><td style="padding:12px 18px 4px">
  <div style="{F}font-size:13px;color:#171715"><b style="color:#D02117">{n_ime}</b> matérias imediatas e <b style="color:#BE9C54">{n_vig}</b> em vigilância para as unidades da DSSD; {len(d.get("fichas", {}))} com ficha de varrimento.</div>
</td></tr>
<tr><td style="padding:0 18px"><table cellpadding="0" cellspacing="0" style="width:100%">{corpo}</table></td></tr>
<tr><td style="padding:16px 18px">{b_preview}{b_ar}
  <div style="{F}font-size:11.5px;color:#666;margin-top:10px">Calendário, cartões e fichas de varrimento na página do AR Preview, atualizada diariamente; o PDF segue em anexo. A agenda da Assembleia da República pode mudar depois desta edição. Pedidos de varrimento adicionais: Chefe da Unidade de Pesquisa e Estatísticas.</div>
</td></tr>
<tr><td style="background:#0E7433;border-top:3px solid #D02117;padding:8px 18px;{F}font-size:11px;color:#e9f2ec">Secretaria-Geral do Governo · Direção de Serviços de Suporte à Decisão · Unidade de Pesquisa e Estatísticas</td></tr>
</table>''')
