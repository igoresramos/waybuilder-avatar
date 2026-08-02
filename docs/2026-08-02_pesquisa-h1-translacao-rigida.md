# H1 -- a translacao rigida por slot dispensa a doadora?

Ataque a hipotese da frente de gramatica: que `idle k=1` e apenas `walk k=0`
transladado alguns pixels, com uma tabela `slot -> (dx,dy)` aprendida por
leave-one-out, sem campo de deslocamento nem doadora.

**Veredito: H1 vence para `walk->idle`, `walk->combat_idle` e `walk->run` no
criterio primario (frames exatos). Perde feio para `walk->sit`. E tem um
buraco de cobertura que a translacao nao resolve nem tenta: os slots
inteiramente legados, onde nao ha peca nao-legada nenhuma para treinar a
tabela -- ai o transplante continua sendo a unica opcao, mesmo errando quase
tudo.**

Motor usado sem reimplementacao: `pixels_diferentes`, `sobreposicao`,
`campo_de_deslocamento`, `aplicar_campo` de `/home/igor0/waybuilder-avatar/transplante.py`.
Scripts (nao commitados): `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/h1-translacao/`
(`loader.py`, `core.py`, e os scripts inline que geraram cada `res_*.json`).

## Metodo

`best_translation(origem, destino, radius=4)`: busca exaustiva em
`dy,dx in [-4,4]`, escolhe o deslocamento que minimiza `pixels_diferentes`
depois de transladar a origem (fora da tela sai vazio, sem repetir borda --
o deslocamento maximo medido pela frente de movimento e de 1 px, entao raio 4
sobra). Empate: menor magnitude, depois menor `|dy|+|dx|`.

Tabela por slot: `moda_deslocamento` dos deslocamentos otimos de cada peca do
slot. Validacao **leave-one-out por peca**: para medir a taxa de acerto do
slot X, a peca de teste nunca entra na moda que a classifica -- a moda usa
"os outros" do slot. Slot com 1 peca so fica sem validacao possivel (fica
fora da avaliacao, mas entra na tabela de producao com `n_amostra=1`).

Baseline de comparacao em TODOS os pontos: `transplante` como esta hoje --
doadora do mesmo slot por maior IoU no quadro de origem, campo de
deslocamento raio 6 patch 5, excluindo a propria peca -- recalculado na MESMA
amostra de cada teste (nunca peguei o numero oficial pronto).

## 1. Reproducao independente

Amostra: corpo male, `walk k=0 -> idle k=1`, pecas com as duas camadas
completas em todas as suas layers. **n=428** (de 464 candidatas pela
interseccao de nomes de animacao -- 36 caem porque alguma camada nao tem o
frame apesar do nome da animacao aparecer na lista, ex. menos frames que o
indice pedido).

| metodo | n | exatos | mediana | media |
|---|---|---|---|---|
| translacao rigida por slot (LOO) | 428 | **77,6%** | **0** | 22,3 |
| transplante (baseline, mesmo slot, maior IoU) | 428 | 20,1% | 22,0 | 42,1 |

Bate com a ordem de grandeza que a frente de gramatica reportou (71,9% em
n=463, protocolo levemente diferente de busca de deslocamento) -- reproduzido
de forma independente, com script proprio, em amostra proxima. O baseline
recalculado aqui (20,1%) tambem bate com o oficial do projeto (20,0%, n=250) e
com o da frente de gramatica (18,5%) -- os tres ficam na mesma faixa, o que
da confianca de que a amostra nao esta viesada.

## 2. Onde a translacao falha -- e se o transplante resolve

Taxa de acerto por slot, translacao vs transplante, **no mesmo subconjunto**
(so entram slots com >=2 pecas na amostra, para a LOO fazer sentido -- 44
slots, cobrindo os 428 itens completos):

Slots em 100% de exatos (translacao) -- cabeca e extremidades fixas, 26 deles:
`accessory, bandana, charm, ears, ears_inner, expression, eyebrows,
facial_eyes, fins, furry_ears, furry_ears_skin, hat_accessory, hat_overlay,
hat_trim, head, headcover, horns, mustache, necklace, nose, ponytail,
shoes_toe, shoulders, socks, vest, visor, wrists, necklace` (n de 2 a 32 cada).

Slots parciais: `hat` 92,0% (n=50), `shoes` 91,7% (n=12), `neck` 87,5% (n=8),
`hair` 86,5% (n=89), `beard` 80,0% (n=5), `tail` 80,0% (n=5), `hairextl`
66,7% (n=6), `wings` 60,0% (n=5), `hairextr` 50,0% (n=6), `legs` 40,0% (n=15).

