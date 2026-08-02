# A doadora analoga resolve a peca que falta?

Medicao pura, teste da tese: "para gerar uma peca que falta numa animacao, usar
como base OUTRA PECA PARECIDA (mesmo slot) que ja tenha essa animacao -- peca
e peca tem silhueta parecida; o corpo nu nao." Este relatorio mede uma tese
DIFERENTE da anterior (`2026-08-02_transformacao-aprendivel.md`, que usava o
CORPO como guia e foi negativa). Reaproveitei dela a funcao de campo de
deslocamento (validada byte a byte contra a implementacao antiga, ver secao de
reprodutibilidade) e a logica de rank-de-cor, mas o metodo de escolha de
doadora e a comparacao peca-a-peca sao novos.

Fonte: `/home/igor0/waybuilder/app/public/avatar/catalogo.json` + atlas PNG.
Corpo `male`, frame 64x64. Ambiente: mesmo venv Python 3.12 (numpy 2.5.1,
Pillow 12.3.0, scipy 1.18.0) do relatorio anterior.

## N usado

442 pecas tem as 5 animacoes no corpo `male` (numero confirmado). Dessas, 23
estao em slots onde sao a UNICA peca do slot (`hat_buckle`, `facial_mask`,
`earring_left/right`, `sash`, `gloves`, `eyes` etc.) -- sem outra peca do
mesmo slot, nao existe candidata a doadora, entao ficam fora do teste.
**Populacao usada: 419 pecas, em 42 slots com 2 ou mais itens** (bem acima do
minimo de 150 pedido). Todos os 419 tem 5 animacoes completas: `walk` com 9
frames, `idle` com 2 frames -- confirmado, nao ha exclusao adicional por
frame faltante.

## Par de frames usado (nota metodologica obrigatoria)

O relatorio anterior descobriu que, no CORPO, `walk k=0` e `idle k=0` sao
identicos. Verifiquei aqui se isso se repete ao nivel de PECA: **339 das 419
pecas (80,9%) tambem tem `walk k=0` == `idle k=0` pixel a pixel** (o mesmo
artefato do spritesheet, herdado individualmente). Isso significa que, se eu
usasse so esse par, 4 em cada 5 doadoras teriam campo de deslocamento igual a
identidade -- nao ha o que transplantar.

Por isso, como no relatorio anterior, testei os DOIS pares e reporto ambos:

- **`k0->k0` (par literal)**: reportado na secao "sanity check" abaixo --
  confirma o artefato e mostra que, neste par degenerado, o transplante e
  levemente PIOR que nao fazer nada.
- **`k0->k1` (idle k=1, "respiracao")**: tem movimento real na maioria das
  pecas (apenas 35/419 = 8,4% sao degeneradas nesse par). **Este e o par
  usado como resultado principal em todos os itens abaixo**, por ser onde a
  transformacao de fato existe para ser testada.

## 1) Silhueta: o quao parecidas sao pecas do mesmo slot

IoU (intersecao/uniao) das mascaras de alfa em `walk k=0`, todos os pares
dentro de cada slot com >=2 itens. Slots pedidos explicitamente + os com mais
massa:

| Slot | N | Pares | Mediana IoU | P90 IoU | Melhor par (IoU) |
|---|---|---|---|---|---|
| hair | 89 | 3916 | 0,588 | 0,723 | 1,000 (relm-xlong / relm-short) |
| hat | 50 | 1225 | 0,509 | 0,724 | 1,000 (bicorne-foreaft / bicorne-foreaft-commodore) |
| shield_pattern | 48 | 1128 | 0,268 | 0,487 | 1,000 (barry / revised-barry) |
| head | 32 | 496 | 0,696 | 0,909 | 1,000 (lizard-female / lizard-male) |
| clothes | 22 | 231 | 0,728 | 0,920 | 1,000 (longsleeve-2-buttoned / longsleeve-polo) |
| facial_eyes | 14 | 91 | 0,287 | 0,667 | 1,000 (round-glasses / sunglasses) |
| hat_trim | 13 | 78 | 0,086 | 0,207 | 0,767 |
| legs | 11 | 55 | 0,731 | 0,945 | 1,000 (cuffed-pants / long-pants) |
| ears | 10 | 45 | 0,356 | 0,658 | 0,768 |
| shoes | 10 | 45 | 0,622 | 0,897 | 1,000 (revised-shoes / sara-shoes) |
| accessory | 9 | 36 | 0,000 | 0,336 | 0,932 |
| visor | 9 | 36 | 0,700 | 0,906 | 1,000 |
| mustache | 8 | 28 | 0,206 | 0,552 | 0,875 |
| armour | 2 | 1 | 0,841 | 0,841 | 0,841 (legion / plate -- o proprio exemplo da tese) |

