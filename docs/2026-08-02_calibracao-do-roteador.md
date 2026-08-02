# Calibração do roteador por rigidez e reconciliação da contagem de lacunas

Data: 2026-08-02
Escopo: os dois únicos itens que ficaram em aberto na pesquisa de transplante (seção 7 de
`2026-08-02_PESQUISA-transplante.md`): calibrar os parâmetros chutados do roteador por
rigidez (recomendação 3) e reconciliar as três contagens de lacunas em circulação.

Motor usado sem reimplementação: `transplante.py` via `lib.py` do ataque (compõe todas as
camadas por zPos antes de medir — corrige o vazamento de câmera vazia do Ataque 1b).
Scripts em `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/calibracao/`.

---

## Tarefa 1 — calibração do roteador

### Desenho da medição

O roteador decide, por peça legada e por slot: **transladar** (usar o deslocamento-moda
das peças de treino do slot) ou **não mexer** (copiar `walk k=0`). A recomendação 3 exige
que o treino venha só de peças **não-legadas** (as que já têm as 5 animações) — é
literalmente o que testei, não usei nenhuma peça legada como treino de outra.

**População de teste:** peças de formato legado que **já têm idle medido** no corpo
`male` — a única população onde dá para saber se o roteador acertou ou errou, porque tem
o frame verdadeiro. `pool(walk0,idle1) = 464`, `completas (treino) = 388`,
**`legadas com idle = 76`** (bate exatamente com o Ataque 6.4 da pesquisa).

**Validação:** LOO por construção — treino é sempre um subconjunto de `completas`, e a
peça testada é sempre `legada`, logo nunca entra no próprio treino.

Para cada peça de teste: `n_treino` = peças completas do mesmo slot; se `n_treino >=
n_min` e a fração que concorda no `(dy,dx)` ótimo próprio (moda) `>= frac_min`, aplica a
translação com o deslocamento da moda; senão, não mexe. Comparo sempre contra o "não
mexer" daquela peça especificamente (não contra um baseline global) — é essa comparação
que define regressão.

### Matriz completa (n=76, corpo male, walk k0→idle k1)

Controle (não mexer em nada, n=76): **5,3% exatos, mediana 70**.

| n_min | frac_min | exatos | exatos % | regressões | regr. sobre exata | aplicar | não mexer | mediana |
|---|---|---|---|---|---|---|---|---|
| 1 | 0,50 | 11 | 14,5 | 0 | 0 | 15 | 61 | 56,0 |
| 1 | 0,60 | 11 | 14,5 | 0 | 0 | 15 | 61 | 56,0 |
| 1 | 0,70 | 11 | 14,5 | 0 | 0 | 15 | 61 | 56,0 |
| 1 | 0,80 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 1 | 0,90 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 1 | 1,00 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 2 | 0,50 | 11 | 14,5 | 0 | 0 | 15 | 61 | 56,0 |
| 2 | 0,60 | 11 | 14,5 | 0 | 0 | 15 | 61 | 56,0 |
| **2** | **0,70** | **11** | **14,5** | **0** | **0** | **15** | **61** | **56,0** |
| 2 | 0,80 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 2 | 0,90 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 2 | 1,00 | 10 | 13,2 | 0 | 0 | 14 | 62 | 56,0 |
| 3 | 0,50 | 9 | 11,8 | 0 | 0 | 12 | 64 | 62,0 |
| 3 | 0,60 | 9 | 11,8 | 0 | 0 | 12 | 64 | 62,0 |
| 3 | 0,70 | 9 | 11,8 | 0 | 0 | 12 | 64 | 62,0 |
| **3** | **0,80 (chute)** | **8** | **10,5** | **0** | **0** | **11** | **65** | **62,0** |
| 3 | 0,90 | 8 | 10,5 | 0 | 0 | 11 | 65 | 62,0 |
| 3 | 1,00 | 8 | 10,5 | 0 | 0 | 11 | 65 | 62,0 |
| 4 | 0,50 | 5 | 6,6 | 0 | 0 | 7 | 69 | 70,0 |
| 4 | 0,60 | 5 | 6,6 | 0 | 0 | 7 | 69 | 70,0 |
| 4 | 0,70 | 5 | 6,6 | 0 | 0 | 7 | 69 | 70,0 |
| 4 | 0,80 | 4 | 5,3 | 0 | 0 | 6 | 70 | 70,0 |
| 4 | 0,90 | 4 | 5,3 | 0 | 0 | 6 | 70 | 70,0 |
| 4 | 1,00 | 4 | 5,3 | 0 | 0 | 6 | 70 | 70,0 |
| 5 a 10 | qualquer | 4 | 5,3 | 0 | 0 | 6 | 70 | 70,0 |