Slots em **0% de exatos** (7, n=2 a 24 cada) -- `armour`(3), `cape`(2),
`clothes`(22), `overalls`(2), `sash_tie`(2), `shield_pattern`(24),
`sleeves`(5). Confirma `clothes` e `shield_pattern` que a gramatica apontou,
e acrescenta mais 5 slots pequenos que tambem zeram.

**O transplante NAO resolve nenhum desses 7**: taxa de exatos do transplante
tambem e 0% em todos, no mesmo subconjunto -- nenhuma doadora recupera um
frame perfeito onde a translacao falha. O que o transplante faz, as vezes, e
reduzir o erro MEDIO (metrica secundaria):

| slot | n | mediana translacao | mediana transplante | quem erra menos |
|---|---|---|---|---|
| clothes | 22 | 102,5 | 47,0 | transplante |
| shield_pattern | 24 | 93,5 | 49,0 | transplante |
| sleeves | 5 | 46,0 | 27,0 | transplante |
| armour | 3 | 35,0 | 62,0 | translacao |
| cape | 2 | 6,0 | 47,5 | translacao |
| overalls | 2 | 76,5 | 134,0 | translacao |
| sash_tie | 2 | 3,5 | 81,5 | translacao |

Ou seja: nos slots onde bracos/tronco se movem de verdade (roupa, manga,
padrao de escudo -- exatamente os casos que a frente de movimento ja tinha
marcado como 0% pro transplante tambem), a doadora ainda ajuda um pouco na
media. Em slots pequenos e idiossincraticos (capa, avental, laco), nem isso --
a translacao erra menos mesmo sem acertar.

## 3. Generaliza para as outras animacoes?

Mesma amostra base (`walk k=0` como origem), quatro destinos, corpo male:

| destino | n | translacao exatos | mediana | media | transplante exatos | mediana | media |
|---|---|---|---|---|---|---|---|
| idle | 428 | **77,6%** | 0,0 | 22,3 | 20,1% | 22,0 | 42,1 |
| combat_idle | 362 | **68,0%** | 0,0 | 59,8 | 16,9% | 32,0 | 56,6 |
| run | 369 | **59,3%** | 0,0 | 71,1 | 13,3% | 37,0 | 73,3 |
| sit | 374 | **0,0%** | 245,0 | 238,7 | 0,5% | 123,0 | 140,7 |

`combat_idle` e `run` sao poses "viradas" (achado da frente de movimento) e a
translacao continua vencendo disparado em frames exatos -- mas repare na
media: em `combat_idle` o transplante tem media MENOR (56,6 contra 59,8).
Isso e o efeito que o slot-a-slot ja mostrou: a maioria das pecas (cabeca,
pes, acessorios fixos) nao gira entre `walk` e `combat_idle`/`run` e a
translacao acerta 100% nelas -- mas as poucas que giram (pernas, roupa)
erram monstruosamente (o pescoco, a perna, o braço saem inteiros do lugar), e
esses poucos erros grandes puxam a media pra cima mais do que os muitos zeros
puxam pra baixo. A mediana (metrica secundaria oficial) continua 0 porque
mais da metade das pecas acerta.

`sit` e o oposto completo: a translacao **perde** do transplante nas tres
metricas. Mover a peca inteira 1-2px na direcao errada (a pose sentada muda a
proporcao do corpo, nao so translada) e pior do que o transplante malfeito
que a frente de movimento ja tinha classificado como "insalvavel" (mediana
123, 0,5% exatos). H1 nao se aplica a `sit`.

## 4. Generalizacao entre corpos

Mesmo protocolo (`walk k=0 -> idle k=1`, LOO por slot), tres corpos:

| corpo | n | translacao exatos | mediana | media | transplante exatos | mediana | media |
|---|---|---|---|---|---|---|---|
| male | 428 | 77,6% | 0 | 22,3 | 20,1% | 22,0 | 42,1 |
| female | 438 | 77,4% | 0 | 18,0 | 19,2% | 22,0 | 41,6 |
| child | 71 | 90,1% | 0 | 3,8 | 26,8% | 11,0 | 20,3 |

Male e female praticamente identicos (77,6% vs 77,4%, diferenca dentro do
ruido). Child sai ainda melhor (90,1%) -- provavelmente pecas menores e mais
simples erram menos pixel absoluto. Nao testei `teen`, `muscular`,
`pregnant`; nao ha razao pra esperar que fujam do padrao dado que male/female
ja convergem, mas isso e extrapolacao, nao medicao.

## 5. O teste que mais importa: pecas legadas de verdade

