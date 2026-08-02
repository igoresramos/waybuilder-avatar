# Anatomia do movimento: como cada animacao move o corpo, por regiao

Medido em 2026-08-02 com o motor de `transplante.py` (nenhuma funcao foi
reimplementada). Corpo `male`, camada 0, direcao "frente" -- o unico recorte que
o acervo guarda.

**Mapa em JSON:** `/home/igor0/waybuilder-avatar/docs/2026-08-02_mapa-de-movimento.json`

## Amostra e baseline

| | |
|---|---|
| Corpo de referencia | `body/body-color`, male, camada 0 |
| Pecas completas (5 animacoes) | **391** itens no male camada 0 (494 se contar cada camada como uma peca) |
| Pecas com doadora do mesmo slot | **349** (as demais sao unicas no slot) |
| Pares de animacao medidos | 25 (5x5), com todos os quadros distintos do destino |
| Campos de deslocamento calculados | 110 (corpo, todos os pares) + 1.564 (pecas, exp. da doadora) |

**Baseline oficial** (250 pecas, male, doadora do mesmo slot por maior IoU,
walk k=0 -> idle k=1): exatos 20,0%, mediana 28, media 42,7.

**Baseline recalculado nesta amostra** (349 pecas, mesmo protocolo):
exatos **22,3%**, mediana **20**, media **36,4**. A amostra e maior e um pouco
mais facil que a oficial; toda comparacao abaixo usa a minha, nao a oficial.

Referencia de piso, na mesma amostra: nao mover nada devolve exatos 6,0% e
mediana 135. Referencia de teto (a peca reconstruida pelo campo dela mesma):
exatos 84,3%, erro medio 2,2% dos pixels opacos.

## Convencao de sinal

`campo_de_deslocamento` devolve, para cada pixel do destino, de onde ele veio na
origem. Tudo neste relatorio esta convertido para **movimento**: `dy > 0` desce
na tela, `dx > 0` vai para a direita. Origem sempre no quadro k=0.

## Regioes

O corpo do acervo e uma vista de cima: calota do cranio no topo, ombros, bracos
nas laterais, coxas e pes embaixo. As bandas foram lidas direto da silhueta do
corpo male.

| regiao | recorte | o que e |
|---|---|---|
| cabeca | `y < 38`, `15 <= x < 49` | calota do cranio e ombros |
| torso | `38 <= y < 50`, `23 <= x < 41` | tronco entre os contornos dos bracos |
| bracos | `38 <= y < 50`, `15 <= x < 23` ou `41 <= x < 49` | bracos, separados do tronco por contorno em x=22 e x=41 |
| pernas | `50 <= y < 57` | coxas |
| pes | `y >= 57` | pes |
| externo | `x < 15` ou `x >= 49` | fora do corpo: capa, asa, arma |

Aviso de amostra: 0,1% dos pixels das pecas completas cai em `externo` e a
populacao de pecas completas e dominada por cabeca (hair 89, hat 50, head 32 de
391). Numeros de `pernas` e `pes` vem de 18 a 30 pecas -- estao no relatorio
porque foram medidos, nao porque sao robustos.

---

## 1. Tabela do movimento, por par e por regiao

`dy / dx (magnitude media)`, em pixels, agregando todos os quadros distintos do
destino. `parados` e a fracao de pixels com deslocamento zero.

