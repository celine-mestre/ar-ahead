"""Ficheiros de calendário (.ics) para o Outlook: um por matéria (docs/cal/<id>.ics) e um com as matérias imediatas e em
vigilância da semana (docs/cal/semana.ics). Abrir o ficheiro no Outlook acrescenta o evento ao calendário de quem o abre.
Horas convertidas para UTC (o Outlook mostra-as na hora local); hora de fim indicativa (2 horas).
Uso: PAGINA_URL=https://… python scripts/calendario.py dados/agenda.json docs/cal"""
import json, sys, os, pathlib
sys.path.insert(0, os.path.dirname(__file__))
from sintese import ics, cal_nome

d = json.loads(open(sys.argv[1], encoding='utf-8').read())
pasta = pathlib.Path(sys.argv[2]); pasta.mkdir(parents=True, exist_ok=True)
url = os.environ.get('PAGINA_URL', 'https://celine-mestre.github.io/ar-ahead/')
itens = [x for x in d['destaques'] + d['agenda'] + d.get('futuro', []) if not x.get('retirado') and x.get('data')]
for velho in pasta.glob('*.ics'): velho.unlink()                # só ficam os da edição em vigor
for x in itens:
    (pasta / cal_nome(x)).write_text(ics([x], url), encoding='utf-8', newline='')
semana = [x for x in d['destaques'] + d['agenda'] if not x.get('retirado') and x.get('data') and x.get('pertinencia') in ('Imediato', 'Vigilância')]
semana.sort(key=lambda x: (x['data'], x.get('hora') or '99'))
(pasta / 'semana.ics').write_text(ics(semana, url, f"AR Preview · {d['edicao'].get('semana', '')}"), encoding='utf-8', newline='')
print(f'{len(itens)} ficheiros de calendário + semana.ics ({len(semana)} matérias)')