(demais 28 slots com N=2 a 7: valores completos em `exp1_report.json`, alguns
com mediana 0,000 -- ex. `wings`, `tail`, `shield`, `shield_trim`, `sash_tie`
-- pares totalmente sem sobreposicao de silhueta).

**Leitura**: a premissa "peca e peca tem silhueta parecida" se sustenta bem
em `clothes` (mediana 0,73), `legs` (0,73), `head` (0,70), `visor` (0,70) e
razoavelmente em `hair`/`hat` (~0,50-0,59). Falha claramente em slots de
acessorio pequeno/assimetrico (`accessory`, `hat_trim`, `wings`, `tail`,
`shield*`), onde a IoU mediana e proxima de zero -- pecas do mesmo slot
podem nao ter quase nenhuma sobreposicao espacial.

## 2) Transplante da doadora (campo de deslocamento, doadora = maior IoU)

Doadora escolhida por maior IoU de silhueta (excluindo o proprio alvo), campo
de deslocamento calculado nos pixels opacos da DOADORA entre `walk k0` e
`idle k?`, busca de patch 5x5 em janela +-6px (implementacao vetorizada,
validada byte a byte contra o codigo do relatorio anterior no corpo: 0
diferencas em 714 pixels). Campo aplicado ao ALVO em `walk k0`.

### Sanity check -- par literal `k0->k0` (degenerado, 80,9% das doadoras)

| Metrica | Baseline (copiar walk) | Transplante |
|---|---|---|
| Media pixels errados | 18,7 | 21,5 |
| Mediana | 0,0 | 0,0 |
| Frames perfeitos | 339/419 (80,9%) | 328/419 (78,3%) |

O transplante fica **pior** que nao fazer nada (328 < 339 perfeitos): como a
maioria das doadoras nao tem movimento real nesse par, o pouco movimento
espurio que algumas tem (sombra/dither de 1-2px sem relacao com pose)
corrompe alvos que originalmente nao precisavam de nenhuma mudanca. Confirma
a ressalva do enunciado: este par nao serve para testar a tese.

### Resultado principal -- par `walk k0 -> idle k1` (movimento real)

| Metrica | Baseline (copiar walk) | Transplante (campo) |
|---|---|---|
| Media pixels errados | 131,5 | **49,5** |
| Mediana | 115,0 | **33,0** |
| P90 | 256,0 | 111,0 |
| **Frames perfeitos (zero erro)** | 35/419 (8,4%) | **38/419 (9,1%)** |

Comparacao peca a peca: transplante melhor que baseline em **315/419 (75,2%)**,
igual em 95 (22,7%), pior em apenas 9 (2,1%).

**Dois achados que nao se confundem**: (a) o transplante reduz o TAMANHO do
erro de forma ampla e consistente -- corta a media em 62% e a mediana em
71%, melhorando 3 em cada 4 pecas; (b) mas isso quase nao se traduz em
FRAMES PERFEITOS, que e a metrica que decide -- ganho liquido de so 3 pecas
(38 vs 35). Investigando individualmente: dos 38 perfeitos do transplante,
**33 já eram perfeitos no baseline** (pecas que por acaso nao mudam nada
entre as poses -- vitoria de graca, nao do metodo) e só **5 sao vitorias
genuinas** (nao eram perfeitas, viraram): `bandana/bandana`,
`beard/trimmed-beard`, `nose/button-nose`, `ears/elven-ears`,
`ears/long-ears` -- todas em slots pequenos e acessorios. **Nenhuma vitoria
genuina caiu em `hair`, `hat`, `head`, `clothes`, `legs` ou `armour`** -- os
slots que a tese mais importa em massa.

