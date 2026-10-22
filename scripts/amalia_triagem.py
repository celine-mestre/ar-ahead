"""Passo 2b — triagem assistida pelo Amália: para cada matéria sem unidade (ou todas, com --tudo),
propõe ASSUNTO (em vez do nome da comissão), resumo de duas linhas, unidades e pertinência,
com as competências de dados/competencias_dssd.json como critério. A Ana Luísa valida.
As regras por palavras-chave (triar.py) correm antes; o Amália só decide o que as regras não decidiram."""
import json, pathlib, sys
from amalia import perguntar, json_da_resposta

comp = json.loads(pathlib.Path('dados/competencias_dssd.json').read_text(encoding='utf-8'))
dados = json.loads(pathlib.Path('dados/triagem_proposta.json').read_text(encoding='utf-8'))
tudo = '--tudo' in sys.argv

SISTEMA = f"""És um analista da Direção de Serviços de Suporte à Decisão (DSSD) da Secretaria-Geral do Governo de Portugal.
Classificas matérias da agenda da Assembleia da República. Responde SÓ com JSON, em português europeu.
Unidades e competências (só estas quatro; nunca inventes outras):
{json.dumps(comp, ensure_ascii=False, indent=1)}
Pertinência: "Imediato" = a unidade tem de preparar algo antes da reunião; "Vigilância" = convém acompanhar; "Registo" = não interessa à DSSD.
"Transversal" junta-se às unidades quando a matéria é de todo o Governo (Orçamento do Estado, Conta Geral do Estado, Reforma do Estado).
Se nenhuma unidade for claramente competente, devolve "uo": [] e "pertinencia": "Registo". Não forces atribuições."""

def pedir(item):
    u = f"""Reunião: {item['tema']}
Data e hora: {item['data']} {item.get('hora','')}
Tipo: {item.get('tipoLabel','')}
Interveniente: {item.get('interveniente','')}
Ordem de trabalhos: {(item.get('ordemTrabalhos') or item.get('resumo',''))[:3500]}

Devolve: {{"assunto": "título curto com o ASSUNTO principal (não o nome da comissão)", "resumo": "duas frases", "uo": ["DACDP"|"DAPL"|"UPE"|"DCIRI"|"Transversal"], "pertinencia": "Imediato"|"Vigilância"|"Registo", "justificacao": "uma frase com o ponto da ordem de trabalhos que decide"}}"""
    return json_da_resposta(perguntar(SISTEMA, u, max_tokens=400))

n = 0
for it in dados['itens']:
    if it.get('validado') or (it['uo'] and not tudo): continue
    r = pedir(it)
    if not r: continue
    it['amalia'] = {k: r.get(k) for k in ('assunto', 'resumo', 'uo', 'pertinencia', 'justificacao')}
    # a proposta do Amália só preenche o que estava vazio; nunca sobrepõe as regras validadas
    if not it['uo']:
        it['uo'] = [u for u in (r.get('uo') or []) if u in ('DACDP', 'DAPL', 'UPE', 'DCIRI', 'Transversal')]
        it['pertinencia'] = r.get('pertinencia') if r.get('pertinencia') in ('Imediato', 'Vigilância', 'Registo') else it['pertinencia']
    if r.get('assunto'): it['tema'] = r['assunto']; it['orgao'] = it.get('orgao') or it['tema']
    if r.get('resumo'): it['resumo'] = r['resumo']
    n += 1
pathlib.Path('dados/triagem_proposta.json').write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding='utf-8')
print(n, 'matérias classificadas pelo Amália (a validar)')
