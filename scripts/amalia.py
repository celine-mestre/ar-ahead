"""Acesso ao Amália — o mesmo esquema do Radar de Notícias (pesos abertos, llama-cpp, create_chat_completion).
O modelo é descarregado no fluxo do GitHub só quando há trabalho pendente (guarda leve)."""
import json, os, re
from llama_cpp import Llama

_MODELO = None
def modelo():
    global _MODELO
    if _MODELO is None:
        _MODELO = Llama(model_path=os.environ.get('AMALIA_GGUF', 'modelos/amalia.gguf'), n_ctx=8192, n_threads=os.cpu_count(), verbose=False)
    return _MODELO

def perguntar(sistema, utilizador, max_tokens=800):
    r = modelo().create_chat_completion(
        messages=[{'role': 'system', 'content': sistema}, {'role': 'user', 'content': utilizador}],
        temperature=0, max_tokens=max_tokens)
    return r['choices'][0]['message']['content']

def json_da_resposta(texto):
    """O Amália por vezes embrulha o JSON em texto ou em ```; extrai o primeiro objeto/lista válido."""
    m = re.search(r'(\{.*\}|\[.*\])', texto, re.S)
    return json.loads(m.group(1)) if m else None
