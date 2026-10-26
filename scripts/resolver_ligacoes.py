"""Ligações diretas às notícias. Cerca de metade das notícias do Radar chegam pelo Google Notícias, com um reencaminhamento
(news.google.com/rss/articles/…) em vez do endereço do jornal. Este passo converte-os no endereço direto, como o Radar faz,
para a página, a ficha e a exportação para Excel mostrarem a ligação do próprio jornal.

Método (o mesmo do Radar, mais o descodificador atual do Google):
  1. identificadores antigos: o endereço vem em claro dentro do identificador (base64);
  2. identificadores atuais: lê-se a página de reencaminhamento (assinatura e data) e pede-se ao Google o endereço;
  3. em último caso, segue-se o reencaminhamento e fica o endereço final.
O que não resolver mantém a ligação do Google, que também abre o artigo.
Resultados guardados em dados/ligacoes.json (cache), para cada ligação ser resolvida uma só vez.
Uso: python scripts/resolver_ligacoes.py [--max N]  (N = novas resoluções por corrida; predefinição 1200)"""
import json, pathlib, re, sys, html, urllib.request, urllib.parse
from base64 import urlsafe_b64decode
from concurrent.futures import ThreadPoolExecutor

CACHE = pathlib.Path('dados/ligacoes.json')
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
# sem estes cookies o Google responde com a página de consentimento (consent.google.com) e nada se resolve
UA['Cookie'] = 'CONSENT=YES+cb.20240101-00-p0.pt+FX+000; SOCS=CAESHAgBEhJnd3NfMjAyNDAxMDEtMF9SQzIaAnB0IAEaBgiA_LyaBg'
UA['Accept-Language'] = 'pt-PT,pt;q=0.9,en;q=0.6'
MAX = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 1200

def plausivel(u):
    return bool(u) and u.startswith('http') and 'google.' not in u and 'gstatic' not in u and len(u) > 20

def do_identificador(lig):
    ident = lig.split('/articles/')[-1].split('?')[0]
    try:
        bruto = urlsafe_b64decode(ident + '=' * (-len(ident) % 4))
        for achado in re.findall(rb"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{20,}", bruto):
            c = achado.decode('utf-8', 'replace')
            if plausivel(c): return c
    except Exception: pass
    return None

def pelo_google(lig, tempo=12):
    """Descodificador atual: a página de reencaminhamento traz uma assinatura e uma data; com elas, o Google devolve o endereço."""
    ident = lig.split('/articles/')[-1].split('?')[0]
    pag = urllib.request.urlopen(urllib.request.Request(f'https://news.google.com/articles/{ident}', headers=UA), timeout=tempo).read().decode('utf-8', 'replace')
    sg = re.search(r'data-n-a-sg="([^"]+)"', pag); ts = re.search(r'data-n-a-ts="([^"]+)"', pag)
    if not sg and len(AMOSTRA) < 2: AMOSTRA.append(re.sub(r'\s+', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', pag, flags=re.S))[:400])
    if not sg or not ts:
        for p in (r'data-n-au="([^"]+)"', r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"'):
            m = re.search(p, pag, re.I)
            if m and plausivel(html.unescape(m.group(1))): return html.unescape(m.group(1))
        return None
    # pedido no formato que o próprio Google usa (o mesmo do pacote googlenewsdecoder)
    art = ["Fbv4je", f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{ident}",{ts.group(1)},"{sg.group(1)}"]']
    dados = ('f.req=' + urllib.parse.quote(json.dumps([[art]]))).encode()
    r = urllib.request.urlopen(urllib.request.Request('https://news.google.com/_/DotsSplashUi/data/batchexecute', data=dados,
        headers={**UA, 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'}), timeout=tempo)
    txt = r.read().decode('utf-8', 'replace')
    try:
        bloco = json.loads(txt.split('\n\n')[1])[:-2]
        u = json.loads(bloco[0][2])[1]
        if plausivel(u): return u
    except Exception:
        if len(AMOSTRA) < 3: AMOSTRA.append('batchexecute: ' + re.sub(r'\s+', ' ', txt)[:300])
    return None

def seguindo(lig, tempo=12):
    r = urllib.request.urlopen(urllib.request.Request(lig, headers=UA), timeout=tempo)
    fim = r.geturl()
    if plausivel(fim): return fim
    corpo = r.read(60000).decode('utf-8', 'replace')
    for p in (r'data-n-au="([^"]+)"', r'<meta[^>]+http-equiv="refresh"[^>]+url=([^">]+)', r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"'):
        for achado in re.findall(p, corpo, re.I):
            c = html.unescape(achado).strip()
            if plausivel(c): return c
    return None

AMOSTRA = []
DIAG = []   # diagnóstico das primeiras tentativas (gravado em dados/ligacoes_diag.json)
def resolver(lig):
    if not lig or 'news.google.' not in lig: return lig
    notas = {}
    for f in (do_identificador, pelo_google, seguindo):
        try:
            r = f(lig)
            if r: return r
            notas[f.__name__] = 'sem resultado'
        except Exception as e:
            notas[f.__name__] = f'{type(e).__name__}: {str(e)[:160]}'
    if len(DIAG) < 8: DIAG.append({'ligacao': lig[:120], **notas})
    return None   # não resolvida: fica a do Google (tenta-se outra vez noutra corrida)

def ligacoes_de(d):
    """Todas as ligações de notícias usadas na edição, por ordem de importância."""
    out = []
    for f in d.get('fichas', {}).values():
        out += [n.get('url') for n in f.get('fundo', [])]
    for x in d['destaques'] + d['agenda'] + d.get('futuro', []):
        c = x.get('cobertura') or {}
        out += [u.get('url') for u in c.get('ultimas', [])]
    for x in d['destaques'] + d['agenda'] + d.get('futuro', []):
        c = x.get('cobertura') or {}
        out += [n[3] for n in c.get('todas', []) if len(n) > 3]
    return list(dict.fromkeys(u for u in out if u and 'news.google.' in u))

if __name__ == '__main__':
    p = pathlib.Path('dados/agenda.json'); d = json.loads(p.read_text(encoding='utf-8'))
    cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}
    pend = [u for u in ligacoes_de(d) if u not in cache][:MAX]
    if pend:
        print(f'{len(pend)} ligações do Google Notícias por resolver…', flush=True)
        with ThreadPoolExecutor(max_workers=12) as piscina:
            for u, r in zip(pend, piscina.map(resolver, pend)):
                if r: cache[u] = r
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=0), encoding='utf-8')
        ok = sum(1 for u in pend if u in cache)
        print(f'{ok} resolvidas nesta corrida; {len(cache)} em cache')
        pathlib.Path('dados/ligacoes_diag.json').write_text(json.dumps({'tentadas': len(pend), 'resolvidas': ok, 'exemplos_falhados': DIAG, 'pagina_recebida': AMOSTRA}, ensure_ascii=False, indent=1), encoding='utf-8')
    # aplica a cache a toda a edição
    n = 0
    def troca(u):
        global n
        if u in cache: n += 1; return cache[u]
        return u
    for f in d.get('fichas', {}).values():
        for nt in f.get('fundo', []): nt['url'] = troca(nt.get('url'))
    for x in d['destaques'] + d['agenda'] + d.get('futuro', []):
        c = x.get('cobertura') or {}
        for u in c.get('ultimas', []): u['url'] = troca(u.get('url'))
        for nt in c.get('todas', []):
            if len(nt) > 3: nt[3] = troca(nt[3])
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{n} ligações substituídas pelo endereço do jornal')
