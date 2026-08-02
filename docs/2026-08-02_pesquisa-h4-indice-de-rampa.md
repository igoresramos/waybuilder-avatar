# H4 -- indice de rampa amplia o pool de doadoras? (PERDE)

Testei a hipotese H4: converter cada pixel para o indice na rampa de cor da
peca (0-5, cor-invariante) em vez de comparar RGB melhora a escolha de
doadora, melhora o transplante, e amplia o pool de doadoras disponiveis para
pecas orfas.

**Veredito: PERDE nas tres perguntas.** A causa e estrutural, nao um bug de
parametro: o criterio que hoje escolhe a doadora (`sobreposicao`, a IoU de
silhueta) ja e cor-invariante porque so olha o canal alfa -- ele nunca usou
RGB para comecar. E o unico lugar do motor onde RGB realmente decide algo
(`campo_de_deslocamento`, por patch matching) compara sempre dois quadros da
MESMA peca (doadora walk -> doadora idle), nunca doadora contra alvo -- entao
normalizar cor para indice nao toca a etapa que de fato usa RGB.

## Metodo

Amostra: 427 pecas do corpo male, camada 0, com `walk` e `idle` presentes e
silhueta nao-vazia em walk k=0 e idle k=1 -- mesmo par de quadros do baseline
oficial. Validacao por peca (a doadora nunca e a propria alvo). Motor
(`sobreposicao`, `campo_de_deslocamento`, `aplicar_campo`, `pixels_diferentes`)
usado sem reimplementacao.

Indice de rampa: para cada item com `canais_de_cor`, resolvi `base`
(`versao.rampa`) em `paletas/<material>/<material>_<versao>.json`, converti os
6 tons hex para RGB, e classifiquei cada pixel visivel do quadro walk k=0 no
tom mais proximo (tolerancia +-1 por canal, igual ao recolor guide da fase 1).
Itens com mais de um `canais_de_cor` (26 no acervo, ex. capacete + tiras)
tiveram cada canal testado separadamente; o indice guardado e o do canal que
casou.

`index_match(a, b)` = fracao de pixels na UNIAO das silhuetas de a e b onde o
tom (indice mod 6) e igual -- a versao cor-invariante de comparar pixel a
pixel. `rgb_match(a, b)` = a mesma conta mas exigindo RGB identico (a
comparacao "de hoje", se alguem tentasse fazer literalmente).

## 0. A indexacao e sem perda? Quase -- 97,5%, nao 100%

Testei em 316 pecas com `canais_de_cor` (corpo male, walk k=0): 97,52% dos
66.982 pixels visiveis casaram um tom da rampa declarada dentro de +-1, e
81,3% das pecas (257/316) casaram 100% dos pixels. **Nao e lossless em geral**
-- as excecoes tem causa identificavel, nao ruido:

- `prosthesis_leg/peg-leg`: 0% de casamento -- o quadro inteiro e magenta
  `(255,44,230)`, cor de placeholder de dev, nao arte real.
- `shoulders/legion`, `legs/formal-pants`, `gloves/gloves`: 0%, porque a
  peca usa uma cor **customizada fora das paletas catalogadas** --
  `paletas/meta_custom.json` documenta isso: "Custom palettes on a
  case-by-case basis", ou seja o acervo tem por design pecas com paleta
  unica que nao esta em nenhum arquivo de `paletas/`.
- `head/orc-female`, `head/minotaur`, `head/goblin`, `head/frankenstein`
  (75-80%): tons de pele monstro/fantasia fora da rampa `body` padrao.
- `hair/shorthawk`, `hair/high-and-tight` (44-67%): cor de cabelo customizada.

**Implicacao pratica:** so uso o indice em pecas onde >=95% dos pixels
casaram a rampa declarada (limiar de confianca). Isso deixa **352 dos 574
itens do acervo com canal de cor indexavel (61%), e 321 confiaveis (56%)** --
cobertura bem menor que o acervo inteiro, e a fase 2 ja mostrou que essa
lacuna nao e aleatoria (so 30 das 170 pecas legadas declaram material).

## (a) A escolha de doadora melhora com indice? Nao -- diferenca dentro do ruido

Comparando, no mesmo pool de 282 alvos indexaveis, a doadora livre por IoU
(qualquer slot) COM e SEM desempate por `index_match`:

| criterio | cobre | exatos | mediana | media |
|---|---|---|---|---|
| livre por IoU, sem desempate | 282/282 | 19,9% | 20,0 | 37,5 |
| livre por IoU + desempate por indice (H4-A) | 282/282 | 19,9% | 20,0 | **37,4** |

Zero pontos percentuais de diferenca em exatos, mediana identica, media varia
0,1 px -- ruido. **Razao:** quando duas candidatas empatam em IoU de silhueta
(comum -- variantes de cor da mesma peca tem IoU=1,0 identico entre si), o
resultado do transplante depende so de qual foi escolhida para gerar o campo
de deslocamento, e como `campo_de_deslocamento` roda inteiramente dentro da
doadora (walk->idle da propria doadora, nunca cruza com o alvo), a escolha
entre near-empates praticamente nao muda a saida.

## (b) O transplante em si melhora? Nao -- empata ou perde

Baseline recalculado na amostra indexavel (mesmo slot, maior IoU -- a
referencia justa para comparar com H4):

| criterio | cobre | exatos | mediana | media |
|---|---|---|---|---|
| **baseline (mesmo slot, IoU) -- amostra indexavel** | 268/282 | **20,1%** | **20,0** | **36,0** |
| H4-A: livre por IoU + desempate por indice | 282/282 | 19,9% | 20,0 | 37,4 |
| H4-B: SO index_match, sem IoU de silhueta | 282/282 | 18,8% | 24,5 | 43,2 |
| mesmo material, ranking por index_match | 282/282 | 19,9% | 28,0 | 46,5 |

