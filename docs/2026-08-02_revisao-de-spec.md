# Revisao de spec -- avatar do personagem, version 11 (blocos @10 e @11)

Data: 2026-08-02. Papel: revisor de spec, nomeado pelo dono. Conflito declarado:
o mesmo agente atuou como PO nesta sessao e assinou o parecer que originou o
@10 (`docs/2026-08-02_PO-direcoes-e-entrega.md`); os blocos derivados desse
parecer foram auditados com o mesmo rigor dos demais, e um deles leva correcao.

Metodo: todo numero dos blocos revisados foi conferido contra
`docs/2026-08-02_PESQUISA-transplante.md`, `docs/2026-08-02_pesquisa-ataque.md`,
`docs/2026-08-02_calibracao-do-roteador.md`,
`docs/2026-08-02_roteador-parametros.json` e
`docs/2026-08-02_acervo-no-github-pages.md`; o codigo (`roteador.py`,
`preencher.py`, `testes/test_roteador.py`) foi lido inteiro; as alegacoes
"medido ao aplicar" da decisao 2a foram REMEDIDAS agora, nao aceitas de
memoria: `waybuilder.vercel.app/avatar/catalogo.json` responde **404** e
`igoresramos.github.io/waybuilder-avatar/saida/catalogo.json` responde **200**;
o `buildCommand` do `vercel.json` tem so `sincronizar-base.sh`;
`app/public/avatar/` esta gitignored; o `vite.config.ts` ja tem o matcher por
origem + prefixo `/waybuilder-avatar/saida/` e o `Avatar.tsx` ja tem
`crossOrigin = "anonymous"` antes do `src`, `RAIZ` no Pages e `?v=` de versao.

---

## Vereditos

| bloco | veredito | motivo em uma linha |
|---|---|---|
| frontmatter (`version: 11`, @10, @11) | **APROVADO** | fiel ao parecer e a calibracao; o salto 7->10 e explicado e o corpo confirma (ha blocos @9); o "~14%" bate com os 14,5% medidos (ver opcional 1) |
| decisao 2a (acervo no Pages) | **APROVADO** | cada numero confere com o doc do Pages, e as provas (404/200, vercel.json, gitignore, matcher, crossOrigin, ?v=, 90 dias) foram reverificadas ao vivo nesta revisao |
| decisao 3b3, bloco @10 (4 direcoes) | **APROVADO** | 118,0 MB / amostra de 44 pecas / folga ~8,5x sobre 1 GB conferem com o @9 e com o doc do Pages; a projecao e declarada como projecao e o peso real fica prometido ao relatorio de (3h) |
| decisao 4, bloco @10 (reconciliacao) | **APROVADO COM CORRECAO** | a reconciliacao e correta na substancia (confirmada no `vite.config.ts`), mas o texto normativo antigo da propria decisao segue vivo e a contradiz (correcao 6) |
| Aberto item 2 (fechado) | **APROVADO** | fecho fiel ao parecer; 8b intacta (saida/ versionada, ~30,6 MB) e 6 intacta (pin no catalogo); o texto original preservado como registro |
| decisao 11b (roteador por rigidez) | **REPROVADO** | os numeros do texto conferem com as fontes, mas o codigo nao implementa a regra calibrada: `preencher.py` deixa peca legada votar no treino, e a garantia de zero regressao foi medida SEM isso (correcao 1) -- e a divergencia mais cara do documento |
| decisao 11c (veredito por animacao) | **APROVADO COM CORRECAO** | a tabela confere fonte a fonte, exceto o "0,5%" atribuido ao artefato dos quadros vazios -- o numero provado como artefato e o 3,6% (correcao 2); e o fecho do item 145 nao registra que os vereditos valem so de frente (correcao 5) |

---

## Correcoes exigidas

### 1. [11b + `preencher.py`] O treino do roteador nao restringe a pecas completas -- o codigo nao cumpre a regra calibrada

- **Onde:** `preencher.py`, `treino_do_slot` (linhas 128-167); spec, decisao 11b.
- **O que esta escrito/implementado:** o filtro de referencia e
  `{"walk", "idle"} <= animacoes(vo)` -- basta ter `walk` e `idle`. Com isso,
  as 76 pecas LEGADAS que ja tem `idle` entram no pool de treino das outras
  pecas do slot. A docstring diz "Referencia e a peca que tem walk E idle". A
  spec 11b apresenta os limiares como "medido" sem definir a populacao de
  treino.
- **O que deveria estar:** referencia = peca **nao-legada, completa nas 5
  animacoes do recorte** (ou `taxonomia.pecas[id].legado == false`). E a spec
  11b deve declarar essa definicao explicitamente, porque e ela que sustenta os
  numeros da tabela.