Caso especifico do PROPRIO exemplo da tese (`armour/legion` <-> `armour/plate`,
IoU 0,84, os unicos dois itens do slot): erro cai de 133px para 29px em
`legion` (78% de reducao) e de 93px para 43px em `plate` (54% de reducao) --
maior reducao relativa medida em qualquer slot de peso -- mas **nenhum dos
dois fecha em zero erro**.

## 3) Teto (doadora oraculo -- a que minimiza o erro, escolha impossivel na pratica)

Mesma mecanica, mas testando TODAS as candidatas do slot e ficando com a que
da o menor erro para aquele alvo especifico (15.096 pares doadora-alvo
avaliados no total, exaustivo, nao amostrado).

| Metrica | Baseline | Oraculo (campo) |
|---|---|---|
| Media pixels errados | 131,5 | 34,6 |
| Mediana | 115,0 | 19,0 |
| **Frames perfeitos** | 35/419 (8,4%) | **71/419 (16,9%)** |

O teto quase dobra a taxa de frames perfeitos (16,9% vs 9,1% pratico), com
**36 vitorias genuinas** (nao so as 35 de graca). Isso mostra que existe,
sim, sinal geometrico real a explorar -- em varios casos a doadora ideal nao
e a de maior IoU. Ex.: para varios cortes de cabelo simples
(`buzzcut`, `balding`, `short-topknot`, etc.) a doadora ideal e
`hair/large-curls`, que por si só tem bastante movimento proprio (392px de
diferenca walk->idle) -- ou seja, o campo aprendido dela nao e trivial, e
mesmo assim zera o erro em varias outras pecas de cabelo. Indicio de que o
movimento de fundo (provavelmente o balanco de cabeca do `idle`) e
compartilhado entre pecas do mesmo slot, mesmo quando a forma difere bastante.
Mas mesmo esse teto inatingivel na pratica deixa 83% das pecas com erro
diferente de zero.

## 4) Transplante direto por analogia (sem campo, aritmetica no indice de rampa)

`alvo_idle_previsto = alvo_walk + (doadora_idle - doadora_walk)`, operando no
indice de rampa de cor (0-5, 6=transparente) de cada peca, mesma doadora do
item 2 (maior IoU). Delta so aplicado onde ambos os frames da doadora sao
opacos; fora da mascara do alvo em `walk`, mantido transparente.

| Metrica | Baseline (rank) | Transplante (rank, k1) |
|---|---|---|
| Media pixels errados | 125,3 | 111,4 |
| Mediana | 114,0 | 88,0 |
| **Frames perfeitos** | 35/419 (8,4%) | **30/419 (7,2%)** |

Peca a peca: melhora em 179/419 (42,7%), igual em 117 (27,9%), **piora em
123 (29,4%)**. O metodo simples **perde do baseline** na metrica que decide
(30 < 35 perfeitos) e tambem perde do campo de deslocamento em toda metrica.
A analogia direta em espaco de indice de cor nao funciona aqui -- provavelmente
porque ela nao modela deslocamento espacial (a peca real se move alguns
pixels na tela; somar so o delta de cor no mesmo pixel nao reproduz isso).

## 5) Traducao para o acervo

Taxa usada como resultado pratico: **9,07% (38/419)**, do campo de
deslocamento com doadora por maior IoU (melhor entre os itens 2 e 4 -- o
metodo por indice de cor do item 4 ficou abaixo do baseline e nao entra
aqui).

| Cenario | Taxa de frames perfeitos | Projetado em 43.836 frames faltando |
|---|---|---|
| Pratico (campo, doadora por IoU) | 9,07% | **~3.976 frames** |
| Teto (campo, doadora oraculo -- impossivel na pratica) | 16,95% | ~7.428 frames |
| Analogia direta por indice de cor | 7,16% | ~3.139 frames |
| Par literal k0->k0 (degenerado, NAO usar) | 78,28% | 34.316 -- numero enganoso, artefato do frame repetido, nao mede a tese |

**Sobre a ultima linha**: 78,28% parece o melhor numero da tabela, mas nao e
-- e o mesmo artefato de frame identico do relatorio anterior (a maioria das
pecas simplesmente nao muda entre `walk k0` e `idle k0` por construcao do
spritesheet, entao "prever" e so copiar). Usando esse par o transplante fica
ATE PIOR que copiar sem fazer nada (328 vs 339 perfeitos, secao 2). Nao
reflete a tese sendo testada.