| par | cabeca | torso | bracos | pernas | pes | parados |
|---|---|---|---|---|---|---|
| idle->idle | -1.0 / +0.0 (1.1) | -0.2 / +0.0 (0.7) | -0.3 / +0.0 (0.4) | +0.0 / +0.0 (0.0) | +0.0 / +0.0 (0.0) | 64% |
| idle->combat_idle | -0.0 / -0.3 (3.8) | -1.2 / +0.3 (4.8) | -2.3 / +1.9 (5.5) | +0.6 / -0.2 (5.2) | +1.3 / -4.3 (4.7) | 1% |
| idle->walk | +0.3 / -0.0 (0.5) | +0.2 / -0.0 (0.6) | -0.1 / +0.0 (1.3) | +0.2 / -0.0 (2.0) | +0.2 / -0.1 (1.9) | 41% |
| idle->sit | -0.3 / -0.0 (2.2) | +1.2 / +0.3 (4.2) | -1.2 / +0.4 (4.6) | +1.3 / -0.1 (4.3) | +0.5 / -0.1 (3.4) | 0% |
| idle->run | +0.3 / +0.0 (3.1) | -0.4 / -0.0 (3.5) | -1.8 / -0.0 (4.3) | +0.7 / +0.0 (4.1) | +1.3 / +0.0 (3.7) | 1% |
| combat_idle->idle | -1.4 / -0.1 (3.7) | +0.7 / -0.3 (4.8) | +3.0 / +0.9 (6.2) | +1.2 / -0.3 (5.7) | +2.0 / +0.3 (5.5) | 1% |
| combat_idle->combat_idle | +1.6 / +0.2 (2.3) | +1.1 / +0.0 (1.2) | +1.2 / +0.0 (1.2) | +0.2 / -0.1 (0.5) | +0.0 / +0.0 (0.0) | 33% |
| combat_idle->walk | -0.5 / -0.1 (3.6) | +0.5 / -0.5 (4.8) | +2.9 / +0.8 (6.0) | +0.9 / -0.7 (4.9) | +1.9 / -0.1 (4.6) | 0% |
| combat_idle->sit | -0.8 / -0.6 (3.3) | +0.8 / -0.0 (4.7) | +0.4 / +0.6 (4.6) | +1.3 / -0.3 (5.0) | +2.5 / -1.3 (5.0) | 0% |
| combat_idle->run | +0.3 / -1.0 (3.1) | +0.3 / -0.8 (4.5) | +0.5 / +0.6 (3.7) | +0.2 / -1.1 (4.3) | +2.4 / -0.8 (4.6) | 2% |
| walk->idle | -0.6 / +0.0 (0.6) | -0.1 / +0.0 (0.4) | -0.2 / +0.0 (0.2) | +0.0 / +0.0 (0.0) | +0.0 / +0.0 (0.0) | 82% |
| walk->combat_idle | -0.0 / -0.3 (3.8) | -1.2 / +0.3 (4.8) | -2.3 / +1.9 (5.5) | +0.6 / -0.2 (5.2) | +1.3 / -4.3 (4.7) | 1% |
| walk->walk | +0.4 / -0.0 (0.6) | +0.2 / -0.0 (0.7) | -0.1 / +0.0 (1.5) | +0.2 / -0.0 (2.3) | +0.2 / -0.1 (2.1) | 32% |
| walk->sit | -0.3 / -0.0 (2.2) | +1.2 / +0.3 (4.2) | -1.2 / +0.4 (4.6) | +1.3 / -0.1 (4.3) | +0.5 / -0.1 (3.4) | 0% |
| walk->run | +0.3 / +0.0 (3.1) | -0.4 / -0.0 (3.5) | -1.8 / -0.0 (4.3) | +0.7 / +0.0 (4.1) | +1.3 / +0.0 (3.7) | 1% |
| sit->idle | -3.1 / +0.1 (3.5) | -0.6 / -1.2 (4.0) | -0.1 / -0.2 (4.0) | +0.6 / -0.5 (4.9) | +2.4 / -0.6 (4.3) | 0% |
| sit->combat_idle | -1.8 / +0.9 (3.4) | -1.5 / -0.8 (4.2) | -0.7 / +0.3 (2.8) | +1.3 / -1.0 (4.9) | +4.8 / -0.1 (6.0) | 1% |
| sit->walk | -2.1 / +0.2 (2.7) | -0.5 / -1.4 (4.0) | +0.2 / -0.1 (4.2) | +0.6 / -0.2 (4.5) | +2.5 / -0.3 (3.8) | 1% |
| sit->sit | -3.7 / -0.1 (4.0) | +1.6 / -0.2 (4.6) | +0.4 / -0.1 (3.9) | +2.1 / -0.7 (4.9) | +2.1 / -1.2 (4.3) | 0% |
| sit->run | -1.9 / +0.0 (2.8) | -0.8 / -1.2 (4.2) | -1.2 / -0.2 (2.4) | +1.3 / -0.9 (4.5) | +2.8 / +0.3 (4.4) | 3% |
| run->idle | -1.8 / +0.4 (3.5) | +0.1 / +2.0 (3.4) | +0.2 / -0.5 (6.6) | +1.4 / +0.6 (4.0) | +3.2 / +1.0 (5.4) | 2% |
| run->combat_idle | -0.8 / +2.0 (3.0) | -0.2 / -0.9 (4.1) | +0.2 / -0.6 (2.4) | +2.8 / -1.1 (5.2) | +3.1 / +3.1 (6.4) | 2% |
| run->walk | -1.0 / +0.5 (3.1) | +0.1 / +1.9 (3.4) | +0.1 / -0.5 (6.5) | +1.2 / +0.8 (3.6) | +3.0 / +1.4 (5.0) | 3% |
| run->sit | -1.6 / +0.3 (3.2) | +1.4 / +0.8 (4.8) | -0.1 / -0.1 (4.3) | +2.2 / +1.4 (4.8) | +2.7 / +0.5 (5.2) | 1% |
| run->run | -0.6 / +0.1 (2.0) | -0.2 / +1.3 (3.9) | -0.2 / -0.1 (3.8) | +2.2 / +0.1 (3.8) | +2.4 / +1.6 (4.7) | 5% |

