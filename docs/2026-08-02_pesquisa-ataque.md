# Ataque as conclusoes das fases 1 e 2

Data: 2026-08-02
Motor usado sem reimplementacao: `transplante.sobreposicao`, `campo_de_deslocamento`,
`aplicar_campo`, `pixels_diferentes`.
Scripts (nao commitados): `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/ataque/`
(`lib.py` -> `a1_vazamento.py` -> `a2_repro.py` -> `a3_legado.py` -> `a4_metrica.py` -> `a5_rigidez.py` -> `a6_visual.py`).
Prova visual: `docs/2026-08-02_ataque-metrica.png`.

**Diferenca de metodo em relacao as fases anteriores:** eu componho TODAS as camadas
da peca (ordenadas por zPos) antes de medir. A fase de movimento e a H2 mediram
`camadas[0]` apenas. Isso importa e esta medido no Ataque 1b.

## Reproducao antes de atacar

male, `walk k=0 -> idle k=1`, pool de 464 itens (todos com as duas artes compostas),
428 com deslocamento de slot disponivel por leave-one-out:

| metodo | n | exatos | mediana | media |
|---|---|---|---|---|
| nao mexer (piso) | 464 | 5,6% | 111 | 134,9 |
| **translacao rigida LOO por slot (H1)** | 428 | **77,6%** | **0** | **22,3** |
| transplante, doadora mesmo slot maior IoU (baseline) | 428 | 20,1% | 22 | 42,1 |
| transplante, doadora livre por IoU | 464 | 19,6% | 20 | 38,3 |

Baseline oficial declarado: 20,0% / 28 / 42,7 (n=250). **Reproduz.** Os numeros da
H1 (77,6% / 0 / 22,3 e 20,1% / 22 / 42,1) saem identicos aos meus, o que significa
que estou medindo a mesma coisa que ela.

---

## Ataque 1 -- VAZAMENTO por arte duplicada: **CONFIRMA** (mas o defeito favorece o baseline)

Hash RGBA do par (walk k0, idle k1), transparente normalizado:

- **13 grupos de arte byte a byte identica sob ids diferentes, 26 itens**, e os 13
  grupos caem **dentro do mesmo slot** -- exatamente onde a doadora e procurada.
  Exemplos: `hat/bascinet` = `hat/round-bascinet`; `head/wolf-female` = `head/wolf-male`;
  `hair/long-topknot` = `hair/short-topknot`; `facial_eyes/eyepatch-ambidextrous` =
  `facial_eyes/eyepatch-left`; `nose/elderly-nose` = `nose/large-nose`.
- 36 grupos com silhueta identica (77 itens) -- o IoU dessas e 1,000 e o desempate
  cai no id.

Efeito medido nos 26 itens: **transplante 100,0% exato, translacao 100,0% exata.**
O transplante acerta porque a doadora e a propria arte com outro nome: IoU = 1, campo
perfeito, copia exata.

Removendo as duplicatas (n=402):

| | com duplicatas | sem duplicatas |
|---|---|---|
| transplante mesmo slot | 20,1% | **14,9%** |
| translacao por slot | 77,6% | 76,1% |

**O vazamento infla o BASELINE em 35% relativo e a hipotese em 2%.** O defeito e
real e nao estava declarado em lugar nenhum, mas corrigi-lo *aumenta* a vantagem da
H1 (de 3,9x para 5,1x). Nao derruba nada; derruba o baseline.

## Ataque 1b -- VAZAMENTO por quadro VAZIO na H2: **CONFIRMA, e este derruba um numero publicado**

A H2 mediu `camadas[0]`. Treze das 366 pecas da amostra dela tem a camada 0 vazia no
recorte frontal (chifres, asas, caudas, escudo revisado): `accessory/*-horns`,
`wings/*`, `tail/*`, `shield/revised-heater-shield-base`, `shield_trim/revised-heater-shield-trim`.
Origem vazia e destino vazio dao `pixels_diferentes = 0` -- **frame "exato" de graca,
para qualquer metodo, inclusive para o controle nulo.**

Recontagem feita nos **proprios `resultados.json` da H2**, excluindo `area == 0`:

| animacao | H2 publicou | exatos reais | baseline publicado | baseline real |
|---|---|---|---|---|
| idle | 24,9% | **22,1%** | 9,3% | 5,9% |
| combat_idle | 20,5% | **17,6%** | 3,6% | 0,0% |
| run | 17,2% | **14,2%** | 3,6% | 0,0% |
| **sit** | **3,6%** | **0,0%** | 3,3% | **0,0%** |

