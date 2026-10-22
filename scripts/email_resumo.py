"""Passo 4 — corpo do email: resumo por unidade orgânica (6 a 8 linhas), gerado do mesmo agenda.json."""
import json, sys, html, os
d = json.loads(open(sys.argv[1], encoding='utf-8').read())
todos = [x for x in d['destaques'] + d['agenda'] if not x.get('retirado')]
url = os.environ.get('PAGINA_URL', '')
uos = ['Transversal'] + list(d['unidades'])
def linhas(uo):
    its = [x for x in todos if uo in x['uo'] and x['pertinencia'] in ('Imediato','Vigilância')]
    its.sort(key=lambda x: (x['pertinencia']!='Imediato', x['data'], x.get('hora','')))
    return its[:4]
out = [f"<p style='font-family:Arial,sans-serif;font-size:14px'><b>AR Ahead · a semana na Assembleia da República · {html.escape(d['edicao']['semana'])}</b><br>Fecho: {html.escape(d['edicao']['fechoLabel'])}. {len(d['destaques'])} destaques com varrimento; {sum(1 for x in todos if x['pertinencia']=='Imediato')} matérias imediatas.</p>"]
for uo in uos:
    its = linhas(uo)
    if not its: continue
    out.append(f"<p style='font-family:Arial,sans-serif;font-size:13px;margin:6px 0'><b>{html.escape(uo)}</b><br>" + '<br>'.join(f"{'&#9679;' if x['pertinencia']=='Imediato' else '&#9675;'} {html.escape(x['dataLabel'])}{' '+html.escape(x['hora']) if x.get('hora') else ''} — {html.escape(x['tema'])}" for x in its) + "</p>")
lig = f"<a href='{html.escape(url)}'>{html.escape(url)}</a> (atualizada diariamente)" if url else 'o ficheiro anexo'
out.append(f"<p style='font-family:Arial,sans-serif;font-size:12px;color:#555'>Detalhe, calendário e fichas de varrimento em {lig}. Pedidos de varrimento adicionais: Chefe da Unidade de Pesquisa e Estatísticas.</p>")
print('\n'.join(out))