- **Fonte que prova:** `docs/2026-08-02_roteador-parametros.json`, campo
  `regra`: *"se o slot tem >= n_min pecas de treino NAO-LEGADAS (completas nas
  5 animacoes)"*. `docs/2026-08-02_calibracao-do-roteador.md`: *"nao usei
  nenhuma peca legada como treino de outra"* -- e, decisivo, a calibracao
  atribui o ZERO regressao exatamente a essa restricao: *"Isso e diferente do
  que a pesquisa original mediu (13 regressoes em 428, 2 delas destruindo peca
  exata) porque la o treino vinha de **qualquer** peca do slot, legada ou
  nao."* O caso `hat/tiara`/`hat/formal-bowler-hat` (arte exata destruida) e
  citado como "com treino contaminado por pecas legadas".
- **Consequencia se nao corrigir:** os 14,5% de exatos e as 0 regressoes que a
  spec cita nao descrevem o que o build faz. Um slot com 1 completa + 1 legada-
  com-idle atinge `n_min=2` e translada onde a regra calibrada mandaria nao
  mexer. O mecanismo de regressao que a calibracao declarou "teoricamente
  possivel e nao observado" volta a ser possivel na pratica, pelo caminho ja
  observado uma vez.
- **Custo do fix:** uma condicao a mais no filtro de `treino_do_slot` (exigir o
  conjunto completo de animacoes do recorte, ou consultar a taxonomia) + uma
  frase na 11b. O `test_roteador.py` trava os limiares mas nao trava a
  populacao de treino -- vale um teste tambem.

### 2. [11c] O "0,5%" nao e o numero que foi provado artefato -- e o 3,6%

- **Onde:** decisao 11c, paragrafo do `sit`; mesmo erro no comentario
  `NAO_GERAR` de `preencher.py` (linhas 41-46).
- **O que esta escrito:** *"O 0,5% de 'exatos' que o transplante mostrava era
  artefato de medicao -- quadros VAZIOS contando como acerto, em 13 pecas cuja
  `camadas[0]` e vazia (...). Corrigido isso, cai para 0,0%."*
- **O que deveria estar:** o numero decomposto e corrigido pelo ataque foi o
  **3,6% da H2 (n=366)**: 13 dos 13 frames exatos eram quadros vazios, e
  corrigido cai a 0,0%. O 0,5% e o baseline de transplante da amostra H1-sit
  (**n=374**), que nunca foi decomposto -- afirmar que "era quadros vazios" e
  atribuir ao 0,5% uma prova que foi feita sobre o 3,6%.
- **Fonte que prova:** `docs/2026-08-02_pesquisa-ataque.md`, Ataque 1b (tabela:
  sit 3,6% -> 0,0%; *"13 dos 13 frames exatos eram quadros vazios"*);
  `docs/2026-08-02_PESQUISA-transplante.md`, tabela de hipoteses (H1-sit:
  baseline 0,5% / n=374) e secao 4.2.
- A conclusao (`sit` nunca gerar, 0,0% em n=349 e n=366) esta certa e bem
  citada -- so a genealogia do numero esta trocada.

### 3. [11b] "origem: medido" esconde que o par (2, 0,70) e desempate por julgamento

- **Onde:** tabela da 11b (colunas "valor"/"origem") e o comentario de
  `roteador.py` ("Medidos, nao arbitrados").
- **O que esta escrito:** os dois limiares com origem "medido", sem
  qualificacao.
- **O que deveria estar:** o que a varredura mediu foi que `frac >= 0,80` e
  `n_min >= 3` PERDEM (o chute e estritamente dominado: 10,5% contra 14,5%).
  Mas o par (2, 0,70) esta num **empate de 6 combinacoes** com resultado
  identico -- `(1;0,50)` a `(2;0,70)` -- e `n_min=2` foi escolhido dentro do
  empate por robustez, que a propria calibracao rotula: *"e uma preferencia de
  robustez (...), nao um resultado medido; sinalizo explicitamente que e
  opiniao, nao dado"*. A spec deve registrar o empate; senao, uma recalibracao
  futura que der `(1;0,50)` identico vai parecer contradizer a spec sem
  contradizer nada.
- **Fonte que prova:** `docs/2026-08-02_calibracao-do-roteador.md`, secao
  "Recomendacao"; `docs/2026-08-02_roteador-parametros.json`,
  `empate_medido_com_recomendado` e `nota_empate`.

### 4. [11b] "pesquisa de doze frentes" -- o numero nao existe em fonte nenhuma

