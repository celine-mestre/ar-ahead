"""Corpo do email de segunda-feira: resumo por unidade orgânica, gerado do mesmo dados/agenda.json que a página.
As matérias transversais aparecem uma só vez, no topo. HTML simples com estilos em linha (compatível com o Outlook).
Uso: PAGINA_URL=https://… python scripts/email_resumo.py dados/agenda.json > email.html"""
import json, sys, html, os
d = json.loads(open(sys.argv[1], encoding='utf-8').read())
url = os.environ.get('PAGINA_URL', '')
ed = d['edicao']
todos = [x for x in d['destaques'] + d['agenda'] if not x.get('retirado') and x['pertinencia'] in ('Imediato', 'Vigilância')]
todos.sort(key=lambda x: (x['data'], x.get('hora') or '99'))
e = html.escape
F = "font-family:Arial,Helvetica,sans-serif;"
def linha(x):
    cor = '#D02117' if x['pertinencia'] == 'Imediato' else '#BE9C54'
    ficha = ' · <i>com varrimento</i>' if x.get('varrimento') else ''
    novo = ' <span style="background:#fff4c2;color:#6b5200;font-size:11px;padding:0 4px">novo</span>' if x.get('novo') else ''
    return (f'<tr><td style="{F}font-size:12px;color:#555;padding:3px 10px 3px 0;white-space:nowrap;vertical-align:top">{e(x["dataLabel"])}{" · " + e(x["hora"]) if x.get("hora") else ""}</td>'
            f'<td style="{F}font-size:13px;padding:3px 0;vertical-align:top"><span style="color:{cor};font-size:14px">&#9679;</span> {e(x["tema"])}{ficha}{novo}</td></tr>')
def bloco(titulo, itens):
    if not itens: return ''
    return (f'<tr><td style="{F}font-size:13px;font-weight:bold;color:#2B5683;padding:14px 0 4px;border-bottom:1px solid #e3e6ea">{e(titulo)}</td></tr>'
            f'<tr><td><table cellpadding="0" cellspacing="0" style="width:100%">{"".join(linha(x) for x in itens)}</table></td></tr>')
transv = [x for x in todos if 'Transversal' in x['uo']]
nomes = d.get('unidades', {})
corpo = bloco('Transversal (todas as unidades)', transv)
for uo in ('DACDP', 'DAPL', 'UPE', 'DCIRI'):
    corpo += bloco(f'{uo} — {nomes.get(uo, "")}', [x for x in todos if uo in x['uo'] and 'Transversal' not in x['uo']])
n_ime = sum(1 for x in todos if x['pertinencia'] == 'Imediato'); n_vig = len(todos) - n_ime
quando = ed.get('atualizadoLabel') or ed.get('fechoLabel', '')
botao = (f'<a href="{e(url)}" style="{F}display:inline-block;background:#FFD200;color:#171715;text-decoration:none;font-weight:bold;font-size:13px;padding:9px 16px;border-radius:6px">Abrir o AR Ahead</a>') if url else ''
print(f'''<table cellpadding="0" cellspacing="0" style="width:100%;max-width:680px;border:1px solid #e3e6ea">
<tr><td style="background:#1a3f6f;border-bottom:3px solid #D02117;padding:14px 18px">
  <div style="{F}color:#fff;font-size:20px;font-weight:bold">AR Ahead</div>
  <div style="{F}color:#FFD200;font-size:14px;font-weight:bold;margin-top:2px">{e(ed["semana"])}</div>
  <div style="{F}color:#dfe6ee;font-size:11.5px;margin-top:4px">A semana na Assembleia da República · edição n.º {ed.get("numero")} · atualizada a {e(quando)}</div>
</td></tr>
<tr><td style="padding:12px 18px 4px">
  <div style="{F}font-size:13px;color:#171715"><b style="color:#D02117">{n_ime}</b> matérias imediatas e <b style="color:#BE9C54">{n_vig}</b> em vigilância para as unidades da DSSD; {len(d.get("fichas", {}))} com ficha de varrimento.</div>
</td></tr>
<tr><td style="padding:0 18px"><table cellpadding="0" cellspacing="0" style="width:100%">{corpo}</table></td></tr>
<tr><td style="padding:16px 18px">{botao}
  <div style="{F}font-size:11.5px;color:#666;margin-top:10px">Calendário, cartões e fichas de varrimento na página, atualizada diariamente; o PDF segue em anexo. Pedidos de varrimento adicionais: Chefe da Unidade de Pesquisa e Estatísticas.</div>
</td></tr>
<tr><td style="background:#0E7433;border-top:3px solid #D02117;padding:8px 18px;{F}font-size:11px;color:#e9f2ec">Secretaria-Geral do Governo · Direção de Serviços de Suporte à Decisão · Unidade de Pesquisa e Estatísticas</td></tr>
</table>''')
