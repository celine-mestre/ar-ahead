"""Passo 1 — recolha da Agenda Parlamentar (dados abertos da AR) para a semana seguinte.

ESQUELETO: o endereço do ficheiro de dados abertos e os nomes dos campos têm de ser confirmados
na página «Agenda Parlamentar» dos Dados Abertos da AR (parlamento.pt > Cidadania > Dados abertos).
A Ana Luísa já tem este passo a funcionar e a produzir um Excel; o objetivo é trazê-lo para aqui,
a escrever diretamente dados/agenda_bruta.json com a estrutura abaixo.

Estrutura de saída (uma entrada por reunião/ponto):
  {"tema": ..., "data": "AAAA-MM-DD", "hora": "9h30", "interveniente": ..., "tipo": [...],
   "tipoLabel": ..., "resumo": ..., "ordemTrabalhos": ..., "orgao": ..., "ligacao": ...}
"""
import json, pathlib, datetime, sys, urllib.request

URL_AGENDA = "A_CONFIRMAR"   # ficheiro JSON/XML dos dados abertos da AR (secção Agenda Parlamentar)

def semana_seguinte(hoje=None):
    hoje = hoje or datetime.date.today()
    seg = hoje + datetime.timedelta(days=(7 - hoje.weekday()) % 7 or 7)   # próxima segunda-feira
    return seg, seg + datetime.timedelta(days=6)

def descarregar(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()

def normalizar(bruto, ini, fim):
    """Converte os registos da AR na estrutura interna e filtra a semana [ini, fim]."""
    saida = []
    for reg in bruto:            # adaptar aos nomes reais dos campos
        data = reg.get('data')   # ex.: "2026-10-20"
        if not data or not (ini.isoformat() <= data[:10] <= fim.isoformat()):
            continue
        saida.append({
            'tema': reg.get('titulo') or reg.get('orgao'),
            'data': data[:10], 'hora': reg.get('hora', ''),
            'interveniente': reg.get('interveniente', ''),
            'tipo': reg.get('tipos', []), 'tipoLabel': '; '.join(reg.get('tipos', [])),
            'resumo': (reg.get('ordem_trabalhos') or '')[:300],
            'ordemTrabalhos': reg.get('ordem_trabalhos') or '',
            'orgao': reg.get('orgao', ''), 'ligacao': reg.get('ligacao', ''),
        })
    return saida

if __name__ == '__main__':
    ini, fim = semana_seguinte()
    if URL_AGENDA == 'A_CONFIRMAR':
        sys.exit('Definir URL_AGENDA (e os nomes dos campos em normalizar) antes de correr.')
    bruto = json.loads(descarregar(URL_AGENDA))
    itens = normalizar(bruto, ini, fim)
    pathlib.Path('dados/agenda_bruta.json').write_text(json.dumps({'inicio': ini.isoformat(), 'fim': fim.isoformat(), 'recolha': datetime.datetime.now().isoformat(timespec='minutes'), 'itens': itens}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(len(itens), 'itens para a semana de', ini, 'a', fim)