Em sit, **13 dos 13 frames exatos eram quadros vazios; 12 deles tambem estavam vazios
no controle nulo.** A frase "sit 3,6% contra 3,3% do fazer-nada, empate estatistico"
descreve 13 pecas invisiveis, nao arte. O numero correto e **0,0% contra 0,0%**, que
e o que a fase de movimento tinha achado -- a divergencia entre as duas fases era este
defeito, nao empate de IoU.

A conclusao qualitativa da H2 (sit fora do build) **sobrevive e fica mais forte**. Os
tres numeros de idle/combat_idle/run caem ~3,5 pontos cada.

## Ataque 2 -- O PAR DE FRAMES: **NAO CONFIRMA** para a H1 (mas o risco era enorme)

A H1 mediu `k=1`. Prova: rodei o pipeline dela nos dois k e so `k=1` reproduz os
numeros publicados (77,6 / 0 / 22,3 e 20,1 / 22 / 42,1). Em `k=0` os numeros seriam
outros.

Quanto valeria a contaminacao, medido (male, n=464 / 428):

| par | nao mexer | translacao | transplante |
|---|---|---|---|
| walk k0 -> idle k**1** (correto) | 5,6% | 77,6% | 20,1% |
| walk k0 -> idle k**0** (contaminado) | **87,5%** | 87,1% | 25,0% |

E o detalhe que importa: **nas 55 pecas em que o par k=0 nao e trivialmente identico,
a translacao da 0,0% de exatos com mediana 78, PIOR que o transplante (0,0%, mediana
55).** Ou seja, medir em k=0 nao so daria +9,5 pontos de graca como inverteria o
veredito no unico subconjunto informativo. O risco apontado no briefing e real; a H1
escapou dele.

No par correto so 24 de 464 (5,2%) sao identicas de saida -- nao ha contaminacao
residual.

## Ataque 3 -- AMOSTRA: **NAO CONFIRMA**

Todos os cortes, male walk0->idle1:

| corte | n | translacao | transplante |
|---|---|---|---|
| tudo | 428 | 77,6% | 20,1% |
| tirando as 24 em que nao mexer ja era exato | 404 | 76,7% | 19,3% |
| tirando as 86 em que o **baseline** ja era exato | 342 | **71,9%** | 0,0% |
| tirando as 26 duplicatas | 402 | 76,1% | 14,9% |
| **macro-media por slot** (44 slots, cada slot pesa 1) | 44 | **78,1%** | 20,1% |
| mediana entre os 44 slots | 44 | 100,0% | 11,8% |
| tirando os 6 maiores slots (hair, hat, head, shield_pattern, clothes, charm) | 195 | **82,6%** | 23,6% |

O ganho **nao** vem de um punhado de pecas faceis nem de slots grandes: sem os 6
maiores slots ele *sobe*. Micro e macro media coincidem (77,6 vs 78,1). Resiste.

## Ataque 4 -- A METRICA: **CONFIRMA**

Tres defeitos, todos medidos.

**(a) A H1 nao melhora o acervo, ela o particiona.** Chamo de RIGIDA a peca para a
qual existe algum `(dy,dx)` com erro zero:

| | n | translacao | transplante | teto da translacao |
|---|---|---|---|---|
| rigidas | 337 (78,7%) | **98,5%** exatos, mediana 0 | 25,5%, mediana 15 | -- |
| **nao-rigidas** | 91 (21,3%) | **0,0%**, mediana 88, media 98,1 | **0,0%, mediana 51, media 74,6** | mediana 76 |

Nas 91 pecas que realmente deformam, a translacao e **73% pior em mediana de erro que
o transplante** -- e o oraculo mostra que nenhuma escolha de `(dy,dx)` salva (mediana
76 no melhor caso possivel). A metrica primaria da 0,0% para os dois e nao ve a
diferenca.

**(b) Quando a translacao falha, ela falha muito mais fundo:**

| metodo | n de fracassos | mediana do erro | fracao da area errada (mediana) | acima de 25% da area |
|---|---|---|---|---|
| translacao | 96 | 87 px | **0,454** | **80,2%** |
| transplante | 342 | 32 px | 0,192 | 38,9% |

Ou seja: 78% dos frames ficam perfeitos e os 22% restantes saem com quase metade da
peca errada. O `% exatos` sobe de 20 para 78 enquanto a cauda piora.

**(c) Regressao pura -- a tabela do slot destroi arte que estava certa.** Em 13 pecas
transladar e pior que nao mexer. Em **2 delas nao mexer era EXATO**:

| peca | area | nao mexer | translacao | transplante | desloc do slot | otimo da peca |
|---|---|---|---|---|---|---|
| `hat/formal-bowler-hat` | 344 | **0** | 193 | 191 | (-1,0) | (0,0) |
| `hat/tiara` | 30 | **0** | 40 | 40 | (-1,0) | (0,0) |
| `hair/bob-side-part` | 321 | 27 | 243 | 287 | (-1,0) | (0,0) |
| `hair/twists-fade` | 276 | 39 | 241 | 290 | (-1,0) | (0,0) |
| `clothes/cardigan` | 288 | 117 | 141 | 52 | (-1,0) | (0,0) |

Prova visual em `docs/2026-08-02_ataque-metrica.png` (colunas: walk k0 | idle k1 real
| translacao | transplante). O chapeu-coco sobe 1 px e descola da cabeca; a arte
original nao se mexia. A tabela por slot introduz um defeito onde nao havia nenhum em
2 de 24 casos (8,3%) e piora em 13 de 428 (3,0%).

Uma ressalva honesta na direcao contraria: `pixels_diferentes` **exagera** o custo de
1 px de deslocamento (193 pixels "errados" para um chapeu que o olho quase nao
distingue). Como metrica secundaria ela e ruim nos dois sentidos -- infla o dano de
um erro de fase e nao distingue "1 px de fase" de "metade da peca embaralhada".

## Ataque 5 -- GENERALIZACAO DE CORPO: **NAO CONFIRMA**

Testei os **6 corpos**, mesmo protocolo, `walk k0 -> idle k1`:

| corpo | n | translacao | transplante | translacao (tirando base-exatas) |
|---|---|---|---|---|
| male | 428 | 77,6% | 20,1% | 71,9% |
| female | 438 | 77,4% | 19,2% | 72,0% |
| teen | 432 | 77,1% | 19,2% | 71,6% |
| muscular | 380 | 84,7% | 21,8% | 80,5% |
| pregnant | 389 | 83,0% | 21,1% | 78,5% |
| child | 71 | 90,1% | 26,8% | 86,5% |

Resiste em todos, inclusive nos tres que a H1 declarou como nao testados
(teen, muscular, pregnant). Nenhum corpo cai abaixo de 77%.

## Ataque 6 -- LEGADAS x COMPLETAS: **CONFIRMA. E o defeito decisivo.**

### 6.1 O censo das lacunas nao bate com nenhum numero em circulacao

Contagem propria, definicao explicita: par (item, corpo) em que o corpo existe para
a peca e a animacao NAO existe.

| animacao ausente | celulas | frames |
|---|---|---|
| idle | 365 | 730 |
| combat_idle | 877 | 1.754 |
| run | 829 | 6.632 |
| sit | 793 | 2.379 |
| **total sem walk** | **2.864** | **11.495** |
| (walk, so por completude) | 135 | 1.215 |

**2.864 celulas / 11.495 frames.** Nem 3.666 nem 2.041. 236 itens afetados.

### 6.2 A tabela por slot nao alcanca 72% das lacunas

Cobertura real: existe **outra** peca do MESMO slot, no MESMO corpo, com `walk` e
com a animacao alvo (a condicao minima para ter deslocamento ou doadora):

| lacuna | celulas | com parceiro no slot | % |
|---|---|---|---|
| idle | 365 | 224 | **61,4%** |
| combat_idle | 877 | 293 | 33,4% |
| run | 829 | 157 | 18,9% |
| sit | 793 | 134 | 16,9% |
| **total** | **2.864** | **808** | **28,2%** |

Slots sem nenhum parceiro, por volume: `shield_pattern` (240 celulas), `weapon` (117),
`charm` (80), `earrings` (25), `necklace` (25), `belt` (21), `backpack` (16), `cargo` (12).
No male, 64 das 91 pecas sem idle (70,3%) nao tem nenhuma peca completa no proprio slot.

### 6.3 As legadas sao outra populacao de arte -- medido

Perfil no `walk k=0`, male (completa = tem as 5 animacoes):

| | n | area mediana | tons mediano | com mais de 6 tons | com alfa parcial |
|---|---|---|---|---|---|
| completas | 388 | **209,5** | 6,0 | 18,3% | 6,2% |
| legadas | 163 | **101,0** | 5,0 | 25,8% | 1,8% |
| legadas sem idle | 87 | 187,0 | 6,0 | **37,9%** | 3,4% |

E o que mais importa, porque e a premissa da H1 -- **rigidez** (existe `(dy,dx)` com
erro zero entre walk k0 e idle k1):

| | n | rigidas | deslocamento otimo (0,0) |
|---|---|---|---|
| completas | 388 | **83,5%** | 47 (12,1%) |
| legadas | 76 | **55,3%** | 30 (39,5%) |