Leitura:

1. **`idle -> X` e `walk -> X` sao a mesma linha** porque `idle` k=0 e `walk` k=0
   sao o MESMO quadro no corpo (0 pixels de diferenca) -- e o mesmo em 362 das
   391 pecas completas (92,6%). O ponto de partida do preenchimento e unico.
2. **`walk -> idle` quase nao move nada**: 82% dos pixels ficam parados, pernas e
   pes ficam 100% parados, e o maior deslocamento medio e -0,6 px na cabeca.
   Este e o par com que o baseline foi medido; e o caso mais facil dos 25.
3. **Tres animacoes sao o mesmo grupo de pose e duas nao sao.** A silhueta do
   corpo tem 30 px de largura em `idle`, `walk` e 26-28 em `sit`, mas cai para
   **21 px em `combat_idle` e 22-25 px em `run`**: o boneco vira de lado. Todo
   par que cruza esses dois grupos tem magnitude 3 a 6 px em TODA regiao. Isso
   nao e translacao, e rotacao -- e um campo de deslocamento nao representa
   rotacao.
4. A regiao que mais anda e quase sempre `bracos` (ate 6,6 px em `run->idle`) e
   a que menos anda e `pes`, exceto quando o par cruza os dois grupos de pose.

## 2. O movimento e local, nao uniforme

Duas medidas independentes dizem a mesma coisa.

### 2.1 Variancia dentro x entre regioes

| par | var total | dentro das regioes | entre regioes | explicada pelas regioes |
|---|---|---|---|---|
| walk->idle | 0.6 | 0.5 | 0.1 | 8% |
| walk->walk | 3.8 | 3.8 | 0.0 | 1% |
| walk->combat_idle | 25.2 | 22.2 | 3.0 | 12% |
| walk->sit | 18.8 | 18.0 | 0.8 | 4% |
| walk->run | 16.1 | 15.5 | 0.6 | 4% |
| sit->combat_idle | 22.3 | 17.5 | 4.8 | 22% |
| run->combat_idle | 23.6 | 18.9 | 4.7 | 20% |
| combat_idle->run | 20.6 | 20.0 | 0.6 | 3% |

Nos 25 pares, as regioes explicam entre **0,5% e 23%** da variancia do
deslocamento (mediana 9,6%). Ou seja: 77% a 99,5% da variacao esta DENTRO da
regiao. Saber que um pixel e do braco quase nao diz para onde ele vai.

### 2.2 Custo de cada granularidade

Erro em pixels ao reconstruir o proprio destino do corpo a partir da propria
origem, com quatro modelos de campo. `parado` = campo zero. `global` = uma unica
translacao (mediana). `regiao` = uma translacao por regiao. `pixel` = o campo
cheio.

