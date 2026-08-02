# Taxonomia dos assets -- o que separa uma peca da outra

Frente de pesquisa: classificar as 627 pecas do acervo pelos eixos que podem
decidir a escolha da doadora do transplante, e medir qual eixo agrupa pecas
realmente parecidas.

Resposta curta, antes dos numeros: **material nao serve, zPos e um apelido do
slot, e regiao e o unico eixo que cobre o acervo inteiro sem perder qualidade.**
Mas o achado que muda o projeto nao e nenhum dos tres: **113 das 170 pecas
legadas nao tem nenhuma doadora possivel dentro do proprio slot**, e e por isso
que a taxonomia importa.

---

## 1. Como foi medido

- Catalogo: `app/public/avatar/catalogo.json` (627 itens).
- Silhueta de cada peca: **uniao de todas as camadas**, faixa de cor `base`,
  frame **walk k=0**, corpo `male` (ou o primeiro disponivel na ordem female,
  teen, muscular, pregnant, child).
  - A uniao das camadas foi necessaria: lendo so a camada de menor ordem, 93
    pecas (chifres, asas, caudas) saiam com area zero -- a L1 delas e vazia e
    toda a arte esta na L2.
  - Nas pecas cujas camadas tem animacoes desiguais (escudos: L1 sem `walk`), a
    silhueta em walk so inclui as camadas que tem walk -- que e exatamente o que
    a tela mostra nessa animacao.
- IoU: `transplante.sobreposicao`. A matriz 623x623 em lote foi **conferida
  contra a funcao do motor em 200 pares sorteados: 0 divergencias**.
- Pixels errados: `transplante.pixels_diferentes`.
- Amostra da parte descritiva: 627 pecas. Amostra da parte de IoU: **623** (4
  pecas tem silhueta vazia de frente). Amostra da prova de transplante: **493**.

### Baseline oficial, recalculado na minha amostra

| | frames exatos | mediana | media | n |
|---|---|---|---|---|
| baseline oficial declarado | 20,0% | 28 | 42,7 | 250 |
| **baseline recalculado aqui** (doadora do mesmo slot, maior IoU) | **18,7%** | **25,5** | **44,0** | **493** (cobre 460) |
| controle nulo (copiar walk k=0 sem transplantar) | 5,3% | 111,0 | 132,8 | 493 |

A diferenca para o numero oficial vem da amostra: aqui entram todas as 493 pecas
do corpo male que tem walk k=0 e idle k=1 com a peca composta de todas as
camadas, nao 250. O regime e o mesmo.

---

## 2. Os eixos, descritos

### Material declarado (`canais_de_cor[].material`)

| material | pecas | % do acervo | % legadas nele |
|---|---|---|---|
| (nenhum declarado) | 232 | 37,0% | 60,3% |
| cloth | 133 | 21,2% | 10,5% |
| hair | 124 | 19,8% | 0,0% |
| body | 62 | 9,9% | 1,6% |
| metal | 51 | 8,1% | 13,7% |
| body+eye | 8 | 1,3% | 0,0% |
| cloth+metal | 5 | 0,8% | 20,0% |
| metal+wood | 5 | 0,8% | 100,0% |
| wood | 4 | 0,6% | 50,0% |
| cloth+hair | 3 | 0,5% | 0,0% |

**232 pecas (37%) nao declaram material nenhum** -- e nao e aleatorio: 140
delas sao legadas. O eixo material esta ausente justamente onde o problema esta.
Das 170 legadas, so 30 tem material declarado.

### zPos

57 valores distintos na faixa [0, 150]. Concentracao alta: z=120 tem 86 pecas
(83 sao `hair`), z=130 tem 49 (46 sao `hat`), z=112 tem 49 (48 sao
`shield_pattern`).

**zPos e quase um apelido do slot**: 30 dos 57 valores de zPos correspondem a um
unico slot, e 84 dos 102 slots tem um unico zPos. Como eixo independente, ele
carrega pouca informacao nova.

### Regiao do quadro