H4-A cobre mais pecas (282 vs 268, porque livre por IoU sempre acha alguem)
mas empata em exatos e perde em media. H4-B mostra que indice **sozinho**,
sem o filtro de forma, e claramente pior (mediana sobe de 20 para 24,5).
`mesmo material + indice` -- a tentativa de reabilitar o material que a fase
2 reprovou, trocando "mesmo rotulo" por "mesma textura de sombra" -- ainda
perde, e feio na mediana (28 contra 20): o material continua sendo o eixo
errado, com ou sem indice.

Para referencia (nao e o numero comparavel, e so contexto): baseline
recalculado na amostra COMPLETA (n=427, nao so a fatia indexavel) deu 21,5%
exatos / mediana 19 / media 35,8 -- proximo do numero oficial (20,0%/28/42,7),
confirmando que a amostra deste teste e representativa.

## (c) Quantas doadoras novas o indice destrava para as orfas? Nenhuma

Das 427 pecas da amostra, **34 nao tem nenhuma outra peca do mesmo slot**
(orfas). Dessas 34, **so 14 (41%) sao indexaveis** -- as outras 20 nao
declaram `canais_de_cor` confiavel, o mesmo padrao ja visto na fase 2 (pecas
legadas raramente declaram material).

Para as 14 orfas indexaveis, contei quantas candidatas (entre as 321
confiaveis) passam do limiar `index_match >= 0,5`, contra o mesmo limiar em
`rgb_match` (comparacao de RGB cru, o que "hoje" literalmente daria se
alguem tentasse):

| metrica | media de candidatas por peca orfa | pecas com ZERO candidatas |
|---|---|---|
| index_match >= 0,5 | 0,0 | **14/14** |
| rgb_match >= 0,5 | 0,1 | 12/14 |

**Indice destrava zero doadoras novas** -- pior que a comparacao de RGB cru
(que por coincidencia de cor achou 2). Razao: `index_match` divide pelos
pixels da UNIAO das silhuetas, entao quando a candidata tem uma forma
diferente do alvo (exatamente o caso das orfas -- e por isso elas nao tem
doadora no mesmo slot, a comparacao por IoU de silhueta ja falhou antes), a
regiao "so um dos dois tem pixel" entra como erro automatico e nenhum par
consegue passar de 0,5. O indice de rampa resolve cor, nao forma -- e o
problema das orfas e forma.

## Por que a hipotese perde, resumido

1. **A comparacao doadora/alvo hoje ja e cor-invariante.** `sobreposicao`
   usa so o canal alfa (silhueta), nunca RGB. Nao havia RGB para substituir
   nessa etapa.
2. **O unico lugar que usa RGB de verdade e interno a doadora**
   (`campo_de_deslocamento` compara doadora walk com doadora idle, patch a
   patch), nunca doadora contra alvo -- normalizar cor pra indice nao muda
   essa etapa porque ela nunca comparou pecas diferentes.
3. **Desempatar por indice entre candidatas de IoU igual nao move o
   resultado**, porque a saida do transplante depende so de qual doadora foi
   escolhida, e near-empates produzem saida quase identica (diferenca de
   0,1 px na media, medida).
4. **A cobertura do indice e menor onde mais precisa**: 56% do acervo e
   indexavel com confianca, mas so 41% das pecas orfas de doadora no mesmo
   slot -- a mesma lacuna de `material` ausente que a fase 2 ja tinha
   documentado.
5. **`index_match` sobre a UNIAO da silhueta nao contorna forma diferente**:
   penaliza automaticamente qualquer regiao onde so uma peca tem pixel, e as
   34 orfas sao orfas justamente porque a forma delas nao bate com nada --
   o indice de cor nao resolve um problema de silhueta.

## Amostra e limitacoes

- Amostra da prova de transplante: 427 pecas (corpo male, camada 0, walk e
  idle nao-vazios); 282 delas com indice confiavel (>=95% dos pixels
  casados na rampa, limiar aplicado apos medir a losslessness real).
- Validacao de losslessness: 316 pecas com `canais_de_cor`, todos os pixels
  visiveis do quadro walk k=0.
- Contagem de orfas: 34 pecas sem outra do mesmo slot na amostra de 427; 14
  delas indexaveis.
- Nao testei limiares de `index_match` diferentes de 0,5 nem uma combinacao
  em peso (em vez de desempate lexicografico) entre IoU e indice -- dado que
  o desempate lexicografico ja mostrou efeito proximo de zero (item a),
  e pouco provavel que outro peso mude a conclusao, mas nao medi.
  Formalmente: **falso pela variavel testada; nao exaustivamente falso para
  qualquer combinacao possivel de peso/limiar.**
  Nao testei fora do par walk k=0 -> idle k=1 (a fase 3 ja mostrou que outros
  pares de animacao tem comportamento bem diferente).
- Nao separei o resultado das 26 pecas com mais de um `canais_de_cor` (o
  indice combina os canais por deteccao automatica de qual rampa casa cada
  pixel) -- nao verifiquei se colisao de indice entre canais diferentes
  prejudica `index_match` nesses casos especificos.

## Scripts

Nao commitados, em
`/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/h4-indice-rampa/`:
`lib.py` (indexacao e metricas), `passo1_lossless.py` (item 0),
`passo2_amostra.py` (dimensionamento), `passo3_prova.py` (itens a, b),
`passo4_orfas.py` (item c).
