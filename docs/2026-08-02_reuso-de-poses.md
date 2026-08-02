# Reuso de poses: viabilidade de remapeamento deterministico (idle/combat_idle/sit/run)

Medicao pura. Comparacao pixel a pixel (hash MD5 de blocos RGBA 64x64) entre frames
das animacoes novas (`idle`, `combat_idle`, `sit`, `run`) e frames das animacoes
antigas presentes em pecas legadas (`spellcast`, `thrust`, `walk`, `slash`, `shoot`,
`hurt`, `backslash`, `halfslash`, `climb`, `emote`, `jump`).

Fonte: `/home/igor0/waybuilder-avatar/fontes/lpc/spritesheets/`
Script: gerado ad-hoc em scratchpad, nao commitado (execucao registrada abaixo).
Corpos testados: `body/bodies/male`, `body/bodies/female`, `body/bodies/teen`.

## 1) Frames por animacao (corpo `male`, mesma contagem em `female` e `teen`)

| Animacao | Linhas (direcoes) | Colunas | Frames totais |
|---|---|---|---|
| idle | 4 | 2 | 8 |
| combat_idle | 4 | 2 | 8 |
| sit | 4 | 3 | 12 |
| run | 4 | 8 | 32 |
| spellcast | 4 | 7 | 28 |
| thrust | 4 | 8 | 32 |
| walk | 4 | 9 | 36 |
| slash | 4 | 6 | 24 |
| shoot | 4 | 13 | 52 |
| hurt | 1 | 6 | 6 |
| backslash | 4 | 13 | 52 |
| halfslash | 4 | 6 | 24 |
| climb | 1 | 6 | 6 |
| emote | 4 | 3 | 12 |
| jump | 4 | 5 | 20 |

`hurt` e `climb` so tem 1 linha (sem variacao por direcao).

## 2) Identidade exata (hash igual) -- corpo `male`

| Animacao nova | Frames com match exato | Taxa |
|---|---|---|
| idle | 4 / 8 | 50% |
| combat_idle | 0 / 8 | 0% |
| sit | 0 / 12 | 0% |
| run | 0 / 32 | 0% |

Os 4 matches exatos de `idle` sao os frames de coluna 0 (primeiro frame, pose parada)
de cada uma das 4 direcoes:

| idle (dir, col) | Match exato em |
|---|---|
| n, 0 | spellcast (n, 0) |
| w, 0 | spellcast (w, 0) |
| s, 0 | spellcast (s, 0), walk (s, 0), slash (s, 0) |
| e, 0 | spellcast (e, 0) |

Os frames de coluna 1 de `idle` (pose de "respiracao") NAO tem match exato em
nenhuma animacao antiga -- ver quase-identidade no item 3.

`combat_idle`, `sit` e `run` nao tem NENHUM frame com hash identico em nenhuma
animacao antiga, em nenhuma das 4 direcoes.

## 3) Quase-identidade (melhor par, diferenca em pixels de 4096 por frame)

Comparacao restrita a mesma direcao (linha). Resumo por animacao (corpo `male`):

| Animacao | Faixa de pixels diferentes (melhor par por frame) | % do frame |
|---|---|---|
| idle (frames sem match exato, coluna 1) | 127 a 168 | 3,1% a 4,1% |
| combat_idle | 252 a 367 | 6,2% a 9,0% |
| sit | 345 a 529 | 8,4% a 12,9% |
| run | 357 a 471 | 8,7% a 11,5% |

Nao ha nenhum par na faixa "2 ou 3 pixels" mencionada como limiar de usabilidade.
O melhor caso fora dos matches exatos (`idle` col.1) ja fica acima de 100 pixels
diferentes por frame -- claramente perceptivel, nao e reuso seguro.
`combat_idle`, `sit` e `run` ficam na faixa de centenas de pixels diferentes por
frame (6% a 13% da imagem): poses genuinamente distintas, sem pose antiga
equivalente no acervo.