Rotulagem **puramente geometrica** (`regiao.py`) -- de proposito nao olha slot
nem zPos, senao o eixo viraria copia de outro e a comparacao entre os tres
ficaria viciada. Cortes calibrados na mediana por slot: linha do queixo em y=40,
tornozelo em y=50, tronco central em x=[19,45).

| regiao | pecas | legadas | area mediana |
|---|---|---|---|
| cabeca | 279 | 7 | 218 |
| torso | 134 | 59 | 212 |
| pernas | 65 | 47 | 101 |
| bracos | 60 | 15 | 89 |
| corpo_inteiro | 41 | 21 | 626 |
| maos | 23 | 13 | 56 |
| pes | 21 | 4 | 108 |
| invisivel | 4 | 4 | 0 |

As 4 invisiveis sao `backpack/backpack`, `backpack/jetpack`, `backpack/square-pack`
e `cargo/jetpack-fins`: mochilas, que de frente nao aparecem. Nao ha silhueta a
transplantar nelas -- e o problema delas nao e falta de doadora, e falta de
pixel.

Nao existe regiao "costas" nesta taxonomia: o acervo so tem a direcao frontal, e
capa/asa/mochila aparecem no quadro pelo tamanho que ocupam, nao pela
profundidade. Quem quiser "costas" tem que ler `zPos <= 8`.

### Area, compacidade, tons

| | min | q1 | mediana | q3 | max |
|---|---|---|---|---|---|
| area (pixels opacos) | 2 | 56 | 161 | 287 | 1202 |
| compacidade (area / caixa) | 0,031 | 0,440 | 0,596 | 0,707 | 1,000 |
| tons distintos | 1 | 4 | 6 | 6 | 153 |

A paleta e mesmo estreita: metade das pecas usa 6 tons ou menos, o que confirma
o comentario do motor sobre patch de vizinhanca (um pixel isolado casa com
qualquer outro da mesma cor). Tons por material sao praticamente iguais entre si
(cloth 5, hair 6, metal 6, body 7) -- **cor tambem nao separa material**.

---

## 3. Pergunta 1: pecas do mesmo material se parecem?

IoU medio, intra na diagonal, entre materiais fora dela (n=370 pecas dos 4
materiais principais):

| | body | cloth | hair | metal |
|---|---|---|---|---|
| **body** | **0,213** | 0,024 | 0,140 | 0,183 |
| **cloth** | 0,024 | **0,112** | 0,034 | 0,045 |
| **hair** | 0,140 | 0,034 | **0,299** | 0,212 |
| **metal** | 0,183 | 0,045 | 0,212 | **0,213** |

**Nao. Material falha como criterio de agrupamento.** A diagonal mal se destaca:
`metal` x `metal` da 0,213 e `metal` x `hair` da 0,212 -- estatisticamente a
mesma coisa. `cloth`, o maior grupo com material declarado, tem o menor IoU
intra do acervo inteiro (0,112), abaixo de varios pares entre materiais
diferentes. A razao e obvia depois de vista: material descreve a superficie, e o
transplante so olha para onde o pixel esta.

Controlado pelo tamanho dos grupos (baseline nulo por permutacao, 30 sorteios
mantendo os tamanhos), material rende **1,68x** o acaso -- o menor ganho de
todos os eixos testados.

## 4. Pergunta 2: e zPos? e regiao?

| | bracos | cabeca | corpo_int | maos | pernas | pes | torso |
|---|---|---|---|---|---|---|---|
| **bracos** | **0,189** | 0,009 | 0,054 | 0,108 | 0,021 | 0,004 | 0,066 |
| **cabeca** | 0,009 | **0,202** | 0,109 | 0,000 | 0,000 | 0,000 | 0,048 |
| **corpo_int** | 0,054 | 0,109 | **0,188** | 0,027 | 0,037 | 0,023 | 0,120 |
| **maos** | 0,108 | 0,000 | 0,027 | **0,125** | 0,040 | 0,023 | 0,024 |
| **pernas** | 0,021 | 0,000 | 0,037 | 0,040 | **0,219** | 0,065 | 0,074 |
| **pes** | 0,004 | 0,000 | 0,023 | 0,023 | 0,065 | **0,424** | 0,008 |
| **torso** | 0,066 | 0,048 | 0,120 | 0,024 | 0,074 | 0,008 | **0,204** |

