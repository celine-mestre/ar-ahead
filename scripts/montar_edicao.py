"""Passo 2c — monta dados/agenda.json (a edição) a partir de dados/triagem_proposta.json.
Corre na segunda-feira antes do varrimento. Só monta se a triagem for de uma semana mais recente do que a edição em vigor.
- «Imediato» → destaques (o Amália gera-lhes a ficha a seguir); o resto → agenda.
- Se nem todas as matérias estiverem validadas pela Ana Luísa, a edição sai marcada «automática, não revista»."""
import json, pathlib, datetime, sys
tri_p, ag_p = pathlib.Path('dados/triagem_proposta.json'), pathlib.Path('dados/agenda.json')
if not tri_p.exists():
    print('Sem triagem nova — mantém-se a edição em vigor.'); sys.exit(0)
tri = json.loads(tri_p.read_text(encoding='utf-8'))
ant = json.loads(ag_p.read_text(encoding='utf-8')) if ag_p.exists() else {}
if ant and tri['inicio'] <= ant['edicao']['inicio']:
    print('A triagem não é de uma semana nova — mantém-se a edição em vigor.'); sys.exit(0)
DIAS = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
def d(s): return datetime.date.fromisoformat(s)
def rotulo(s): x = d(s); return f"{DIAS[x.weekday()]}, {x.day} {MESES[x.month-1][:3]}"
def extenso(x, ano=True): return f"{x.day} de {MESES[x.month-1]}" + (f" de {x.year}" if ano else '')
ini, fim = d(tri['inicio']), d(tri['fim'])
semana = f"{extenso(ini, ini.year != fim.year)} a {extenso(fim)}" if ini.month != fim.month else f"{ini.day} a {extenso(fim)}"
validadas = all(i.get('validado') for i in tri['itens'])
destaques, agenda = [], []
for i in tri['itens']:
    x = {k: i.get(k, '') for k in ('tema', 'data', 'hora', 'interveniente', 'tipoLabel', 'resumo', 'ordemTrabalhos')}
    x.update(dataLabel=rotulo(i['data']), tipo=i.get('tipo', []), uo=i.get('uo', []), pertinencia=i.get('pertinencia', 'Registo'),
             periodo='Manhã' if (i.get('hora') or '99')[:2] < '13' else 'Tarde', ligacoes=[{'titulo': 'Agenda parlamentar', 'url': i['ligacao']}] if i.get('ligacao') else [])
    (destaques if x['pertinencia'] == 'Imediato' else agenda).append(x)
recolha = tri.get('recolha', '')[:10]
ed = {'numero': ant.get('edicao', {}).get('numero', 0) + 1, 'ano': ini.year, 'semana': semana, 'inicio': tri['inicio'], 'fim': tri['fim'],
      'fecho': recolha, 'fechoLabel': extenso(d(recolha)) if recolha else ''}
if not validadas:
    ed.update(estado='automática, não revista', aviso='Esta edição foi montada e triada automaticamente (regras e Amália) e não foi revista pela Unidade de Pesquisa e Estatísticas. As fichas de varrimento, quando existem, foram geradas a partir do corpus do Radar de Notícias e não incluem a verificação de números.')
nova = {k: ant[k] for k in ('produto', 'tagline', 'unidades', 'disclaimer', 'metodologia', 'pedidos') if k in ant}
nova.update(edicao=ed, destaques=destaques, agenda=agenda, fichas={})
ag_p.write_text(json.dumps(nova, ensure_ascii=False, indent=1), encoding='utf-8')
print(f"Edição n.º {ed['numero']} montada: {semana} · {len(destaques)} destaques · {len(agenda)} na agenda · {'validada' if validadas else 'NÃO revista'}")