**Sobre o erro tipico nos ~91% que nao saem perfeitos** (metodo pratico,
campo): mediana de erro relativo (erro/pixels opacos do alvo) nos casos
nao-perfeitos = **22,7%** (media 52,9%) -- contra 82,6% de mediana relativa
no baseline. Aplicando essa mediana relativa as pecas de referencia:

| Peca de referencia | Pixels opacos | Erro esperado (mediana relativa 22,7%) |
|---|---|---|
| Calca (161px) | 161 | ~36,5 px errados |
| Bota (120px) | 120 | ~27,2 px errados |
| Manga longa (327px) | 327 | ~74,1 px errados |

Isso e **redesenhar, nao corrigir**: 20-30% dos pixels de uma peca errados
nao e um retoque de "poucos pixels" -- e mancha, silhueta ou sombreamento
fora do lugar numa fracao substancial da peca, tipicamente vista como arte
quebrada e nao como economia de trabalho.

**Slot que funciona bem sozinho?** Nenhum slot de peso (`hair`, `hat`,
`clothes`, `legs`, `armour`, `head`) teve vitoria genuina no metodo pratico
(item 2) -- zero frames perfeitos novos nesses seis slots somados (204 pecas).
As 5 vitorias genuinas caem todas em slots pequenos/acessorios (`ears`,
`nose`, `beard`, `bandana`), universo de poucas dezenas de pecas no acervo
inteiro. O caso `armour` (o proprio exemplo da tese) teve a maior reducao de
erro RELATIVA medida (78% e 54% nos dois unicos itens do slot) mas nenhum dos
dois fechou em zero.

## Veredito

A tese **nao se sustenta** como "gerar a peca faltante", medida pela metrica
que decide (frames perfeitos). Mas ela tem uma parte que se sustenta e outra
que nao, e as duas sao mensuraveis separadamente:

- **O que se sustenta**: a premissa de silhueta (item 1) e real em varios
  slots de peso (`clothes` 0,73, `legs` 0,73, `head` 0,70 de IoU mediana). O
  transplante por campo de deslocamento (item 2, par com movimento real)
  reduz o TAMANHO do erro de forma ampla -- melhora 75% das pecas, corta a
  mediana de erro em 71% frente a so copiar. Isso e maior que o ganho medido
  na tese anterior (corpo como guia, ~11% de reducao de erro medio) -- a
  ideia de "peca parecida generaliza melhor que corpo nu" tem, sim, suporte
  quantitativo aqui.
- **O que nao se sustenta**: essa reducao de erro quase nunca chega a ZERO.
  Frames perfeitos sobem de 8,4% para so 9,1% no metodo pratico -- um ganho
  liquido de 3 pecas em 419, e mesmo essas 5 vitorias genuinas caem todas em
  slots marginais, nenhuma em `hair`, `hat`, `clothes`, `legs`, `head` ou
  `armour`. O teto teorico (doadora oraculo, impossivel de saber na pratica)
  dobra a taxa para 16,9% -- ainda deixa 83% das pecas com erro. A variante
  mais simples (analogia direta por indice de cor, item 4) fica ABAIXO do
  baseline. Projetado nos 43.836 frames faltando: **~3.976 sairiam perfeitos
  pelo metodo pratico** (9,1%), o restante com erro tipico de 20-30% dos
  pixels da peca -- tamanho de redesenho, nao de retoque.

## Reprodutibilidade

Scripts ad-hoc (nao commitados, fora do path do projeto por serem artefato de
medicao): `/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/work/`
(`field_lib.py` -- campo de deslocamento vetorizado, validado contra o
codigo antigo; `prep_items.py` -- preprocessamento dos 419 itens, 42s;
`exp1_iou.py` -- IoU por slot; `exp234.py` -- transplante campo + rank,
pratico + oraculo, 4,1s para as 15.096 comparacoes doadora-alvo; `analyze.py`
-- agregacao final). Venv em
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/venv`.
Dados intermediarios: `items.json`, `prep_data.pkl`, `exp1_report.json`,
`best_donor.pkl`, `iou_matrices.pkl`, `exp234_records.json` (419 registros,
um por alvo, com todas as metricas por metodo).
