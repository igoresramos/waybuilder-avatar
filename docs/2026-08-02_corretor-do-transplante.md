# O resto do transplante e sistematico? Vale um corretor aprendido?

Medicao pura. Usa `transplante.py` sem alteracao (`sobreposicao`, `escolher_doadora`,
`campo_de_deslocamento`, `aplicar_campo`, `pixels_diferentes`). Nao reimplementa o motor.

## Amostra

Catalogo `waybuilder/app/public/avatar/catalogo.json`, corpo `male`. Peca elegivel =
tem as 5 animacoes (`idle`, `combat_idle`, `walk`, `sit`, `run`) em alguma camada do
item (a primeira que satisfaz), y extraido de `cores.base` (ou primeira cor) dessa
mesma camada. **442 pecas** elegiveis (bate com a estimativa do enunciado).

Delas, **419** estao em slots com 2+ itens (candidato a doadora existe). Delas,
**399** tem doadora valida (`escolher_doadora` retornou algo, i.e. sobreposicao > 0
com alguma outra peca do slot) -- essa e a populacao usada em todo o relatorio, acima
do minimo de 300 pedido.

Par usado: doadora `walk k=0 -> idle k=1` (campo de deslocamento), aplicado ao alvo
`walk k=0`, comparado ao alvo `idle k=1` real. Doadora = maior `sobreposicao` no
slot, empate por id (delegado 100% ao modulo).

**Sanity check vs. o numero do enunciado**: nesta amostra completa (399, nao 250),
o transplante puro deu media 38,22px, mediana **27px**, **78/399 = 19,5%** exatas.
O enunciado citava mediana 28px e 17,2% numa amostra de 250 -- mesma ordem de
grandeza, populacao maior aqui, consistente.

## 1) Onde o erro cai

Soma de pixels errados nas 399 pecas, decompostos com a mesma logica de silhueta e
alpha do `pixels_diferentes` (nao alterei a funcao, decompus a mesma regra em 3
categorias que somam exatamente o total de cada peca):

| Tipo | Definicao | Pixels | % do erro total |
|---|---|---|---|
| falta | real tem peca, transplante deixou vazio | 11.098 | 72,8% |
| cor | os dois tem peca, cor (RGB ou alpha) difere | 3.704 | 24,3% |
| sobra | transplante pos peca onde o real nao tem | 447 | 2,9% |

**O erro e majoritariamente "faltou desenhar"**, nao "desenhou errado" nem "desenhou
demais". O campo de deslocamento tende a deixar buracos (silhueta menor que a real)
muito mais do que a inventar pixel fantasma ou acertar a forma e errar so a cor.

Por slot (37 slots com erro > 0; slots com erro = 0 nao aparecem):

| Slot | N pecas | Pixels errados | Sobra % | Falta % | Cor % |
|---|---|---|---|---|---|
| hair | 89 | 5165 | 6,3 | 62,8 | 31,0 |
| shield_pattern | 48 | 2334 | 0,0 | 100,0 | 0,0 |
| hat | 50 | 2299 | 2,0 | 65,4 | 32,6 |
| clothes | 22 | 1013 | 0,6 | 10,1 | 89,3 |
| head | 32 | 759 | 0,0 | 94,1 | 5,9 |
| hat_trim | 13 | 424 | 0,0 | 100,0 | 0,0 |
| legs | 11 | 319 | 10,7 | 47,3 | 42,0 |
| accessory | 6 | 302 | 0,0 | 100,0 | 0,0 |
| hairextr | 7 | 273 | 4,8 | 68,9 | 26,4 |
| overalls | 2 | 268 | 0,7 | 97,8 | 1,5 |
| hairextl | 7 | 249 | 3,6 | 71,9 | 24,5 |
| bandana | 4 | 248 | 0,0 | 100,0 | 0,0 |
| shield_paint | 2 | 218 | 0,0 | 100,0 | 0,0 |
| beard | 5 | 149 | 2,0 | 98,0 | 0,0 |
| headcover | 3 | 117 | 0,0 | 100,0 | 0,0 |
| sleeves | 5 | 115 | 8,7 | 24,3 | 67,0 |
| ears | 10 | 113 | 0,0 | 100,0 | 0,0 |
| armour | 2 | 97 | 1,0 | 44,3 | 54,6 |
| horns | 2 | 96 | 0,0 | 100,0 | 0,0 |
| facial_eyes | 14 | 76 | 0,0 | 100,0 | 0,0 |
| shoulders | 2 | 74 | 0,0 | 100,0 | 0,0 |
| ponytail | 3 | 63 | 0,0 | 100,0 | 0,0 |
| shoes | 10 | 62 | 0,0 | 93,5 | 6,5 |
| socks | 3 | 62 | 0,0 | 100,0 | 0,0 |
| neck | 3 | 48 | 0,0 | 100,0 | 0,0 |
| visor | 9 | 42 | 0,0 | 100,0 | 0,0 |
| expression | 3 | 39 | 0,0 | 100,0 | 0,0 |
| mustache | 8 | 34 | 0,0 | 100,0 | 0,0 |
| ears_inner | 3 | 30 | 0,0 | 100,0 | 0,0 |
| furry_ears | 2 | 30 | 0,0 | 100,0 | 0,0 |
| hat_overlay | 3 | 28 | 0,0 | 100,0 | 0,0 |
| furry_ears_skin | 2 | 27 | 0,0 | 100,0 | 0,0 |
| hat_accessory | 3 | 21 | 0,0 | 100,0 | 0,0 |
| shoes_toe | 2 | 18 | 0,0 | 100,0 | 0,0 |
| fins | 2 | 16 | 0,0 | 100,0 | 0,0 |
| nose | 5 | 11 | 0,0 | 100,0 | 0,0 |
| eyebrows | 2 | 10 | 0,0 | 100,0 | 0,0 |