| par | parado | global | regiao | pixel | quanto o campo global recupera | quanto o por regiao recupera |
|---|---|---|---|---|---|---|
| walk->idle | 81 | 81 | 52 | 33 | 0% | 60% |
| walk->walk | 275 | 254 | 228 | 111 | 13% | 28% |
| walk->combat_idle | 328 | 328 | 291 | 238 | -1% | 41% |
| walk->sit | 420 | 394 | 356 | 247 | 15% | 37% |
| walk->run | 355 | 324 | 314 | 230 | 24% | 33% |
| combat_idle->walk | 592 | 587 | 574 | 370 | 2% | 8% |
| run->walk | 519 | 532 | 524 | 362 | **-8%** | -3% |
| run->idle | 560 | 570 | 560 | 374 | **-5%** | 0% |
| sit->sit | 454 | 316 | 282 | 182 | 51% | 63% |

**Quantificacao pedida:** um campo unico global recupera em mediana **12%** do
erro que o campo por pixel recupera, e em 5 dos 25 pares (`run->idle`, `run->walk`,
`run->combat_idle`, `walk->combat_idle` e seu gemeo `idle->combat_idle`) ele
**piora** o resultado em relacao a nao mexer em nada. Um campo por regiao recupera em mediana 28%.
Nenhum dos dois substitui o campo por pixel; a granularidade fina nao e um
detalhe de implementacao, e o metodo.

### 2.3 Onde o proprio campo ja falha

| par | pixels saturados (deslocamento 6 em algum eixo) | vetores distintos | coerencia com o vizinho | teto de erro do metodo |
|---|---|---|---|---|
| walk->idle | 0% | 12 | 92% | 5% |
| combat_idle->combat_idle | 1% | 8 | 90% | 10% |
| walk->walk | 2% | 44 | 79% | 17% |
| sit->sit | 21% | 74 | 59% | 33% |
| walk->run | 11% | 90 | 41% | 48% |
| walk->sit | 24% | 93 | 42% | 46% |
| walk->combat_idle | 21% | 105 | 38% | 58% |
| run->walk | 26% | 113 | 35% | 54% |
| combat_idle->idle | 26% | 138 | 37% | 55% |

- **saturado**: o `raio=6` de `campo_de_deslocamento` limita cada eixo a 6 px.
  Nos pares que cruzam grupos de pose, 11% a 32% dos pixels batem no limite --
  o movimento real e maior do que o campo consegue escrever.
- **coerencia**: fracao de pixels vizinhos horizontais com deslocamento
  identico. Cai de 92% (walk->idle) para 34-42% nos pares dificeis: mais da
  metade dos vizinhos discorda, o que e assinatura de casamento por ruido, nao
  de movimento.
- **teto de erro**: erro de aplicar o campo da doadora sobre a PROPRIA doadora,
  dividido pelos pixels opacos. Em `walk->idle` e 5%. Nos 12 pares que cruzam os dois grupos de pose
  (frente <-> perfil) o campo **erra 46% a 58% dos pixels da propria peca que o
  gerou**; nos pares dentro do grupo frente com pose diferente (`walk->sit`,
  `sit->sit`) fica em 33% a 46%. Nenhuma alvo pode sair melhor do que isso.

## 3. As pecas se movem como o corpo? Nao.

391 pecas completas, campo proprio de cada uma contra o campo do corpo.

### 3.1 O corpo nem sequer cobre a peca

| medida (walk k=0 -> idle k=1) | valor |
|---|---|
| pixels em que a peca e o corpo coexistem, mediana | **6** |
| pecas com menos de 8 px em comum com o corpo | **50,8%** |
| pecas com menos de 30% da propria area sobre o corpo | **72,8%** |

Metade do acervo completo nao encosta no corpo no quadro de destino: cabelo,
chapeu, visor, orelha e acessorio ficam acima da calota do cranio, onde o campo
do corpo e zero por construcao. Para essas pecas o corpo nao tem o que ensinar.

### 3.2 Onde coexistem, o campo diverge

| par | campo identico ao do corpo | desalinho medio |
|---|---|---|
| walk -> idle k=1 | 72,4% | 0,44 px |
| walk -> sit k=1 | 14,7% | 3,77 px |
| walk -> run k=1 | 8,0% | 2,89 px |
| walk -> combat_idle k=1 | 7,3% | 4,12 px |

E o que isso custa em pixels (erro relativo aos opacos da peca; `campo proprio`
e o teto, `campo do corpo` e usar o movimento do corpo com a silhueta correta da
peca, isolando erro de movimento de erro de forma):

