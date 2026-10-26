"""Passo 2 — triagem automática: propõe unidade orgânica e pertinência a partir de dados/regras_uo.json.
A revisão humana (UPE) confirma ou corrige no ficheiro resultante (dados/triagem_proposta.json) antes do varrimento.
"""
import json, pathlib, re, sys
if not pathlib.Path('dados/agenda_bruta.json').exists():
    print('Sem recolha nova — triagem não feita.'); sys.exit(0)
regras = json.loads(pathlib.Path('dados/regras_uo.json').read_text(encoding='utf-8'))
bruto = json.loads(pathlib.Path('dados/agenda_bruta.json').read_text(encoding='utf-8'))
def triar(item):
    texto = ' '.join([item['tema'], item['resumo'], item['ordemTrabalhos'], item['interveniente']]).lower()
    uos, pert = set(), 'Registo'
    for uo, cfg in regras['unidades'].items():
        if any(re.search(r'\b'+re.escape(t.lower())+r'\b', texto) for t in cfg['termos']):
            uos.add(uo)
            if any(re.search(r'\b'+re.escape(t.lower())+r'\b', texto) for t in cfg.get('imediato', [])): pert = 'Imediato'
            elif pert != 'Imediato': pert = 'Vigilância'
    if any(t in texto for t in regras.get('transversal', [])): uos.add('Transversal'); pert = pert if pert=='Imediato' else 'Vigilância'
    if any(t in texto for t in regras.get('governo', {}).get('termos', [])):   # presença do Governo na AR: coordenação política
        uos.add('DACDP'); pert = pert if pert=='Imediato' else 'Vigilância'
    return sorted(uos), pert
for it in bruto['itens'] + bruto.get('futuro', []):
    it['uo'], it['pertinencia'] = triar(it)
    it['validado'] = False          # a revisão humana muda para true (ou corrige uo/pertinencia)
pathlib.Path('dados/triagem_proposta.json').write_text(json.dumps(bruto, ensure_ascii=False, indent=1), encoding='utf-8')
n = len(bruto['itens']); print(n, 'itens;', sum(1 for i in bruto['itens'] if i['uo']), 'com unidade proposta;', sum(1 for i in bruto['itens'] if i['pertinencia']=='Imediato'), 'imediato')
