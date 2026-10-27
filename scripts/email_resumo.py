"""Corpo do email de segunda-feira: lista única das matérias imediatas e em vigilância, por ordem cronológica, gerada do mesmo
dados/agenda.json que a página. Cada matéria leva:
  - a etiqueta da unidade (ou «Transversal») a que se aplica;
  - o membro do Governo presente e uma síntese muito curta da sessão (scripts/sintese.py; só texto publicado pela AR);
  - ligação à página própria na AR (da matéria ou da comissão) só quando existe — a agenda geral não, porque o conteúdo
    dela já vai no email;
  - «adicionar ao calendário» (ficheiro .ics que o Outlook abre como evento) e, se houver ficha, o varrimento.
As emissões não têm ligação própria antecipada: indica-se o Canal Parlamento.
Logótipo da SGGov servido pela própria página (docs/logo-sggov-email.png); HTML simples com estilos em linha (Outlook).
Uso: PAGINA_URL=https://… python scripts/email_resumo.py dados/agenda.json [assunto.txt] > email.html"""
import json, sys, html, os
sys.path.insert(0, os.path.dirname(__file__))
from sintese import membro_governo, sintese, pagina_ar, cal_nome, CANAL
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

def linha(x):
    cor = '#D02117' if x['pertinencia'] == 'Imediato' else '#BE9C54'
    pag, rotulo = pagina_ar(x)
    tema = f'<a href="{e(pag)}" style="color:#171715;text-decoration:none;font-weight:bold">{e(x["tema"])}</a>' if pag else f'<b>{e(x["tema"])}</b>'
    gov, sin = membro_governo(x), sintese(x)
    info = ''
    if gov: info += f'<br><span style="{F}font-size:12px;color:#171715"><span style="color:#666">Governo:</span> {e(gov)}</span>'
    if sin: info += f'<br><span style="{F}font-size:12px;color:#555">{e(sin)}</span>'
    extras = []
    if pag: extras.append(f'<a href="{e(pag)}" style="{LIG}">{rotulo}</a>')
    if x.get('varrimento') and url: extras.append(f'<a href="{e(url)}#{e(x["varrimento"])}" style="{LIG}">varrimento</a>')
    elif x.get('varrimento'): extras.append('com varrimento')
    if url and x.get('data'): extras.append(f'<a href="{e(url)}cal/{e(cal_nome(x))}" style="{LIG}">adicionar ao calendário</a>')
    novo = ' <span style="background:#fff4c2;color:#6b5200;font-size:11px;padding:0 4px">novo</span>' if x.get('novo') else ''
    mais = f'<br><span style="{F}font-size:11.5px;color:#666">{" · ".join(extras)}</span>' if extras else ''
    return (f'<tr><td style="{F}font-size:12px;color:#555;padding:8px 10px 8px 0;white-space:nowrap;vertical-align:top;border-bottom:1px solid #eef0f3">{e(x["dataLabel"])}{" · " + e(x["hora"]) if x.get("hora") else ""}</td>'
            f'<td style="{F}font-size:13px;padding:8px 0;vertical-align:top;border-bottom:1px solid #eef0f3"><span style="color:{cor};font-size:14px">&#9679;</span> {tema}{novo}{info}<br>{etiquetas(x)}{mais}</td></tr>')

nomes = d.get('unidades', {})
def etiquetas(x):
    """Etiqueta de cada unidade (ou «Transversal», que serve todas) a que a matéria se aplica."""
    uos = ['Transversal'] if 'Transversal' in x['uo'] else [u for u in ('DACDP', 'DAPL', 'UPE', 'DCIRI') if u in x['uo']]
    est = f'{F}display:inline-block;font-size:10.5px;font-weight:bold;padding:1px 6px;margin:3px 4px 0 0;border-radius:3px;'
    return ''.join(
        f'<span style="{est}background:#2B5683;color:#ffffff" title="todas as unidades da DSSD">Transversal</span>' if u == 'Transversal'
        else f'<span style="{est}background:#e8eef5;color:#2B5683" title="{e(nomes.get(u, ""))}">{e(u)}</span>' for u in uos)

# lista única, por ordem cronológica; a unidade de cada matéria vai em etiqueta
corpo = (f'<tr><td><table cellpadding="0" cellspacing="0" style="width:100%">{"".join(linha(x) for x in todos)}</table></td></tr>') if todos else ''
if not corpo:
    corpo = f'<tr><td style="{F}font-size:13px;color:#555;padding:12px 0">Sem matérias imediatas ou em vigilância à data desta edição.</td></tr>'