`clothes`, `sleeves` e `armour` sao os unicos slots de peso onde "cor" domina (a
forma sai certa, a cor errada); em quase todos os outros o erro e majoritariamente
"faltou pixel".

## 2) O erro e previsivel pelo contexto? (predictor honesto)

Split por PECA, 80/20, `RandomState(42)`: **319 treino / 80 teste** (nenhuma peca de
teste aparece no treino). Corretor = lookup exato por contexto (nao k-NN aproximado
nem arvore com scipy -- e um k-NN de raio 0/hash table, numpy puro, `np.unique` +
`searchsorted` sobre patch 5x5 do quadro GERADO em indice de rampa (0-5, 6=vazio) +
posicao relativa dentro da caixa da peca prevista (bin 4x4=16). Rotulo = indice de
rampa certo (0-6) no mesmo pixel. Onde o contexto exato nunca apareceu no treino, o
corretor mantem a saida do transplante (nao arrisca).

- Pixels de treino: 1.306.624 (319 pecas x 4096). Pixels de teste: 327.680 (80 x 4096).
- Contextos unicos no treino: 65.439, dos quais **84,3% aparecem uma unica vez**
  (singleton) -- o espaco de contexto e muito mais esparso que os dados disponiveis.
- Cobertura no teste (contexto ja visto no treino): **95,6%**, mas dominada por
  contexto trivial ("tudo vazio" numa dada posicao): so 1,2% dos pixels de teste
  cobertos vieram de um contexto de suporte 1 no treino.

| Metrica | Valor |
|---|---|
| Acuracia por pixel, teste completo (327.680 px) -- baseline (transplante puro) | 99,18% |
| Acuracia por pixel, teste completo -- corretor | 99,20% |
| Pixels que o transplante errou no teste | 2.683 (0,8% do teste) |
| Acuracia do corretor SO nesses 2.683 pixels errados | **6,56%** |
| Conserta (errado -> certo) | 176 |
| Estraga (certo -> errado) | 111 |
| Saldo liquido (pixel, espaco de rampa) | +65 |

A acuracia "geral" de 99%+ e inflada pelo fundo vazio (a maioria dos 4096 pixels de
qualquer peca e transparente nos dois lados) -- e por isso o proprio enunciado pediu
a metrica condicionada. Condicionada, o corretor acerta **so 6,56%** dos pixels que
o transplante errou. O saldo liquido em pixel e positivo (+65 de 2.683), mas pequeno
e as custas de estragar 111 pixels que já estavam certos.

## 3) O numero que decide

No subconjunto de teste (80 pecas), contadas por igualdade EXATA de todos os 4096
pixels (confirmado que "exato no espaco de rampa" e "exato em RGBA real" batem
nesse subconjunto -- 16/80 nos dois criterios):

| Metodo | Pecas exatas / teste | % |
|---|---|---|
| Baseline (transplante puro) | 16/80 | 20,0% |
| Transplante + corretor | 10/80 | **12,5%** |

O corretor **piora** a metrica que decide: consertou 1 peca so (`clothes/longsleeve-2-vneck`)
e estragou 7 que já saiam exatas (`beard/trimmed-beard`, `ears/elven-ears`,
`facial_eyes/sunglasses`, `hair/flat-top-fade`, `hat/barbarian`,
`hat/celestial-wizard-moon-hat`, `shoes/ghillies`). Resultado liquido: **-6 pecas**
exatas em 80, mesmo com saldo de pixel levemente positivo no item 2. O motivo e o
mesmo da esparsidade acima: corrigir 6-7 pixels certos aqui e ali dentro de uma peca
que ja errava em outro lugar nao a torna exata, mas basta corrigir 1 pixel errado
(por acaso, coincidencia de contexto) numa peca que já era perfeita para quebra-la.

## 4) O teto

Oraculo por contexto exato: mesma feature (patch 5x5 + posicao), mas o lookup e
construido com a populacao INTEIRA (399, sem separar treino/teste -- mede o limite
teorico do espaco de feature, nao generalizacao) e resolve empate por maioria
(ambiguidade contabilizada).

- Contextos unicos (populacao inteira): 79.596. Contextos ambiguos (mais de uma
  classe real observada para o mesmo contexto exato): 982 (1,2%) -- mas concentrados
  em pouquissimos contextos GIGANTES (ex.: o contexto "tudo vazio" mais frequente
  tem suporte 320.745, dos quais 320.152 sao de fato vazio e so 593 nao -- ambiguidade
  real e pequena, nao e 50/50).
- Teto de acuracia por pixel dado o contexto (maioria por contexto): **99,643%**
  (vs. 99,18% do baseline no teste -- ganho real mas marginal em pixel).
- **Teto de pecas exatas, populacao inteira (399): 145/399 = 36,3%** (vs. baseline
  19,5% -- quase o dobro).
- Teto restrito ao mesmo subconjunto de teste usado no item 2/3: **29/80 = 36,2%**
  (vs. baseline 20,0% no mesmo subconjunto).

O teto mostra que **existe, sim, sinal sistematico explorável pelo contexto** --
quase dobra a taxa de pecas exatas se voce tivesse dado infinito e memoria perfeita
por contexto. Mas ele nao chega nem perto de 100%: 63,7% das pecas continuariam
com pelo menos 1 pixel errado mesmo no cenario impossivel.

## 5) Veredito pratico

**Nao vale, na forma atual, treinar um corretor para produzir com o metodo aqui
testado.** Dados que sustentam isso, direto das secoes acima:

- O teto (item 4) mostra que ha sinal real: 36,3% vs 19,5% de pecas exatas se o
  contexto pudesse ser perfeitamente memorizado.
- Mas o corretor honesto (item 2/3), com holdout real por peca, **piora** a metrica
  que decide (12,5% vs 20,0% de exatas) apesar de ter acesso ao MESMO espaco de
  feature do oraculo. A causa medida: 84,3% dos contextos de treino sao singleton
  (1.306.624 pixels de treino nao bastam para cobrir 65.439+ contextos distintos com
  confianca), entao o corretor generaliza mal fora do fundo vazio trivial e, quando
  arrisca, erra mais do que acerta ao nivel de peca inteira (176 consertos vs 111
  estragos EM PIXEL, mas isso vira -6 pecas exatas porque estragar 1 pixel numa peca
  perfeita custa a peca inteira).
- Uma CNN pequena teria potencial de generalizar melhor que o lookup exato
  (compartilha peso entre patches parecidos em vez de exigir bater byte a byte), e
  o teto de 36,3% justifica NAO descartar a ideia de vez. Mas o numero real de
  exemplos de treino disponivel e so **319 pecas** (as unicas com par walk/idle real
  e doadora valida) -- universo pequeno para uma rede aprender bordas de silhueta
  robustas a 37+ slots com geometrias muito diferentes entre si, com risco concreto
  de repetir o mesmo overfitting que quebrou o lookup (que ja tinha 84% de contexto
  singleton com MENOS parametros que uma CNN teria).
- Antes de partir para peso aprendido: reduzir a dimensao do contexto (patch 3x3 em
  vez de 5x5, ou uma feature de "distancia a borda da silhueta" em vez do patch cru)
  e/ou aumentar dado por peça via augmentation (flip horizontal, jitter dentro da
  propria rampa de cor) sao os passos que testariam se a esparsidade e o problema
  central antes de comprometer o esforco de treinar uma rede.

## Reprodutibilidade

Scripts ad-hoc (fora do path do projeto por serem artefato de medicao, nao
commitados): `/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/lpc2/`
(`build_items.py` -- extracao dos 442 itens do catalogo; `step1_transplante.py` --
sanity check do motor; `step2_full.py` -- transplante completo com decomposicao de
erro e rank de cor, 399 registros; `step3_item1.py` -- agregacao item 1;
`step4_corretor.py` -- split treino/teste e features; `step5_train_eval.py` --
lookup + metricas item 2; `step6_item3.py` -- contagem de pecas exatas item 3;
`step7_oracle.py` -- teto item 4; `step8_support.py` / `step9_check_ambig.py` --
checagens de suporte/ambiguidade citadas no texto). Dados intermediarios:
`items.json`, `recs.pkl` (399 registros com pred_rank/real_rank/erro decomposto),
`dataset.pkl` (split treino/teste + features), `item1_report.json`,
`item2_report.json`, `item3_report.json`, `item4_report.json`. Todos os passos
importam `transplante.py` direto (`sys.path.insert`), sem reimplementar o motor.