Dados completos (todas as direcoes e colunas, corpo `male`) preservados em
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/male_out.txt`
(fora do path do projeto -- artefato de trabalho da medicao, nao arte, nao precisa
ir para o repo).

## 4) Repeticao entre corpos (`female`, `teen`)

| Corpo | idle: match exato | idle: melhor quase-match (col. 0) | combat_idle / sit / run: match exato |
|---|---|---|---|
| male | 4/8 (col. 0, todas direcoes) | -- (ja exato) | 0/0/0 |
| female | 0/8 | 13 a 20 pixels diferentes (spellcast/jump col. 0) | 0/0/0 |
| teen | 0/8 | 100 a 154 pixels diferentes (emote/jump col. 0) | 0/0/0 |

A hipotese NAO se sustenta de forma consistente entre corpos. Em `male` o frame
0 de `idle` e byte-a-byte identico ao frame 0 de `spellcast`/`walk`/`slash`
(remapeamento realmente deterministico, zero risco). Em `female` a mesma pose
quase bate (13 a 20 pixels de 4096, ~0,3% a 0,5%) mas NAO e hash-identica --
provavel diferenca de 1 pixel de antialiasing/sombra, o que quebra o criterio
"deterministico" pedido. Em `teen` a diferenca ja sobe para 100+ pixels (2,4%
a 3,8%), fora de qualquer margem de "quase-identico".
`combat_idle`, `sit` e `run` repetem o padrao de nao-match em todos os 3 corpos:
zero identidade exata, diferencas de centenas de pixels no melhor caso.

## 5) Validacao com roupa real (nao so corpo nu)

Pecas verificadas (torso legado, tem `walk.png` mas nao tem `idle.png`):

- `torso/jacket/santa/male`
- `torso/clothes/longsleeve/formal/male`
- `torso/waist/belt_leather/male`

Todas as 3 tem `spellcast.png` -- a animacao cujo frame de coluna 0 e o match
exato de `idle` no corpo `male`. Contagem de pixels com alpha > 0 no frame
`spellcast` coluna 0 (o frame que seria reaproveitado para `idle`), por direcao:

| Peca | dir n | dir w | dir s | dir e |
|---|---|---|---|---|
| santa (jacket) | 501/4096 | 287/4096 | 459/4096 | 287/4096 |
| longsleeve formal | 418/4096 | 237/4096 | 369/4096 | 237/4096 |
| belt_leather | 68/4096 | 45/4096 | 72/4096 | 45/4096 |

Nas 3 pecas ha pixel de roupa desenhado no frame que seria reaproveitado --
o remapeamento de `idle` (para corpo `male`, via `spellcast` col. 0) entregaria
arte de roupa visivel, nao um frame vazio. Esta parte da hipotese se confirma
para as pecas testadas.

Nao foi possivel testar o mesmo para `combat_idle`/`sit`/`run` porque, no proprio
corpo (item 2 e 4), essas 3 animacoes nao tem NENHUM frame equivalente exato --
nao ha frame-alvo valido no corpo para remapear, entao a questao "a roupa tem
esse frame" fica sem objeto.

## Verificacao complementar: sobreposicao de faltas (pastas-fonte)

Medi diretamente nas pastas de `spritesheets/` (nivel de arquivo-fonte, unidade
diferente dos "627 itens" do catalogo do app -- aqui sao 5128 pastas-folha com
PNG, todas as categorias LPC, nao so as usadas pelo app):

| Faltando | Pastas |
|---|---|
| idle | 4311 / 5128 |
| combat_idle | 4416 / 5128 |
| sit | 4374 / 5128 |
| run | 4394 / 5128 |
| pastas onde SO falta `idle` (as outras 4 presentes) | 0 |
| pastas incompletas que TAMBEM faltam `combat_idle` | 4416 / 4418 (99,95%) |

Ou seja: praticamente toda pasta que falta `idle` tambem falta `combat_idle`.
Isso e consistente com os numeros do catalogo do app (169 dos 170 itens
incompletos faltam `combat_idle`). Como `combat_idle` nao tem nenhum frame
remapeavel (item 2 e 3), nenhuma peca fica "completa" so remapeando `idle`.

## Veredito

**PARCIAL, e o resultado pratico e proximo de zero.**

- `idle`: remapeamento deterministico (hash identico, zero risco) e viavel
  SOMENTE para o corpo `male`, e somente 4 dos 8 frames (o frame estatico de
  cada direcao, nao o frame de respiracao). Para `female` e `teen` a mesma
  pose NAO bate por hash (diferencas de 13 a 154 pixels de 4096) -- nao
  atende ao criterio de "puro apontamento deterministico, zero risco" exigido.
  A hipotese depende do corpo, portanto nao generaliza.
- `combat_idle`, `sit`, `run`: INVIAVEIS. Zero frames com hash identico em
  qualquer animacao antiga, em qualquer direcao, em nenhum dos 3 corpos
  testados. As melhores aproximacoes ficam entre 127 e 566 pixels diferentes
  por frame de 4096 (ate 13,8%), muito acima do limiar de "2 ou 3 pixels"
  citado como aceitavel.
- Roupa: nas 3 pecas legadas testadas, o frame-alvo do remapeamento de `idle`
  existe com conteudo real (nao vazio). Mas isso so importa para `idle`,
  porque as outras 3 animacoes nao tem frame-alvo no corpo para comecar.
- Impacto nos 170 itens incompletos: como 169 dos 170 tambem faltam
  `combat_idle` (inviavel), e nao ha nenhuma peca-fonte que falte APENAS
  `idle` entre as 4 (0 confirmado na varredura de pastas), o remapeamento de
  `idle` nao completaria nenhum item sozinho -- so reduziria em 1 (de 5 para
  4) a quantidade de animacoes faltantes em itens que continuariam
  incompletos por causa de `combat_idle`/`sit`/`run`.

Conclusao numerica: 0 dos 170 itens seriam totalmente recuperados por este
remapeamento. Na melhor hipotese (aceitando o risco de nao-identidade exata
em female/teen), o ganho se limita a preencher parcialmente `idle` em itens
que ja teriam outras animacoes faltando de qualquer forma.
