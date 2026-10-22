# AR Ahead — a semana na Assembleia da República

Agenda parlamentar semanal para os dirigentes da Direção de Serviços de Suporte à Decisão (DSSD) da Secretaria-Geral do Governo, triada por unidade orgânica (DACDP, DAPL, UPE, DCIRI), com cobertura mediática e fichas de varrimento.

**Página:** https://celine-mestre.github.io/ar-ahead/ (endereço provisório, para desenvolvimento e testes)
**Responsável:** Unidade de Pesquisa e Estatísticas (UPE)

---

## O que acontece sozinho

| Quando (hora de Lisboa) | O quê |
|---|---|
| Todos os dias, 7h07 e 18h07 | Recolhe a agenda da AR, atualiza a edição da semana, marca o que é novo, alterado ou retirado, refaz a página e o PDF |
| Segunda-feira, 9h07 | Envia aos dirigentes o resumo por unidade, com o logótipo da SGGov, o PDF em anexo, a ligação para a página e, em cada matéria, a ligação para a AR e para o varrimento |
| Quando começa uma semana nova | Arquiva a edição anterior e avisa a pessoa da triagem com a lista de matérias a rever |

**Semana-alvo:** de segunda a quinta, a semana em curso; de sexta a domingo, a semana seguinte.

Os horários estão em UTC no workflow. No horário de verão (de março a outubro), subtrai-se 1 às horas dos três `cron`.

---

## Cadeia

```
1. scripts/recolher_agenda.py   dados abertos da AR          → dados/agenda_bruta.json
2. scripts/triar.py             regras (dados/regras_uo.json) → dados/triagem_proposta.json
3. scripts/montar_edicao.py     edição nova ou atualização    → dados/agenda.json
4. scripts/amalia_triagem.py    Amália: unidade e assunto das matérias novas sem unidade
5. scripts/cobertura.py         notícias do Radar de Notícias (60 dias, OCS nacionais) para todas as matérias
6. scripts/amalia_varrimento.py Amália: fichas completas («Imediato») e curtas («Vigilância»)
7. scripts/gerar.py             modelo + dados + histórico   → saida/ar-ahead.html
8. scripts/pdf.js               Chromium                      → saida/ar-ahead.pdf
9. scripts/indice_edicoes.py    lista de edições              → docs/edicoes/indice.json
   scripts/email_resumo.py      corpo do email de segunda-feira
```

Tudo corre em `.github/workflows/ar-ahead.yml`.

---

## Fonte dos dados

Dados abertos da Assembleia da República, Agenda Parlamentar (XVII Legislatura), em formato JSON:

- Página de origem: https://www.parlamento.pt/Cidadania/Paginas/DABoletimInformativo.aspx
- Ficheiro: `AgendaParlamentar_json.txt`. O endereço completo está em `scripts/recolher_agenda.py`.

Secções lidas: Plenário, Comissões Parlamentares, Grupos de Trabalho, Conferência de Líderes e Comissão Permanente, e ainda a «Resumo da Calendarização». A AR publica uma janela que vai mais ou menos de ontem a dois meses à frente.

---

## A página

- **Edição em curso:** cartões por matéria, filtros por unidade e pertinência, calendário mensal e agenda hora a hora.
- **Seletor «Semanas»**, por cima do calendário:
  - edições anteriores, a cinzento, com ligação para a edição completa;
  - a semana em curso;
  - as semanas seguintes já publicadas pela AR, a verde, ainda sem triagem completa nem varrimento.
- **«Mais à frente»:** reuniões futuras e calendarização da AR.
- **Histórico:** cada edição fica em `docs/edicoes/nNN.html` (a piloto, de 19 a 25 de outubro de 2026, em `piloto.html`). O menu «Edições» do cabeçalho e o seletor de semanas leem esse arquivo.
- **Modelo e dados separados:** `modelo/template_cartoes.html` não tem conteúdo, só desenha o `dados/agenda.json`. Para mudar o aspeto, muda-se o modelo; para mudar o conteúdo, muda-se o JSON.

---

## Revisão humana

Para corrigir a classificação de uma matéria, acrescenta-se uma linha a `dados/correcoes.csv`:

```
chave;uo;pertinencia;assunto;expressoes
ar-123456;DCIRI|UPE;Vigilância;Conselho das Comunidades Portuguesas;Conselho das Comunidades|CCP
```

- A `chave` aparece em `dados/triagem_semana.csv`.
- As unidades separam-se com `,` ou `|`; as expressões de pesquisa com `|`.
- A correção prevalece em todas as atualizações seguintes e a matéria fica marcada como validada; o Amália nunca a altera.
- Também se aplica às matérias das semanas seguintes (por exemplo, para marcar já como «Imediato» uma grande matéria de novembro).
- As expressões de pesquisa tornam a contagem de notícias precisa.

Matérias acrescentadas à mão (por exemplo, prazos de pareceres) têm `"manual": true` e nunca são retiradas automaticamente.

---

## Amália

Usa o mesmo esquema do Radar de Notícias: pesos abertos, `llama-cpp`, a correr no próprio workflow.

- **Triagem:** `amalia_triagem.py` propõe unidade, pertinência, assunto e expressões de pesquisa só para o que as regras não decidiram. Usa como critério as competências descritas em `dados/competencias_dssd.json`.
- **Varrimento:** `amalia_varrimento.py` escreve as fichas apenas a partir de notícias reais do Radar de Notícias, nunca da memória do modelo. Cada notícia tem data, fonte e ligação.
  - «Imediato»: ficha completa com até 20 notícias analisadas. «Vigilância»: ficha curta com até 8, que passa a completa quando a cobertura está a subir.
  - A amostra é escolhida ao longo dos 60 dias: cerca de 40 % da última semana e o resto repartido pelas semanas anteriores na proporção da cobertura, com preferência pelo assunto no título e pela variedade de órgãos e de dias.
  - As fichas são refeitas até à segunda-feira da semana da matéria quando há notícias novas, quando passam de curta a completa e quando uma ficha sem notícias passa a ter notícias.
  - As fichas revistas por pessoas nunca são reescritas; a página mostra quantas notícias saíram desde a revisão.
  - As matérias «Imediato» das semanas seguintes já publicadas pela AR também têm ficha com antecedência, que passa para a edição quando a semana chega.
  - `python scripts/amalia_varrimento.py --verificar` diz o que há para fazer, sem carregar o modelo.
- **Lista completa, sem IA:** `cobertura.py` guarda, para cada matéria, todas as notícias encontradas (até 400, as mais recentes), que a página mostra em «Notícias» e no fim de cada ficha.
- **Revisão:** as fichas geradas pelo Amália não incluem a verificação de números, que fica para revisão humana. Para marcar uma ficha como revista, muda-se `gerado_por` em `dados/agenda.json` para o nome de quem reviu.

Sem o segredo `AMALIA_GGUF_URL`, os passos do Amália saltam e a página publica-se na mesma, com a contagem e a lista completa.

---

## Segredos do repositório

Criam-se em Settings › Secrets and variables › Actions › New repository secret.

| Nome | Valor |
|---|---|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | endereço remetente |
| `SMTP_PASS` | palavra-passe de aplicação do Google (16 letras, sem espaços) |
| `SMTP_FROM` | `AR Ahead <endereço remetente>` |
| `DIRIGENTES_DSSD` | destinatários do email de segunda-feira, separados por vírgulas |
| `EMAIL_TRIAGEM` | destinatário do aviso de semana nova |
| `AMALIA_GGUF_URL` | opcional: endereço do modelo Amália |

Sem os segredos SMTP, os emails não são enviados e o registo do workflow mostra o texto que seria enviado.

---

## Correr à mão

Actions › AR Ahead › Run workflow, com o passo `atualizar` (recolha e publicação) ou `enviar` (email aos dirigentes).

---

## Notas

- O repositório é **público**. A página tem `noindex`, para não aparecer nos motores de pesquisa, mas abre para qualquer pessoa com o endereço, e todo o conteúdo do repositório (dados, regras, histórico) é legível.
- A atribuição às unidades e o varrimento são indicativos e estão sujeitos a validação. O varrimento é amostral e não exaustivo.
- O email usa o logótipo publicado em `docs/logo-sggov.png`: os programas de email não mostram imagens embebidas no próprio HTML.
- `scripts/importar_html_antigo.py` converteu a edição piloto (HTML original) para JSON.