Regiao separa de verdade: a diagonal domina em 6 das 7 linhas, e os zeros fora
dela sao literais (nenhuma peca de cabeca encosta em peca de pernas). A unica
regiao fraca e `maos` (0,125 intra contra 0,108 com bracos) -- a fronteira
antebraco/mao e mesmo difusa.

zPos tem o maior IoU intra bruto (0,442), mas isso e efeito de ter 57 grupos:
grupo pequeno e parecido por construcao. Ver a proxima secao.

## 5. Pergunta 3: qual dos tres eixos agrupa melhor

IoU medio global (par ao acaso entre as 623 pecas, 193.753 pares): **0,0852**.
IoU do melhor par sem restricao nenhuma: mediana 0,802.

`nulo` = mesmo eixo com os rotulos embaralhados, mantendo os tamanhos dos grupos
(media de 30 sorteios). `ganho` = intra / nulo, e a unica leitura justa entre
eixos com numeros de grupos diferentes.

| eixo | grupos | cobertura | IoU intra | nulo | **ganho** | melhor par intra (mediana) | coincide com a busca livre |
|---|---|---|---|---|---|---|---|
| slot | 102 | 623/623 | 0,4846 | 0,0850 | **5,70x** | 0,802 | 80,2% |
| zPos | 57 | 623/623 | 0,4419 | 0,0851 | **5,20x** | 0,793 | 77,5% |
| regiao + faixa zPos | 58 | 623/623 | 0,3181 | 0,0854 | 3,72x | 0,789 | 77,9% |
| grupo (arvore) | 11 | 623/623 | 0,2718 | 0,0855 | 3,18x | 0,792 | 85,4% |
| faixa zPos (10) | 16 | 623/623 | 0,2505 | 0,0854 | 2,93x | 0,787 | 81,5% |
| regiao + material | 32 | 395/623 | 0,3450 | 0,1213 | 2,84x | 0,817 | 73,3% |
| **regiao** | 7 | 623/623 | 0,2031 | 0,0853 | **2,38x** | 0,800 | **91,0%** |
| **material** | 9 | **395/623** | 0,2025 | 0,1207 | **1,68x** | 0,817 | 79,2% |

Ordem pelo ganho: **zPos (5,20x) > regiao (2,38x) > material (1,68x)**.

Mas o ganho do zPos e emprestado: ele so bate o slot porque e o slot com outro
nome (30/57 valores mapeiam para um slot unico). E a coluna que interessa para a
aplicacao e a ultima -- com quanta frequencia o melhor par dentro do grupo e
tambem o melhor par do acervo inteiro. Nela **regiao ganha de todos com 91,0%,
usando apenas 7 grupos e cobrindo 100% do acervo**. Material cobre 63%.

### A prova pratica

Nao adianta IoU se a arte nao melhora. Rodei o transplante de verdade
(`campo_de_deslocamento` -> `aplicar_campo`), doadora walk k=0 -> idle k=1
aplicado a alvo walk k=0, comparado com alvo idle k=1, na mesma amostra de 493
pecas. Nenhuma peca e doadora de si mesma.

| criterio da doadora | cobre | **frames exatos** | mediana | media |
|---|---|---|---|---|
| **mesmo slot (baseline)** | 460/493 | **18,7%** | **25,5** | **44,0** |
| mesma regiao | 493/493 | 18,5% | **23,0** | 41,3 |
| mesmo zPos exato | 484/493 | 18,2% | 25,0 | 43,9 |
| **mesmo material** | 372/493 | **14,2%** | **33,0** | 52,2 |
| livre (todo o acervo por IoU) | 493/493 | 18,5% | **22,0** | **39,7** |
| controle nulo (nao transplantar) | 493/493 | 5,3% | 111,0 | 132,8 |

Tres leituras, todas honestas:

1. **Material perdeu, e feio.** Restringir a doadora ao mesmo material derruba
   os frames exatos de 18,7% para 14,2% e piora a mediana de 25,5 para 33. E a
   unica restricao que fica abaixo do baseline nas tres metricas.
2. **Regiao empata com slot e cobre mais.** 18,5% contra 18,7% de exatos (33
   pecas de diferenca na amostra, dentro do ruido), mediana melhor (23 contra
   25,5), e cobre 493/493 contra 460/493.
3. **Nenhuma restricao bate a busca livre por IoU.** Soltar a doadora para o
   acervo inteiro da a melhor mediana (22) com o mesmo percentual de exatos.
   **Restringir por eixo taxonomico nao adiciona nada ao IoU** -- o IoU ja sabe
   sozinho o que a taxonomia tentaria dizer.

O valor da taxonomia, portanto, nao e prescritivo. E diagnostico: ela diz onde o
IoU vai falhar.

## 6. Pergunta 4: pecas orfas

Duas nocoes de orfa, e a segunda e a que dói.

**(a) Orfa de silhueta** -- nao se parece com nada no acervo. Poucas: a mediana
do melhor par do acervo e 0,802, e so **10 pecas tem melhor par abaixo de 0,20**
e 27 abaixo de 0,30. As piores:

| peca | melhor IoU do acervo | com |
|---|---|---|
| wings_dots/monarch-wings-dots | 0,049 | wings/monarch-wings |
| hairtie_rune/hair-tie-rune | 0,056 | hairtie/hair-tie |
| wound_eye_left/left-eye | 0,154 | mustache/handlebar-mustache |
| wound_eye_right/right-eye | 0,154 | mustache/handlebar-mustache |
| mustache/handlebar-mustache | 0,167 | mustache/mustache |
| hat_trim/tricorne-lieutenant-trim | 0,183 | hat/tricorne |
| cape_trim/cape-trim | 0,186 | shoes/revised-shoes |
| jacket_trim/frock-coat-buttons | 0,190 | jacket_trim/frock-coat-lace |
| hat_buckle/wizard-hat-buckle | 0,194 | wrinkles/wrinkles |
| hat_trim/tricorne-stitching | 0,198 | hat_trim/tricorne-thatching |

Padrao claro: sao pecas **minusculas** (area 2 a 56 px) -- runas, fivelas,
botoes, pontos de asa. IoU e uma metrica cruel com area pequena: dois pixels de
diferenca ja derrubam a fracao. Para essas, escolher doadora por IoU e
loteria.

**(b) Orfa de doadora** -- e legada e nao tem de quem herdar. **113 das 166
legadas medidas nao tem NENHUMA peca nao-legada no proprio slot.** Slots
inteiros sao legados de ponta a ponta: `weapon` (26), `charm` (16), `belt` (8),
`jacket` (6), `necklace` (5), `vest` (4), `dress` (4), `apron` (4), `bracers`,
`chainmail`, `quiver`, `wrists`, `earrings`, `cape`, `arms`... Para essas 113 o
criterio "doadora do mesmo slot" simplesmente **nao produz resposta**.

Restringindo as doadoras a pecas nao-legadas, 37 das 166 legadas tem melhor
doadora possivel com IoU < 0,30, e 96 com IoU < 0,50. Quase todo o slot `weapon`
esta nessa faixa (armas sao formas diagonais longas, sem analogo no acervo).

## 7. O que fazer com as 113

Para as 113 orfas de slot, medi o melhor IoU alcancavel sob cada restricao
(doadoras = 457 pecas nao-legadas):

| restricao | cobre | IoU mediano | IoU medio | >= 0,50 | coincide com a livre |
|---|---|---|---|---|---|
| livre (sem restricao) | 113/113 | 0,409 | 0,433 | 34,5% | 100% |
| **mesma regiao** | **113/113** | **0,356** | 0,382 | 29,2% | **66,4%** |
| mesma regiao + faixa zPos | 24/113 | 0,248 | 0,286 | 16,7% | 41,7% |
| mesmo material | 14/113 | 0,296 | 0,318 | 14,3% | 35,7% |
| faixa zPos (10) | 45/113 | 0,194 | 0,214 | 11,1% | 22,2% |
| **mesmo zPos exato** | 30/113 | **0,021** | 0,092 | **0,0%** | 3,3% |