(as linhas de `n_min` 5, 6, 8, 10 são idênticas às de `n_min=4/frac>=0,80` — a partir daí
nenhum slot da amostra tem treino suficiente para mudar a decisão; matriz completa das 48
combinações em `docs/2026-08-02_roteador-parametros.json` e no `matriz.json` do scratchpad).

### Achado central: regressão zero em toda a grade

Nas 48 combinações testadas — incluindo a mais permissiva, `n_min=1, frac_min=0,50` —
**nenhuma peça piorou em relação a não mexer**. Isso é diferente do que a pesquisa original
mediu (13 regressões em 428, 2 delas destruindo peça exata) porque lá o treino vinha de
**qualquer** peça do slot, legada ou não. Restringindo o treino a peças não-legadas
(exatamente como a recomendação 3 pede), a razão aparece nos dados: nas 4 peças legadas
que já saíam exatas sem mexer (`legs/armour`, `prosthesis_leg/peg-leg`, `shoes/armour`,
`shoes/hoofs`), o treino não-legado do slot também concorda em `(0,0)` — moda 1,0 de
concordância nos 3 slots com treino disponível. O roteador não as toca porque o próprio
treino diz "não mexe".

**Isso não é garantia geral** — é o que aconteceu nestas 76 peças. Um slot em que o treino
completo tem moda `(-1,0)` e uma peça legada específica é estaticamente `(0,0)` (o caso
`hat/tiara`/`hat/formal-bowler-hat` do Ataque 4c, mas lá com treino contaminado por peças
legadas) continua teoricamente possível e não foi observado porque não caiu na amostra.

Detalhe do que aconteceu no ramo "aplicar" em `n_min=1, frac=0,50` (15 peças, cobre todos
os empatados até frac=0,70):

| resultado | n | peças |
|---|---|---|
| melhorou (ficou exata ou com menos erro) | 9 | armour/leather, neck/capeclip, neck/capetie, neck/cravat, neck/jabot, neck/scarf, shoulders/legion, shoulders/mantal, tail/wolf-tail |
| igual (moda do slot = (0,0), sem efeito) | 6 | legs/armour, legs/legion-skirt, legs/plain-skirt, legs/slit-skirt, shoes/armour, shoes/hoofs |
| piorou | 0 | — |

### O chute (3, 80%) não sobrevive

Contra o par recomendado, o chute perde nas duas métricas que importam e empata na
terceira: **10,5% contra 14,5% de exatos**, mesmas 0 regressões, mediana pior (62 contra
56). É estritamente dominado — não há trade-off, o chute é só mais conservador sem
comprar nada com isso, nesta amostra.

### Validação em outros 5 corpos (n=392 combinado)

Não fazia parte do pedido, mas o custo era baixo e a pergunta "isso generaliza?" é óbvia
demais para não checar. Mesmo par, mesmo método, `(2, 0,70)` contra o chute `(3, 0,80)`:

| corpo | n | exatos (2,0,70) | exatos (3,0,80) | regressões (ambos) |
|---|---|---|---|---|
| female | 86 | 9,3% | 5,8% | 0 |
| teen | 83 | 10,8% | 6,0% | 0 |
| muscular | 68 | 11,8% | 7,4% | 0 |
| pregnant | 71 | 8,5% | 4,2% | 0 |
| child | 8 | 12,5% | 12,5% (empate, n pequeno) | 0 |
| **pooled 6 corpos** | **392** | **11,0%** | **6,9%** | **0 / 0** |

Ressalva: os 6 corpos não são amostras independentes (a mesma peça aparece em vários
corpos com arte distinta) — é validação de estabilidade, não uma segunda medição
independente com n=392.