n_ime = sum(1 for x in todos if x['pertinencia'] == 'Imediato'); n_vig = len(todos) - n_ime
quando = ed.get('atualizadoLabel') or ed.get('fechoLabel', '')
n_ed = f'edição n.º {ed["numero"]}' + (' (piloto)' if ed.get('estado') == 'piloto' else '')

# disco branco já desenhado na imagem (transparente à volta): fica redondo também no Outlook, que ignora border-radius
logo = (f'<td style="width:46px;padding:0 12px 0 0;vertical-align:middle">'
        f'<img src="{e(url)}logo-sggov-email.png" width="46" height="46" alt="SGGov" style="display:block;border:0;width:46px;height:46px"></td>') if url else ''
legenda = ' · '.join(f'<b>{e(u)}</b> {e(nomes[u])}' for u in ('DACDP', 'DAPL', 'UPE', 'DCIRI') if nomes.get(u))
b_preview = (f'<a href="{e(url)}" style="{F}display:inline-block;background:#FFD200;color:#171715;text-decoration:none;font-weight:bold;font-size:13px;padding:9px 16px;border-radius:6px;margin:0 8px 6px 0">Abrir o AR Preview</a>') if url else ''
BT = f'{F}display:inline-block;background:#ffffff;color:#2B5683;text-decoration:none;font-weight:bold;font-size:13px;padding:8px 15px;border-radius:6px;border:1px solid #2B5683;margin:0 8px 6px 0'
b_ar = f'<a href="{AGENDA_AR}" style="{BT}">Agenda parlamentar</a>'
b_canal = f'<a href="{CANAL}" style="{BT}">Canal Parlamento (emissões)</a>'
b_cal = f'<a href="{e(url)}cal/semana.ics" style="{BT}">Todas no calendário</a>' if url and todos else ''

print(f'''<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<table cellpadding="0" cellspacing="0" style="width:100%;max-width:680px;border:1px solid #e3e6ea">
<tr><td style="background:#1a3f6f;border-bottom:3px solid #D02117;padding:14px 18px">
  <table cellpadding="0" cellspacing="0"><tr>{logo}<td style="vertical-align:middle">
    <div style="{F}color:#dfe6ee;font-size:10.5px;letter-spacing:.06em">SECRETARIA-GERAL DO GOVERNO · SUPORTE À DECISÃO</div>
    <div style="{F}color:#fff;font-size:20px;font-weight:bold;margin-top:2px">AR Preview</div>
  </td></tr></table>
  <div style="{F}color:#FFD200;font-size:14px;font-weight:bold;margin-top:8px">{e(ed["semana"])}</div>
  <div style="{F}color:#dfe6ee;font-size:11.5px;margin-top:4px">A semana na Assembleia da República · {n_ed} · atualizada a {e(quando)}</div>
</td></tr>
<tr><td style="padding:12px 18px 4px">
  <div style="{F}font-size:13px;color:#171715"><b style="color:#D02117">{n_ime}</b> matérias imediatas e <b style="color:#BE9C54">{n_vig}</b> em vigilância para as unidades da DSSD; {len(d.get("fichas", {}))} com ficha de varrimento.</div>
  {f'<div style="{F}font-size:11px;color:#666;margin-top:6px">{legenda}</div>' if legenda else ''}
</td></tr>
<tr><td style="padding:0 18px"><table cellpadding="0" cellspacing="0" style="width:100%">{corpo}</table></td></tr>
<tr><td style="padding:16px 18px">{b_preview}{b_cal}{b_ar}{b_canal}
  <div style="{F}font-size:11.5px;color:#666;margin-top:10px">Calendário, cartões e fichas de varrimento na página do AR Preview, atualizada diariamente; o PDF segue em anexo. «Adicionar ao calendário» abre o evento no Outlook (hora de fim indicativa). As emissões em direto, quando as há, estão no Canal Parlamento. A agenda da Assembleia da República pode mudar depois desta edição. Pedidos de varrimento adicionais: <a href="mailto:upe@sggoverno.gov.pt?subject=AR%20Preview%20%E2%80%94%20pedido%20de%20varrimento" style="color:#2B5683">upe@sggoverno.gov.pt</a>.</div>
</td></tr>
<tr><td style="background:#0E7433;border-top:3px solid #D02117;padding:8px 18px;{F}font-size:11px;color:#e9f2ec">Secretaria-Geral do Governo · Suporte à Decisão</td></tr>
</table>''')

# assunto do email (usado pelo envio): «AR Preview n.º N · semana»
if len(sys.argv) > 2:
    open(sys.argv[2], 'w', encoding='utf-8').write(f'AR Preview n.º {ed["numero"]} · {ed["semana"]} — agenda da Assembleia da República')
