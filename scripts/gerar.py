"""Gera a página de cartões (HTML autónomo) a partir de dados/agenda.json e do modelo.
Uso: python scripts/gerar.py dados/agenda.json saida/ar-ahead.html
"""
import sys, pathlib, json
raiz = pathlib.Path(__file__).resolve().parent.parent
dados, destino = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
modelo = (raiz/'modelo'/'template_cartoes.html').read_text(encoding='utf-8')
logo = (raiz/'modelo'/'logo_sggov_b64.txt').read_text().strip()
d = json.loads(dados.read_text(encoding='utf-8'))          # valida o JSON
json_txt = json.dumps(d, ensure_ascii=False).replace('</script', '<\\/script')
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(modelo.replace('__LOGO__', logo).replace('__DATA__', json_txt), encoding='utf-8')
print('gerado', destino, f"{len(d['destaques'])} destaques, {len(d['agenda'])} matérias, {len(d['fichas'])} fichas")