### Recomendação

**`n_min = 2`, `frac_min = 0,70`.**

Pelo critério de desempate literal (a: zero regressão sobre exata → b: mais exatos → c:
menos regressões → d: mais simples), o vencedor no male sozinho é um empate de 6 pares:
`(1,0,50)` a `(2,0,70)` — todos produzem exatamente a mesma decisão de roteamento (15
aplicar, 61 não-mexer, 11 exatos, 0 regressões). Escolho `(2, 0,70)` dentro desse empate,
não porque meça melhor — não mede, é idêntico — mas porque `n_min=1` deixa uma única peça
de treino decidir o slot inteiro, o que não é "concordância" nenhuma matematicamente
(fração de 1 elemento é sempre 100%). Isso é uma preferência de robustez para slots fora
da amostra, não um resultado medido; sinalizo explicitamente que é opinião, não dado. A
validação nos outros 5 corpos reforça a escolha porque `(2,0,70)` continua no topo ou
empatado no topo em todos eles.

**O chute (3, 80%) não sobrevive.** Perde em exatos e mediana, empata em regressões
(zero nos dois), em 6 corpos e n=392 combinado.

---

## Tarefa 2 — reconciliação da contagem de lacunas

Três números, três unidades de contagem diferentes — todos reproduzidos exatamente a
partir do próprio `preencher.py`, do `preenchimento.json` e do `catalogo.json`, nenhum
chutado.

### A contagem canônica: **2.864 células / 11.495 frames**

**Unidade:** `(item, corpo, animação)` — a peça inteira, com todas as camadas compostas,
contada uma vez por combinação; animações-alvo `{idle, combat_idle, sit, run}` (walk
excluído — walk é a animação-base, presente em praticamente todo o acervo); corpo só
conta se **todas** as camadas do item existirem naquele corpo (existência por
interseção, não por "qualquer camada").

Reproduzido com script direto sobre `catalogo.json`, sem depender de nenhum artefato de
frente anterior:

```
grossa_raw (item, corpo, anim), todos os 627 itens: 2999 células (com walk)
  sem walk: 2864 células  <-- CANÔNICO
  frames (idle=2, combat_idle=2, sit=3, run=8): 11495  <-- CANÔNICO
```

Bate campo a campo com o Ataque 6.1 da pesquisa (idle 365, combat_idle 877, run 829, sit
793 → soma 2864).

### Por que 2.041 é menor: escopo mais estrito, mesma unidade