| par | campo proprio | campo do corpo | parado |
|---|---|---|---|
| walk -> idle k=1 | 2,2% (84,3% exatos) | 52,9% (8,0% exatos) | 61,8% (6,1% exatos) |
| walk -> combat_idle k=1 | 10,1% (74,7%) | 74,2% (0,0%) | 75,1% |
| walk -> run k=1 | 9,8% (69,9%) | 77,0% (0,0%) | 80,1% |
| walk -> sit k=1 | 55,9% (1,3%) | 89,2% (0,0%) | 93,6% |

Restringindo as 92 pecas que de fato ficam sobre o corpo (>=30% de area
sobreposta), em `walk->idle`: campo proprio 6,7% de erro, campo do corpo 23,1%,
parado 39,6%. O movimento do corpo ajuda, mas devolve so 50% do caminho que o
campo proprio devolve -- e esse e o melhor caso dos quatro.

### 3.3 As classes que nao seguem o corpo

Divergencia = `|movimento medio da peca - movimento medio do corpo|` na mesma
regiao e no mesmo quadro. Em `walk -> combat_idle k=1` e `walk -> run k=1`,
ordenado pela maior divergencia:

| classe (slot) | n | onde diverge | divergencia |
|---|---|---|---|
| `hairextl` / `hairextr` (cabelo comprido lateral) | 14 | bracos | **3,7 a 7,1 px** |
| `sleeves` (mangas soltas) | 5 | torso | 5,9 px |
| `ponytail` / `updo` (rabo de cavalo, coque) | 4 | cabeca | 2,2 a 6,4 px |
| `neck` (gola) | 3 | torso | 2,3 px |
| `shoes` / `socks` | 13 | pernas | 3,4 a 4,1 px |
| `hat` / `hair` / `head` (o grosso do acervo) | 171 | cabeca | 1,7 a 1,8 px |
| `clothes` | 22 | torso | 0,9 px |

O cabelo comprido e a classe nomeada que mais se descola: no `walk->sit`, as
tranças e cabelos xlong tem erro proprio de 20 a 86 px e erro com o campo do
corpo de 45 a 121 px -- o corpo praticamente nao explica nada do movimento
delas. `updo/high-bun` e `ponytail/relm-topknot` sao os casos extremos (campo do
corpo = mesmo erro que nao mover).

**Uma classe que nem chega a ter movimento:** 16 das 391 pecas completas
(`wings/*`, `tail/*`, `shield*`, `accessory/*-horns`, `hat_accessory/cavalier-feather`)
tem quadros VAZIOS no recorte de frente -- asa e rabo sao desenhados so em
algumas direcoes/quadros. Sao 330 quadros vazios entre os 8.993 medidos. Em 2
casos a origem esta vazia e o destino nao: o transplante e impossivel por
construcao, nao por qualidade.

## 4. Regiao trivial e regiao perdida

Transplante atual (349 pecas, doadora do mesmo slot por maior IoU, campo
walk k=0 -> destino k=1), erro contado dentro de cada regiao. "pecas" e quantas
das 349 tem pixel naquela regiao.

**Destino `idle` k=1** -- global: exatos 22,3%, mediana 20. Sem mover: 6,0%, mediana 135.

| regiao | pecas | exatos | mediana | media | px medios |
|---|---|---|---|---|---|
| cabeca | 323 | 22,0% | 18 | 32,7 | 200 |
| torso | 79 | 13,9% | 16 | 17,2 | 66 |
| bracos | 40 | 10,0% | 6 | 7,6 | 26 |
| **pernas** | 24 | **50,0%** | 2 | 11,2 | 66 |
| **pes** | 18 | **66,7%** | **0** | 7,0 | 66 |

**Destino `combat_idle` k=1** -- global: exatos 17,8%, mediana 30.

| regiao | pecas | exatos | mediana | media |
|---|---|---|---|---|
| cabeca | 323 | 19,5% | 20 | 37,2 |
| torso | 107 | 10,3% | 21 | 23,3 |
| bracos | 48 | 43,8% | 1 | 7,4 |
| **pernas** | 30 | **0,0%** | 26 | 30,8 |
| **pes** | 20 | **0,0%** | 10 | 12,8 |

**Destino `run` k=1** -- global: exatos 14,3%, mediana 35.

