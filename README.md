# AR Ahead — a semana na Assembleia da República · kit de automatização

Cadeia: **recolha (sexta 12h)** → **triagem proposta + validação humana** → **varrimento (IA + revisão)** → **publicação (segunda 9h)**.

```
dados/agenda_bruta.json        ← scripts/recolher_agenda.py (dados abertos da AR; URL a confirmar)
dados/triagem_proposta.json    ← scripts/triar.py (regras em dados/regras_uo.json) → Ana Luísa valida
dados/agenda.json              ← após varrimento: fichas em "fichas", destaques em "destaques"
saida/ar-ahead.html           ← scripts/gerar.py (modelo/template_cartoes.html + logótipo)
saida/ar-ahead.pdf            ← scripts/pdf.js (Chromium)
saida/email.html               ← scripts/email_resumo.py (resumo por unidade para o corpo do email)
```

* O modelo não contém conteúdo: só desenha o `agenda.json`. Para corrigir o aspeto, muda-se o modelo; para publicar uma semana, muda-se o JSON.
* `scripts/importar_html_antigo.py` converte a 1.ª edição (HTML da Ana Luísa) para `agenda.json` — foi assim que este `dados/agenda.json` nasceu.
* O repositório deve ser **privado** (a atribuição às unidades é um juízo interno). Numa organização gratuita no GitHub, os repositórios privados têm 2 000 minutos/mês de Actions; esta cadeia gasta ~5 minutos por semana.
* Segredos a criar no repositório: `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `EMAIL_TRIAGEM`, `DIRIGENTES_DSSD` (mesmo esquema do Radar de Notícias).
* **Amália** (mesmo esquema do Radar: pesos abertos, `llama-cpp`, corre no próprio fluxo): `scripts/amalia_triagem.py` atribui unidade e pertinência ao que as regras não decidiram e reescreve o tema como ASSUNTO; `scripts/amalia_varrimento.py` gera as fichas dos «Imediato» a partir do corpus do Radar de Notícias (nunca da memória do modelo) — cada notícia com data, fonte e ligação reais. Os «Pontos de atenção» ficam para a revisão humana. Segredo adicional: `AMALIA_GGUF_URL`. As competências que o Amália lê estão em `dados/competencias_dssd.json`.