`2.041` é o mesmo cálculo (mesma unidade, mesmas 4 animações, mesmo critério de "corpo
existe por completo"), **restrito aos 170 itens com `taxonomia.pecas[id].legado = true`**
— a lista curada de peças "de formato legado" (a que a pesquisa e este pedido chamam de
"as 170 peças legadas"). Reproduzido:

```
170 itens legado=true x 6 corpos x {idle,combat_idle,sit,run}: 2041 células, 7956 frames
```

Bate exatamente. **2864 − 2041 = 823** células vêm de itens que **não** estão na lista
curada dos 170, mas ainda assim têm um buraco pontual em 1+ animação (por exemplo, uma
peça com as 5 animações completas em `male` mas sem `sit` em `child`). Verificado
diretamente: rodando o mesmo cálculo só nos itens fora da lista `legado=true`, dá
exatamente 823. **Não é erro — é que 2.041 mede um subconjunto menor e mais estrito da
mesma coisa que 2.864 mede.**

### Por que 3.666 é maior: unidade mais fina, e é saída, não lacuna

`3.666` vem direto do `preencher.py` (`len(registro)` em `preenchimento.json`), e difere
em dois eixos ao mesmo tempo, não um só:

1. **Unidade mais fina** — `(item, corpo, CAMADA, animação)`, sem colapsar camadas
   múltiplas da mesma peça na mesma célula. `preencher.py` gera um PNG por camada, então
   uma peça com 2 camadas que faltam a mesma animação em conjunto vira 2 registros, não
   1. Matematicamente, a soma das lacunas por camada é a mesma coisa que a lacuna por
   interseção (De Morgan: `ANIMS − ∩camada = ∪(ANIMS − camada)`), e isso bate
   perfeitamente nos dados: a contagem bruta por camada, ANTES de excluir o que não achou
   doadora, dá **3.794** tentativas — e a versão colapsada por célula dessas mesmas
   3.794 tentativas dá **exatamente 2.999** (2.864 sem walk + 135 de walk), confirmando
   que é a mesma lacuna, só contada em granularidade diferente.
2. **Inclui walk** (135 células/tentativas) — peças que também não têm a animação
   `walk` propriamente dita.
3. **É contagem de sucesso, não de lacuna** — `3.666 = 3.794 tentativas − 128
   combinações camada×animação sem doadora nem fallback de corpo`. Ou seja, 3.666 é
   "quantas lacunas o pipeline preencheu", não "quantas lacunas existem".

```
fina_raw (item,corpo,camada,anim), TODOS os 627 itens: 3794 tentativas
  preenchidas com sucesso (via 'analoga' + via 'corpo'): 2103 + 1563 = 3666  <-- bate com preenchimento.json
  sem doadora ('sem saida'): 128
grossa_raw colapsada por célula (mesmas 3794 tentativas): 2999 (= 2864 sem-walk + 135 walk)
```

### Tabela-resumo

| número | unidade | escopo (itens) | animações | inclui walk | é lacuna ou saída |
|---|---|---|---|---|---|
| **2.864 / 11.495 frames** | item×corpo×animação (peça composta) | todos os 627 | idle/combat_idle/sit/run | não | lacuna real (canônico) |
| 2.041 / 7.956 frames | item×corpo×animação (peça composta) | só os 170 `legado=true` | idle/combat_idle/sit/run | não | lacuna real, subconjunto de 2.864 |
| 3.666 | item×corpo×**camada**×animação | todos os 627 | idle/combat_idle/**walk**/sit/run | sim | **saída preenchida com sucesso** (não é lacuna) |

Nenhuma das três está "errada" — nenhuma foi reproduzida antes deste documento porque
cada frente tinha assumido a unidade das outras sem verificar.

---

## O que virar código

1. **Roteador por rigidez, parâmetros calibrados:**
   `n_min_treino_nao_legado = 2`, `fracao_min_concordancia = 0,70`.
   Treino = peças completas (5 animações) do mesmo slot/corpo. Se `n_treino >= 2` e
   `>= 70%` delas concordam na moda do `(dy,dx)` ótimo próprio → aplicar translação com
   esse deslocamento. Caso contrário → copiar `walk k=0` sem alteração.
   Efeito medido: 14,5% de exatos contra 10,5% do chute (3, 80%), 0 regressões nos dois,
   validado em 6 corpos (pooled n=392: 11,0% contra 6,9%, 0 regressões nos dois).
   Arquivo: `docs/2026-08-02_roteador-parametros.json`.

2. **Contagem canônica de lacunas para qualquer projeção de entrega:**
   **2.864 células / 11.495 frames** (item×corpo×animação, `{idle,combat_idle,sit,run}`,
   corpo exigindo existência completa em todas as camadas). Não usar 3.666 (é saída do
   pipeline, não lacuna) nem 2.041 sozinho para dimensionar o total (é o subconjunto
   curado dos 170 itens "legado"; útil para relatar especificamente esse recorte, não
   para o total).

---

## Amostra e limites, declarados

- Tarefa 1: medido em `male` (n=76 peças legadas com idle medido, a população inteira
  disponível — não é uma subamostra escolhida) para a matriz principal; validação
  cruzada em 5 outros corpos (n=392 combinado, amostras correlacionadas entre si, não
  independentes).
- Zero regressões é o que foi medido nas 76+392 peças testadas, não uma prova de que o
  roteador nunca pode regredir — o mecanismo teórico de regressão (moda do slot
  discordando do ótimo de uma peça estaticamente `(0,0)`) continua existindo e não foi
  descartado, só não apareceu nesta amostra.
- Tarefa 2: as três contagens foram recalculadas do zero a partir de `catalogo.json`,
  `taxonomia.json` e `preenchimento.json` — nenhum número veio de memória ou de
  extrapolação.