| regiao | pecas | exatos | mediana | media |
|---|---|---|---|---|
| cabeca | 320 | 16,6% | 23 | 48,1 |
| torso | 116 | 19,0% | 19 | 25,6 |
| bracos | 54 | 3,7% | 8 | 11,0 |
| **pernas** | 26 | **0,0%** | 38 | 36,3 |
| **pes** | 25 | **0,0%** | 21 | 18,9 |

**Destino `sit` k=1** -- global: exatos **0,0%**, mediana 123.

| regiao | pecas | exatos | mediana | media |
|---|---|---|---|---|
| cabeca | 273 | 0,0% | **122** | 125,5 |
| torso | 213 | 0,5% | 24 | 33,8 |
| bracos | 104 | 0,0% | 13 | 14,5 |
| pernas | 69 | 0,0% | 21 | 27,0 |
| pes | 28 | 0,0% | 12 | 23,4 |

Respondendo direto:

- **Trivial:** `pes` e `pernas` no destino `idle`. O corpo move 0,00 px ali
  (100% dos pixels parados) e o transplante acerta 66,7% e 50,0% dos casos, com
  mediana 0 e 2 pixels errados. Sao as unicas celulas do estudo em que o
  transplante e majoritariamente exato. Ressalva de amostra: 18 e 24 pecas.
- **Sempre ruim:** `pernas` e `pes` nos destinos `combat_idle` e `run` --
  **0,0% de exatos nas quatro celulas**, mediana 10 a 38 px. Sao exatamente as
  regioes cujo movimento cruza os dois grupos de pose (o corpo gira e as pernas
  trocam de posicao). E `cabeca` no destino `sit`: 0,0% de exatos e mediana de
  122 pixels errados, o pior numero de todo o estudo -- em `sit` k=1 a cabeca do
  corpo desce para fora da banda `y < 38`, e a peca de cabeca nao tem para onde
  ser levada.
- A animacao `sit` inteira e insalvavel pelo metodo atual: 0,0% de exatos em
  todas as regioes e em todas as 349 pecas.

## 5. Consequencia para a escolha da doadora

Testei, para cada alvo, TODAS as doadoras do mesmo slot (331 alvos com pelo
menos duas candidatas e IoU > 0, media de 37 candidatas por alvo):

| destino | regra atual (maior IoU) | oraculo (melhor candidata) | candidata media | pior candidata | corr(IoU, erro) |
|---|---|---|---|---|---|
| idle k=1 | 23,6% exatos, mediana 20 | 30,2% exatos, mediana 10 | mediana 60 | mediana 148 | **-0,60** |
| combat_idle k=1 | 18,7%, mediana 30 | 24,2%, mediana 16 | mediana 72 | mediana 171 | -0,36 |
| run k=1 | 15,1%, mediana 36 | 21,1%, mediana 21 | mediana 78 | mediana 171 | **-0,00** |
| sit k=1 | 0,0%, mediana 124 | 0,0%, mediana 122 | mediana 166 | mediana 218 | -0,43 |

- A regra do maior IoU **funciona e vale muito**: contra a candidata media ela
  corta a mediana de erro de 60 para 20 em `idle`, e captura 86% a 94% do ganho
  que um oraculo obteria.
- O teto da escolha de doadora e baixo: mesmo escolhendo perfeitamente, os
  exatos vao de 23,6% para 30,2% em `idle`. **O gargalo nao e qual doadora, e o
  modelo de campo.**
- Em `run` a correlacao entre IoU e erro e **zero** (-0,001). Silhueta parecida
  na pose de partida nao prediz nada sobre transferir um movimento de rotacao.
  Escolher doadora por IoU do quadro de partida e, para `run`, escolher no
  escuro.

---

## Onde estao os numeros

- Mapa completo por `(animacao_origem, animacao_destino, regiao)`, mais
  `transplante_por_regiao`, `pecas_contra_o_corpo` e `escolha_da_doadora`:
  **`/home/igor0/waybuilder-avatar/docs/2026-08-02_mapa-de-movimento.json`**
- Scripts do experimento (nao versionados):
  `/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/movimento/`
  (`base.py`, `exp1_mapa.py`, `exp3_pecas.py`, `exp4_regioes.py`,
  `exp5_doadora.py`, `consolidar.py`)