**zPos colapsa completamente aqui** (mediana 0,021): como zPos e sinonimo de
slot, e o slot inteiro e legado, sobram como candidatas so as poucas pecas de
outro slot que dividem o mesmo z por acidente -- e elas nao tem nada a ver com a
alvo. Este e o argumento mais forte contra usar zPos como criterio.

Os pares que a busca livre encontra sao bons e fazem sentido visual:

```
cargo/ore            <- hat/kettle-helm                    IoU=0,808
belt/leather-belt    <- sash/obi                           IoU=0,792
vest/vest            <- armour/legion                      IoU=0,792
jacket/tabard        <- armour/plate                       IoU=0,777
jacket/santa-coat    <- clothes/longsleeve                 IoU=0,703
arms/armour          <- sleeves/original-longsleeves-overlay IoU=0,697
apron/overskirt      <- legs/hose                          IoU=0,694
chainmail/chainmail  <- clothes/longsleeve                 IoU=0,681
```

E os que nao fazem:

```
weapon/scythe        <- wings/lizard-wings                 IoU=0,150
weapon/rapier        <- legs/pantaloons                    IoU=0,163
weapon/cane          <- shield/heater-shield-base          IoU=0,176
cape_trim/cape-trim  <- shoes/revised-shoes                IoU=0,186
```

Migracoes recorrentes que a busca livre descobre sozinha: `charm -> neck` (11x),
`weapon -> legs` (8x), `belt -> sash` (6x), `jacket -> clothes` (5x),
`necklace -> neck` (5x).

---

## 8. A tabela

Salva em:

```
/home/igor0/waybuilder-avatar/docs/2026-08-02_taxonomia.json
```

347 KB, **627 pecas**, chaveada pelo `id` do catalogo. Cada entrada tem:

```json
"jacket/tabard": {
  "material": null, "materiais": [],
  "zPos": 55, "zPos_camadas": [55],
  "regiao": "torso", "area": 309, "compacidade": 0.7725, "tons": 5,
  "bbox": [0.5, 0.3438, 0.8125, 0.6562], "bbox_px": [32, 22, 52, 42],
  "centroide": [0.6605, 0.4926], "lateralidade": 0.0,
  "slot": "jacket", "grupo": "Torso", "categoria": "torso",
  "legado": true, "n_camadas": 1,
  "corpo_medido": "male", "anim_medida": "walk"
}
```

Campos alem dos pedidos, porque as outras frentes vao precisar: `legado` (a
peca precisa ou nao de transplante), `bbox_px` (sem normalizar, para recorte
direto), `lateralidade` (fracao da area fora do tronco central -- e o que separa
braco/mao de torso/perna) e `anim_medida` (rastreabilidade).

Scripts que a produziram, se alguem quiser refazer:
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/taxonomia/`
(`medir.py` -> `regiao.py` -> `analise2.py` -> `analise3.py` -> `prova.py` ->
`resumo.py`).

## 9. Limites desta medicao

- Tudo medido na direcao frontal, corpo `male`. Nao verifiquei se a taxonomia se
  sustenta em `female`/`child`, onde a proporcao do corpo muda.
- A regiao usa a faixa de cor `base`. Pecas cuja `base` nao e a paleta mais
  representativa podem ter silhueta ligeiramente diferente em outras cores.
- A fronteira `maos`/`bracos` e fraca (IoU intra 0,125 contra 0,108 cruzado).
  Se alguma frente depender dessa distincao, ela precisa ser refeita.
- A prova de transplante mediu **1 par de frames** (walk k=0 -> idle k=1). Nao
  testei se a ordem dos eixos muda em `sit`, `run` ou `combat_idle`.
- O ganho sobre o baseline nulo usa 30 permutacoes; com grupos pequenos
  (`wood`, n=4) o nulo e ruidoso.