**A premissa da H1 vale em 83,5% das pecas que ja tem a arte e em 55,3% das legadas.**
E 4 em cada 10 legadas nao devem se mexer, contra 1 em cada 8 das completas -- a
tabela aprendida nas completas (moda esmagadora `(-1,0)`) vai empurrar peca parada.

### 6.4 Teste direto: mesmo par, alvo legado real

76 pecas de formato legado que **tem** idle no male (portanto mensuraveis), contra as
388 completas. Mesmo par `walk k0 -> idle k1`, LOO por peca.

**Treino/doadora = qualquer peca do slot com walk+idle (cenario de producao):**

| alvo | n | cobertos | translacao (nos cobertos) | efetivo | transplante | efetivo |
|---|---|---|---|---|---|---|
| completas | 388 | 362 | **82,0%** exatos, media 18,6 | 76,5% | 21,5% | 20,1% |
| **legadas** | 76 | 66 | **53,0%** exatos, media **42,7** | **46,1%** | 12,1% | 10,5% |

**Treino/doadora = so pecas completas (cenario dos slots inteiramente legados):**

| alvo legado | cobertos | exatos nos cobertos | efetivo sobre os 76 |
|---|---|---|---|
| translacao por slot | 15/76 | 66,7% | **13,2%** |
| transplante mesmo slot | 15/76 | 6,7% | 1,3% |
| transplante doadora livre por IoU | **76/76** | 1,3% (mediana 36,5) | 1,3% |

Segunda evidencia independente, par `walk k0 -> walk k1` (disponivel nos dois grupos,
treino so com completas): transplante nas completas 21,3% exatos / mediana 24;
**nas legadas 0,0% / mediana 89,5 / media 163,6** -- erro maior que a area mediana da
propria peca. Mesma direcao, outra medida.

### 6.5 Leitura

**77,6% e o numero das pecas que ja tem a arte.** No alvo que interessa ele cai para
53,0% quando existe parceiro no slot, e para 13,2% quando o slot inteiro e legado. E
esse 53,0% ainda e o melhor caso possivel: sao legadas que alguem ja portou para idle
em algum momento -- as 91 do male sem idle nenhum nao sao mensuraveis por metodo
nenhum, e 70,3% delas nem parceiro de slot tem.

Multiplicando cobertura por acerto, a estimativa honesta do que o pipeline entrega
hoje: idle 61,4% de cobertura x ~53% de acerto = **~33% das lacunas de idle** saem
como frame exato. Em run e sit a cobertura sozinha (18,9% e 16,9%) ja limita o teto.

---

## Placar

| ataque | veredito | numero que decide |
|---|---|---|
| 1. vazamento por arte duplicada | **CONFIRMA** | 26 itens gemeos; baseline 20,1% -> 14,9% sem eles |
| 1b. vazamento por quadro vazio (H2) | **CONFIRMA** | sit 3,6% -> **0,0%** exatos; idle 24,9% -> 22,1% |
| 2. par de frames k=0 | NAO CONFIRMA | H1 mediu k=1; k=0 daria 87,1% e inverteria as nao-triviais |
| 3. amostra de pecas faceis | NAO CONFIRMA | macro-media por slot 78,1%; sem os 6 maiores slots 82,6% |
| 4. a metrica | **CONFIRMA** | fracassos com 45,4% da area errada; 2 pecas exatas destruidas |
| 5. generalizacao de corpo | NAO CONFIRMA | 77,1% a 90,1% nos 6 corpos |
| 6. legadas x completas | **CONFIRMA** | 82,0% -> 53,0%; rigidez 83,5% -> 55,3%; cobertura 28,2% |

## O que sobrevive

1. **A translacao rigida bate o transplante, e por mais do que a H1 disse.** Sem as
   duplicatas a razao vai de 3,9x para 5,1x. Resiste aos 6 corpos, ao corte das
   faceis, a macro-media por slot e ao par de frames correto.
2. **sit fica de fora.** Nao por empate: por 0,0% de frames exatos reais.
3. **Material e zPos continuam ruins como criterio.** Nao reataquei; nada do que medi
   contradiz.

## O que nao sobrevive

1. **"77,6% de frames exatos" como promessa do entregavel.** E 53,0% no alvo legado
   com parceiro de slot, 13,2% sem parceiro, e a cobertura da tabela e 28,2% das
   lacunas (61,4% so em idle).
2. **Os numeros de exatos da H2** (idle/combat_idle/run inflados ~3,5 pontos; sit
   inflado 12x, de 0,0% para 3,6%).
3. **"o baseline transplante vale 20%".** Vale 14,9% quando se tira a arte duplicada.
4. **"a translacao nunca piora".** Piora em 13 pecas de 428, e em 2 delas destroi arte
   que estava exata.
