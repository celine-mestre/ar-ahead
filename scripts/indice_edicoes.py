"""Histórico semana a semana: reconstrói docs/edicoes/indice.json a partir das edições arquivadas
(docs/edicoes/nNN.json e, se existir, piloto.json). A página usa-o no seletor «Edições» do cabeçalho."""
import json, pathlib
pasta = pathlib.Path('docs/edicoes'); ix = []
for f in sorted(pasta.glob('*.json')):
    if f.name == 'indice.json': continue
    try: e = json.loads(f.read_text(encoding='utf-8'))['edicao']
    except Exception: continue
    html = f.with_suffix('.html')
    if html.exists():
        ix.append({'numero': e.get('numero', 0), 'semana': e.get('semana', ''), 'inicio': e.get('inicio', ''), 'ficheiro': html.name})
ix.sort(key=lambda e: e['inicio'], reverse=True)
(pasta / 'indice.json').write_text(json.dumps(ix, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(ix), 'edições no histórico')
