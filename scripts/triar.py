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
    # «Imediato» só pelo que é o assunto principal: o tema, ou toda a ordem do dia no Plenário (nas comissões, uma referência
    # ao Orçamento entre vários pontos vale Vigilância, não Imediato)
    plenario = (item.get('orgao') or item['tema']).startswith('Plenário')
    forte = (item['tema'] + ' ' + (item['ordemTrabalhos'] if plenario else '')).lower()
    uos, pert, crit = set(), 'Registo', []
    for uo, cfg in regras['unidades'].items():
        ime = [t for t in cfg.get('imediato', []) if re.search(r'\b'+re.escape(t.lower())+r'\b', forte)]
        bate = [t for t in cfg['termos'] + [i for i in cfg.get('imediato', []) if i not in cfg['termos']] if t not in ime and re.search(r'\b'+re.escape(t.lower())+r'\b', texto)]
        if bate or ime:   # um termo «imediato» implica a unidade e sobe a pertinência
            uos.add(uo); crit += [f'«{t}» ({uo})' for t in bate[:2]]
            if ime: pert = 'Imediato'; crit += [f'«{t}» ({uo}) → Imediato' for t in ime[:1]]
            elif pert != 'Imediato': pert = 'Vigilância'
    bt = [t for t in regras.get('transversal', []) if t in texto]
    if bt: uos.add('Transversal'); pert = pert if pert=='Imediato' else 'Vigilância'; crit += [f'«{t}» (transversal)' for t in bt[:1]]
    bg = [t for t in regras.get('governo', {}).get('termos', []) if t in texto]
    if bg:   # presença do Governo na AR: coordenação política
        uos.add('DACDP'); pert = pert if pert=='Imediato' else 'Vigilância'; crit += [f'«{t}» (Governo na AR → DACDP)' for t in bg[:1]]
    return sorted(uos), pert, crit
for it in bruto['itens'] + bruto.get('futuro', []):
    it['uo'], it['pertinencia'], it['criterio'] = triar(it)
    it['validado'] = False          # a revisão humana muda para true (ou corrige uo/pertinencia)
pathlib.Path('dados/triagem_proposta.json').write_text(json.dumps(bruto, ensure_ascii=False, indent=1), encoding='utf-8')
n = len(bruto['itens']); print(n, 'itens;', sum(1 for i in bruto['itens'] if i['uo']), 'com unidade proposta;', sum(1 for i in bruto['itens'] if i['pertinencia']=='Imediato'), 'imediato')