170 pecas sao legadas (flag `legado` da taxonomia). Verifiquei quantas TEM
`idle` (mesmo faltando as outras animacoes novas) em algum corpo: **50 tem
`idle` e `walk` completos no corpo male** -- essa e a unica evidencia direta
possivel, porque sao pecas REAIS que ja carregam a resposta certa, nao
substitutas.

Protocolo sem vazamento: a tabela slot->(dx,dy) foi treinada **so com as 414
pecas nao-legadas** (as 50 legadas nunca entram no treino), e aplicada nas
50. O mesmo corte alimentou o `baseline_transplante` (pool = as 414
nao-legadas, mesmo slot, maior IoU).

Resultado direto: **36 das 50 (72%) nao tem slot com NENHUMA peca nao-legada
para treinar nem para doar** -- `charm, necklace, cape, weapon, bauldron,
bracers, chainmail, prosthesis_hand, prosthesis_leg, ring, vest, wrists` sao
slots inteiramente legados, confirmando ponto a ponto o achado da frente de
taxonomia (113 das 166 legadas sem par no proprio slot). Nem a translacao nem
o transplante-por-slot tem o que fazer nesses 36 -- os dois ficam sem
resposta, nao so um deles.

Nos 14 restantes que TEM peca nao-legada no slot:

| metodo | n | exatos | mediana | media |
|---|---|---|---|---|
| translacao rigida (treino so em nao-legadas) | 14 | **64,3%** | 0 | 36,0 |
| transplante (pool so nao-legadas, mesmo slot) | 14 | **0,0%** | 56,5 | 74,6 |

Nessa amostra pequena mas real, a translacao nao so generaliza -- ela vence
de forma ainda mais lopsided que na amostra completa (o transplante zera).
Item a item: `legs/legion-skirt` e `legs/plain-skirt` falham (saia nao anda
como calca de armadura -- moda do slot `legs` e "parado", saia nao e), e
`armour/leather` e `neck/scarf` tambem falham. `neck`, `shoes` e `shoulders`
acertam tudo.

**Limite declarado**: n=14 e pequeno, e e uma amostra enviesada -- so cobre
slots que ja tinham parente nao-legado (`legs, armour, neck, shoes,
shoulders`), nao os 36 slots inteiramente legados que sao a maioria do
problema real (`weapon` 26 pecas, `charm` 16, `belt` 8 -- os maiores blocos
legados do acervo, por conta da frente de taxonomia). Para esses, nenhuma
medicao direta e possivel: nao existe peca legada NEM nao-legada que sirva de
verdade fundamental no proprio slot.

## 6. Combinacao: translacao onde ela ganha, transplante onde nao

Regra por slot: comparar taxa de exatos (translacao vs transplante) no mesmo
n; usar quem tem taxa maior; empate (os 7 slots 0%/0%) desempata pela
mediana menor. Aplicado aos 44 slots validados por LOO da amostra `idle`
(n=428): **3 slots trocam para transplante** -- `clothes`, `shield_pattern`,
`sleeves` (os 3 onde o transplante tinha mediana menor na tabela da secao 2).

| | n | exatos | mediana | media |
|---|---|---|---|---|
| translacao pura | 428 | 77,6% | 0 | 22,3 |
| **combinado (translacao + transplante nos 3 slots)** | 428 | **77,6%** | **0** | **16,4** |

A taxa de exatos nao muda (o transplante nunca ganha um frame exato a mais),
mas a media cai 26% (22,3 -> 16,4) porque os erros gigantes de `clothes` e
`shield_pattern` ficam menores. Vale a troca so nesses 3 -- nos outros 4
slots que tambem zeram (`armour, cape, overalls, sash_tie`) a translacao ja
erra menos, entao trocar pioraria.

## 7. Tabela entregue

`/home/igor0/waybuilder-avatar/docs/2026-08-02_h1-tabela-slot.json`

Schema: `{"meta": {...}, "slots": {slot: {dx, dy, n_amostra, taxa_exatos,
taxa_exatos_transplante_no_mesmo_n, mediana_diff_translacao,
mediana_diff_transplante, usar_transplante_no_lugar, validado_por_loo}}}`.

- **80 slots** tem pelo menos 1 peca com `walk`+`idle` completos no corpo
  male (treino de producao usa TODAS essas pecas, nao so LOO, pra estimar o
  `dx,dy` final).
- **44 desses 80** tem >=2 pecas e foram validados por leave-one-out --
  `taxa_exatos`, medianas e `usar_transplante_no_lugar` (bool) preenchidos.
  `usar_transplante_no_lugar=true` em `clothes`, `shield_pattern`, `sleeves`;
  `false` nos outros 41.