- **Onde:** primeiro paragrafo da 11b.
- **O que esta escrito:** "Uma pesquisa de doze frentes com passe adversarial".
- **O que deveria estar:** a pesquisa declara **10 frentes** no proprio
  cabecalho ("3 de fundamentos, 5 de hipotese, 1 de ataque adversarial, 1 de
  juizo visual"); o indice lista 11 relatorios (com a frente combinada).
  "Doze" nao bate com nenhuma das duas contagens. Usar "dez" (o cabecalho da
  fonte) ou "onze" (o indice), nao doze.
- **Fonte que prova:** `docs/2026-08-02_PESQUISA-transplante.md`, linhas 5 e
  224-238.

### 5. [11c + 3b3] O item 145 fecha "por animacao" com numeros medidos SO de frente -- e o @10 acabou de ligar 4 direcoes

- **Onde:** decisao 11c ("Fecha o item 145 -- o veredito por animacao, com
  numero") e o cruzamento com 3b3 @10.
- **O que esta escrito:** nada sobre direcao; a ressalva final da 11c cobre
  legadas vs completas, nao frontal vs perfil/costas.
- **O que deveria estar:** todos os numeros de 11b/11c foram medidos no recorte
  frontal ("Limites gerais. Tudo medido no recorte frontal" -- pesquisa, secao
  2). O proprio parecer do PO que originou o @10 fixou o gatilho: *"o veredito
  do item 145 passa a valer POR DIRECAO, nao por animacao agregada"* (secao 5).
  A spec incorporou a decisao das 4 direcoes mas nao incorporou essa condicao
  -- quem ler a 11c daqui a seis meses vai achar que o veredito cobre as 4
  linhas que o build emite. Registrar na 11c: vereditos valem para a direcao de
  frente; com as 4 direcoes, revalidar por direcao antes de estender.
- **Fonte que prova:** `docs/2026-08-02_PO-direcoes-e-entrega.md`, secao 5,
  ultimo bullet; `docs/2026-08-02_PESQUISA-transplante.md`, secao 2.

### 6. [decisao 4] O texto normativo antigo contradiz o proprio adendo @10

- **Onde:** decisao 4 -- titulo e o paragrafo "Se o acervo recortado nao
  couber, a saida **nao** e runtime cache".
- **O que esta escrito:** o titulo segue "O acervo cabe no precache" e o
  paragrafo segue proibindo runtime cache -- sendo que o @10 logo abaixo
  registra que o acervo E runtime cache `CacheFirst` por decisao do dono, e a
  2a constroi em cima disso. A frase do adendo, "O paragrafo acima segue
  valendo para o nucleo, nao para o acervo", aponta para um paragrafo que so
  fala do acervo: se ele nao vale para o acervo, nao vale para nada.
- **O que deveria estar:** marcar titulo e paragrafo como superados em @10 (ou
  reescrever o titulo para o que a decisao passou a ser: "o NUCLEO cabe no
  precache; o acervo e runtime cache com garantia 'offline apos a primeira
  visita'"), deixando o texto antigo explicitamente historico, como o Aberto 2
  ja faz.
- **Fonte que prova:** `app/vite.config.ts` (runtime cache `CacheFirst`,
  cacheName `avatar`, 90 dias -- confirmado nesta revisao) e o proprio adendo
  @10 da decisao 4.

### 7. [11b/11c] `idle` sem `walk` continua no transplante -- e a spec diz que o idle "sai do transplante" sem excecao

- **Onde:** frontmatter @11 e 11b ("o `idle` sai do transplante"); codigo em
  `preencher.py:206` (`if falta == "idle" and "walk" in tem`).
- **O que esta escrito/implementado:** o roteador so age quando a peca TEM
  `walk` (e a base da copia e da translacao). Peca sem `walk` cai no ramo do
  transplante tambem para `idle` -- o codigo esta certo (nao ha base para
  copiar), mas a spec promete uma saida sem registrar a excecao.
- **O que deveria estar:** uma linha na 11b: peca sem `walk` nao tem base para
  o roteador e permanece no transplante da decisao 11 (a contagem canonica
  registra 135 celulas sem `walk`).
- **Fonte que prova:** `preencher.py:206`;
  `docs/2026-08-02_calibracao-do-roteador.md`, Tarefa 2 (135 celulas de walk).

### 8. [11c] A conclusao sobrevivente da H2 sobre pernas/pes em `combat_idle`/`run` nao foi adotada nem registrada

- **Onde:** decisao 11c, linhas de `combat_idle` e `run` ("transplante, como
  esta").
- **O que esta escrito:** nada sobre pernas e pes.
- **O que deveria estar:** o ataque preservou explicitamente a conclusao
  qualitativa da H2 -- *"cortar pernas/pes em combat_idle e run"* -- e a
  recomendacao 6 da pesquisa mediu **0,0% de exatos nas 4 celulas** (mediana
  10-38 px, fracao de area errada 37,5% a 90,2%) para peca com pixel em pernas
  ou pes nessas animacoes. Nem o codigo implementa o corte, nem a spec registra
  que ele foi deliberadamente deixado de fora. Como a 11c se apresenta como "o
  veredito por animacao", a omissao vai virar susto: adotar o corte, ou
  registrar por que nao.
- **Fonte que prova:** `docs/2026-08-02_pesquisa-ataque.md`, Ataque 1b ("A
  conclusao qualitativa da H2 (cortar sit, cortar pernas/pes em combat_idle e
  run) sobrevive"); `docs/2026-08-02_PESQUISA-transplante.md`, recomendacao 6.

---

## O que eu mudaria de redacao (opcional)

1. **"~14% em alvo legado real"** (frontmatter @11 e 11b): o numero-fonte e
   14,5% (roteador calibrado, male, n=76); o agregado nos 6 corpos e **11,0%**
   (n=392, amostras correlacionadas). Citar "14,5% no male; 11,0% agregado nos
   6 corpos" fecha a porta para leitura otimista sem alongar o texto. O "~14%"
   nao e desonesto -- e so menos preciso do que a fonte permite.
2. **"em 61 das 76 pecas legadas medidas [nao mexer] foi a decisao certa"**
   (11b, e repetido nas docstrings de `roteador.py` e `test_roteador.py`): o
   que foi medido e que o roteador DECIDIU nao mexer em 61 e que isso produziu
   zero regressao; a otimalidade por peca nao foi verificada (exigiria o
   oraculo). "Em 61 das 76 o roteador nao toca a peca, com zero regressao
   medida" e o que os dados sustentam.
3. **O 28,2% sem denominador** (11b): dizer "28,2% das 2.864 lacunas
   canonicas" e apontar a reconciliacao da calibracao (Tarefa 2) -- e ela que
   enterra o 3.666 como numero de entrega; hoje a spec depende de o leitor
   achar essa genealogia sozinho.
4. **Decisao 11** ganharia um ponteiro no proprio titulo ou primeiro paragrafo
   ("escopo reduzido por 11b/11c") -- hoje o leitor que para na 11 sai com "o
   transplante gera tudo".
5. **`COPIA_DIRETA` em `preencher.py:57` e constante morta**: o comportamento
   esta inline no ramo do idle. Nao e defeito de spec; e dead code que vai
   confundir manutencao. Mencionado, nao removido (mudanca cirurgica).
6. **Deduplicacao por bytes do `walk` k=0 apenas** (`preencher.py:158`): o
   ataque identificou duplicatas pelo hash do PAR (walk k0, idle k1). Duas
   pecas com o mesmo walk k0 e idle k1 DIFERENTES seriam colapsadas e um voto
   legitimo (possivelmente discordante) descartado -- vies pro lado do
   "concorda". Caso raro, mas vale igualar o criterio ao do ataque.
7. **`test_roteador.py:155`**: "36 dos 50 slots legados" -- o 36 tem fonte
   (pesquisa, secao 7), o 50 nao consta em nenhum dos documentos. Conferir ou
   remover o denominador.
8. **Gate de aceite (recomendacao 7 da pesquisa)**: os tres sinais de fila
   humana nao foram adotados. Coerente com a decisao 11 (defeito assumido pelo
   dono), mas uma linha registrando a nao-adocao deliberada evitaria reabrir a
   discussao.

---

## Veredito final

**A spec NAO deve ser commitada como esta.** Duas correcoes sao de merito, nao
de estilo: a **1** (o codigo nao implementa a regra calibrada que a 11b promete
-- e exatamente o tipo de divergencia spec-codigo que esta revisao existe para
barrar) e a **2** (numero com genealogia errada em spec aprovada). As correcoes
3-8 sao de registro e custam paragrafos, nao trabalho novo.

O que esta solido e merece ser dito: a decisao 2a e o bloco @10 da 3b3 passaram
por conferencia numero a numero e por remedicao ao vivo **sem um unico desvio**
-- inclusive a parte que nasceu da minha propria caneta como PO. A honestidade
do 77,6% -> ~14% esta de pe e bem construida (o numero de manchete e
explicitamente desmontado no frontmatter, na 11b e na ressalva da 11c); os
reparos exigidos ai sao de precisao, nao de intencao. Decisoes 11/11b e 4/2a
nao se contradizem: se complementam com fronteiras explicitas -- exceto o texto
normativo antigo da decisao 4, que a correcao 6 resolve.
