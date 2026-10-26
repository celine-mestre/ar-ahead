# AR Preview — a semana na Assembleia da República

Agenda parlamentar semanal para os dirigentes da Direção de Serviços de Suporte à Decisão (DSSD) da Secretaria-Geral do Governo, triada por unidade orgânica (DACDP, DAPL, UPE, DCIRI), com cobertura mediática e fichas de varrimento.

**Página:** https://celine-mestre.github.io/ar-ahead/ (endereço provisório, para desenvolvimento e testes; o repositório mantém por agora o nome `ar-ahead`)
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
7. scripts/gerar.py             modelo + dados + histórico   → saida/ar-preview.html
8. scripts/pdf.js               Chromium                      → saida/ar-preview.pdf
9. scripts/resolver_ligacoes.py ligações diretas às notícias (reencaminhamentos do Google Notícias → endereço do jornal; cache em dados/ligacoes.json)
10. scripts/indice_edicoes.py   lista de edições              → docs/edicoes/indice.json
   scripts/email_resumo.py      corpo do email de segunda-feira
```

Tudo corre em `.github/workflows/ar-preview.yml`.

---

## Fonte dos dados

- **Principal: https://agenda.parlamento.pt** — a exportação JSON do próprio site da Agenda Parlamentar (a mesma do botão «Exportar › Para JSON»). É a versão mais atual: a 26/10/2026, o ficheiro dos dados abertos ainda não tinha três reuniões que o site já mostrava (COFAP de 27/10 às 11h00, Grupo de Trabalho para os Assuntos Culturais de 28/10 e o Parlamento dos Jovens remarcado para 29/10 às 9h30).
- **Recurso: dados abertos** (https://www.parlamento.pt/Cidadania/Paginas/DABoletimInformativo.aspx › Agenda Parlamentar › XVII Legislatura › `AgendaParlamentar_json.txt`), usados se o site da agenda não responder. A «Resumo da Calendarização» dos meses seguintes vem sempre daqui.
- O registo de cada recolha (`dados/agenda_bruta.json`, campo `fonte`) diz qual das duas foi usada.

Secções lidas: Plenário, Comissões Parlamentares, Grupo de Trabalho, Grupo de Trabalho AR, Conferência de Líderes e Comissão Permanente. Ficam de fora as audiências dos grupos parlamentares, as visitas, as assistências e o Conselho de Administração.

---

## A página

- **Edição em curso:** calendário mensal, agenda hora a hora e hemiciclo; ao clicar numa matéria abre-se o cartão na gaveta lateral, com a classificação, a cobertura e a lista de notícias (exportável para Excel e imprimível). Os cartões completos ficam ocultos por defeito e mostram-se com um botão; o PDF inclui-os sempre.
- **Seletor «Semanas»**, por cima do calendário:
  - edições anteriores, a cinzento, com ligação para a edição completa;
  - a semana em curso;
  - as semanas seguintes já publicadas pela AR, a verde, ainda sem triagem completa nem varrimento.
- **«Mais à frente»:** reuniões futuras e calendarização da AR.
- **Histórico:** cada edição fica em `docs/edicoes/nNN.html` e `.json`. A n.º 1 é a edição piloto (19 a 25 de outubro de 2026), a n.º 2 a primeira automática. O seletor de semanas lê esse arquivo.
- **Modelo e dados separados:** `modelo/template_cartoes.html` não tem conteúdo, só desenha o `dados/agenda.json`. Para mudar o aspeto, muda-se o modelo; para mudar o conteúdo, muda-se o JSON.

---

## Quem decide «Imediato», «Vigilância» e «Registo»

Por esta ordem, e cada passo prevalece sobre o anterior:

1. **Regras (`dados/regras_uo.json`)** — listas de termos por unidade (DACDP, DAPL, UPE, DCIRI), validadas pelos dirigentes. Um termo da lista `termos` dá **Vigilância** e atribui a unidade; um termo da lista `imediato` dá **Imediato**, mas só quando aparece no assunto principal (o tema, ou toda a ordem do dia no Plenário). Os termos `transversal` marcam a matéria para todas as unidades. A lista `governo` (audições de ministros, comissões de inquérito, interpelações) dá pelo menos Vigilância e DACDP. Sem nenhum termo, fica **Registo**.
2. **Amália** (quando ativo) — só para as matérias que as regras deixaram sem unidade: propõe unidade, pertinência, assunto e expressões de pesquisa, com uma justificação.
3. **Revisão humana (`dados/correcoes.csv`)** — prevalece sempre e marca a matéria como validada.

Cada cartão mostra a linha «Classificação: …» com o termo ou a justificação que decidiu, para a revisão perceber o porquê e corrigir a regra, não só o caso.

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

A agenda vem exclusivamente da Assembleia da República: não se acrescentam matérias à mão (prazos ou lembretes que não constem da agenda da AR ficam de fora).

---

## Varrimento mediático (automático) e Amália

**As notícias vêm sempre e só do Radar de Notícias por área governativa** (`upe-sggov/radar-noticias`): nunca de pesquisa manual nem da memória do modelo. Fichas feitas à mão são retiradas e substituídas pela versão automática. As únicas ligações mantidas nos cartões são as da Assembleia da República.

- **Contagem e lista completa (sem IA):** `cobertura.py` procura, para cada matéria, as notícias dos últimos 60 dias pelas expressões de pesquisa (definidas na revisão, pelo Amália, ou reconhecidas automaticamente para matérias recorrentes como o Orçamento do Estado e a Conta Geral do Estado) e guarda a contagem, a tendência de 7 dias e a lista (até 400, as mais recentes).
- **Fichas (`amalia_varrimento.py`):**
  - «Imediato»: ficha completa com até 20 notícias. «Vigilância»: ficha curta com até 8, que passa a completa quando a cobertura está a subir. As matérias «Imediato» das semanas seguintes também têm ficha com antecedência.
  - A seleção é feita ao longo dos 60 dias: cerca de 40 % da última semana e o resto repartido pelas semanas anteriores na proporção da cobertura, com preferência pelo assunto no título e pela variedade de órgãos e de dias.
  - **Sem o Amália** (sem o segredo `AMALIA_GGUF_URL`): a ficha mostra só a seleção de notícias (data, órgão, título, ligação), sem análise.
  - **Com o Amália:** a mesma seleção, com enquadramento, síntese, natureza e impacto de cada notícia; as fichas sem análise são completadas automaticamente.
  - As fichas são refeitas até à segunda-feira da semana da matéria quando há notícias novas, quando passam de curta a completa e quando uma ficha sem notícias passa a ter notícias. A mesma matéria em vários dias (por exemplo, duas sessões do mesmo debate) partilha a ficha.
  - `python scripts/amalia_varrimento.py --verificar` diz o que há para fazer, sem carregar o modelo.
- **Triagem:** `amalia_triagem.py` propõe unidade, pertinência, assunto e expressões de pesquisa só para o que as regras não decidiram, usando as competências em `dados/competencias_dssd.json`.
- **Revisão:** as fichas do Amália não incluem a verificação de números, que fica para revisão humana. Para marcar uma ficha como revista (e impedir que seja reescrita), acrescenta-se `"revista_por": "nome"` à ficha em `dados/agenda.json`; a página passa a mostrar as notícias novas desde a revisão.

---

## Segredos do repositório

Criam-se em Settings › Secrets and variables › Actions › New repository secret.

| Nome | Valor |
|---|---|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | endereço remetente |
| `SMTP_PASS` | palavra-passe de aplicação do Google (16 letras, sem espaços) |
| `SMTP_FROM` | `AR Preview <endereço remetente>` |
| `DIRIGENTES_DSSD` | destinatários do email de segunda-feira, separados por vírgulas |
| `EMAIL_TRIAGEM` | destinatário do aviso de semana nova |
| `AMALIA_GGUF_URL` | opcional: endereço do modelo Amália |

Sem os segredos SMTP, os emails não são enviados e o registo do workflow mostra o texto que seria enviado.

---

## Correr à mão

Actions › AR Preview › Run workflow, com o passo `atualizar` (recolha e publicação) ou `enviar` (email aos dirigentes).

---

## Notas

- O repositório é **público**. A página tem `noindex`, para não aparecer nos motores de pesquisa, mas abre para qualquer pessoa com o endereço, e todo o conteúdo do repositório (dados, regras, histórico) é legível.
- A atribuição às unidades e o varrimento são indicativos e estão sujeitos a validação. O varrimento é amostral e não exaustivo.
- O email usa o logótipo publicado em `docs/logo-sggov.png`: os programas de email não mostram imagens embebidas no próprio HTML.
- `scripts/importar_html_antigo.py` converteu a edição piloto (HTML original) para JSON.