- **36 tem so 1 peca na amostra** -- `dx,dy` calculado (e a moda de 1 item
  so, ou seja o proprio deslocamento dela) mas SEM validacao cruzada
  possivel: `taxa_exatos=null`, `usar_transplante_no_lugar=null`. Inclui
  exatamente os slots que a secao 5 mostrou inteiramente legados
  (`weapon, bracers, chainmail, ring, prosthesis_hand, prosthesis_leg,
  bauldron`, etc.) -- ai o `dx,dy` da tabela vem de uma peca legada isolada
  que por acaso tem `idle`, e nao deveria ser usado sem revisao manual.
- **22 dos 102 slots do catalogo ficam FORA da tabela inteira** -- zero
  pecas com `walk`+`idle` completos no corpo male: `apron, backpack,
  backpack_straps, bandages, belt, buckles, cargo, dress, dress_sleeves,
  dress_sleeves_trim, dress_trim, earrings, jacket, jacket_collar,
  jacket_pockets, jacket_trim, quiver, weapon_magic_crystal, wings_dots,
  wings_edge, wound_arm, wound_ribs`.

## Parametros exatos (para virar codigo)

- Deslocamento por peca: busca exaustiva `dy,dx in [-4,4]` minimizando
  `pixels_diferentes(translate(origem,dy,dx), destino)`; empate por menor
  `|dy|+|dx|`, depois menor `|dy|`, depois menor `|dx|`, depois `dy`, depois
  `dx` (ordem determinista).
- Deslocamento por slot: moda dos deslocamentos por peca; empate por menor
  magnitude, depois `(dy,dx)` lexicografico.
- Escopo de aplicacao seguro (`usar_transplante_no_lugar=false`, 41 slots):
  usar a translacao `walk k=0 -> dx,dy` como `idle k=1`. Vale tambem para
  `combat_idle k=1` e `run` com a MESMA logica mas deslocamentos proprios
  (nao medi a tabela slot->(dx,dy) desses dois destinos linha a linha, so
  agregado -- se for pro codigo, repetir a secao 1 com `anim_destino`
  trocado antes de gerar a tabela de producao pra `combat_idle`/`run`).
  Fonte de deslocamento por par de animacao ja existe em
  `2026-08-02_mapa-de-movimento.json`.
- Escopo de exclusao: **nao aplicar em `sit`** -- nenhuma versao (translacao
  ou transplante) produz arte aceitavel (0,0% e 0,5% de exatos, mediana 123
  a 245 pixels errados).
- 3 slots usam transplante em vez de translacao mesmo sendo o par
  `walk->idle`: `clothes`, `shield_pattern`, `sleeves` (a translacao empata
  em 0% de exatos com o transplante, mas erra mais em media).
- 36 slots (listados no JSON com `validado_por_loo:false`) tem `dx,dy` mas
  **nao devem ir pro build sem revisao manual** -- vem de 1 peca so, sem
  nenhuma validacao cruzada.
- 22 slots nao tem solucao nenhuma pela translacao (nem pelo transplante
  restrito ao mesmo slot) -- precisam do criterio "livre por IoU" que a
  frente de taxonomia validou, ou de revisao manual caso a caso.

## Limites declarados

- Toda medicao e no corpo `male`/`female`/`child`, direcao frente (unico
  recorte do acervo); nao testei `teen`, `muscular`, `pregnant`.
- A validacao das secoes 1-4 usa pecas que JA tem a animacao de destino
  (para poder medir erro contra a verdade) -- e por construcao majoritaria
  de pecas nao-legadas, porque sao as que sobram depois do filtro
  `walk+destino completos`. A secao 5 e o unico teste com peca legada de
  verdade, e cobre so 14 casos utilizaveis (36 ficam sem cobertura por falta
  de par de treino no slot, nao por falha do metodo).
- O raio de busca do deslocamento (4px) e maior que o 1px medido pela
  gramatica para a maioria dos slots, mas MENOR que o raio 6 do
  `campo_de_deslocamento`; nao testei raio 5+ -- se algum slot precisar de
  deslocamento maior que 4px ele teria ficado sub-otimizado aqui (mediana
  ainda seria conservadora a favor do transplante nesse caso hipotetico, nao
  a favor de H1).
- `taxa_exatos_transplante_no_mesmo_n` no JSON usa o transplante como esta
  hoje (raio 6, patch 5); nao testei se um transplante com parametros
  diferentes mudaria a secao 2 ou 6.
- Os 36 slots com `n_amostra=1` sao inteiramente nao-validados -- o numero
  no JSON e uma estimativa de ponto unico, nao uma medicao de acerto.
