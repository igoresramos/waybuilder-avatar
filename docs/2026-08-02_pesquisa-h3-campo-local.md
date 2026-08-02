# H3 -- Campo por regiao vs campo global

Testa se dividir o campo de deslocamento em regioes anatomicas (cada uma
podendo usar sua propria doadora) bate o campo global unico que o motor usa
hoje (`transplante.campo_de_deslocamento` aplicado ao quadro inteiro).

**Veredito: H3 PERDE.** Em nenhum dos 6 experimentos (3 pares de animacao x
2 escopos de amostra) o campo por regiao bateu o campo global em frames
exatos ou em mediana de erro. A costura entre regioes cria erro novo e
sistematico na fronteira (+23% a +26% de pixels errados ali, contra o campo
global no mesmo alvo), sem ganho equivalente no interior. Escolher uma
doadora diferente por regiao (variante b) nao muda o resultado em relacao a
usar a mesma doadora em todas as regioes (variante a) -- o problema nao e
qual doadora, e a fragmentacao geometrica da busca.

## Metodo

Motor original, sem reimplementar: `sobreposicao`, `campo_de_deslocamento`,
`aplicar_campo`, `pixels_diferentes`, `escolher_doadora` de
`/home/igor0/waybuilder-avatar/transplante.py`, `raio=6, patch=5` (default,
igual ao motor em producao).

**Particao em regioes.** As bandas fixas do
`docs/2026-08-02_mapa-de-movimento.json` (cabeca, torso, bracos, pernas,
pes, externo) sao retangulos no canvas 64x64 e, juntas, cobrem o canvas
inteiro sem sobra e sem sobreposicao -- bracos e externo viram dois
retangulos cada (esquerdo/direito) para manter tudo retangular:

| sub-regiao | y | x |
|---|---|---|
| cabeca | 0-38 | 15-49 |
| torso | 38-50 | 23-41 |
| braco_esq / braco_dir | 38-50 | 15-23 / 41-49 |
| pernas | 50-57 | 15-49 |
| pes | 57-64 | 15-49 |
| externo_esq / externo_dir | 0-64 | 0-15 / 49-64 |

**Tres variantes, mesmo alvo, mesma peca de teste, comparadas lado a lado:**
- **(c) global** (baseline atual): 1 campo, calculado no quadro inteiro
  (64x64), doadora = mesmo slot, maior IoU no quadro de origem.
- **(a) regiao, mesma doadora**: a MESMA doadora do global, mas o campo e
  recalculado 8 vezes -- uma por sub-regiao, cada chamada recebendo so o
  recorte da doadora e do alvo naquela sub-regiao -- e depois colado de
  volta no canvas 64x64.
- **(b) regiao, doadora por regiao**: para cada sub-regiao, escolhe a
  doadora (dentre as mesmas candidatas do slot) por maior IoU DENTRO daquele
  recorte, podendo divergir da doadora global.

**Custura.** Para (a), medi separadamente o erro em pixels a ate 1px de
qualquer divisa entre sub-regioes ("fronteira") e o erro no resto
("interior"), comparando contra o mesmo calculo no campo global, alvo a
alvo -- para isolar se a regionalizacao cria defeito novo bem na emenda.

**Validacao por peca**: a doadora nunca e a propria peca de teste (mesmo
slot, excluindo self). Peca sem outra candidata no slot fica fora da
amostra (coluna `n_sem_doadora`).

## Amostra

Corpo male, camada composta (todas as camadas do item, alpha-over por
zPos). Tres pares de animacao, escolhidos porque cruzam os dois grupos de
pose que a fase de movimento identificou (frontal: idle/walk/sit x virado:
combat_idle/run) -- e por isso sao onde a translacao rigida da H1 falha e
onde H3 teria mais a ganhar:

- `walk k=0 -> idle k=1` (referencia FACIL, dentro do grupo frontal, e o
  par do baseline oficial)
- `walk k=0 -> run k=1` (cruza grupo, foco de H3)
- `walk k=0 -> combat_idle k=1` (cruza grupo, foco de H3)

Cada par rodou em dois escopos:
- **todos os slots** (n = 416 a 457, cobertura por par abaixo) -- amostra
  principal, > 300 conforme pedido.
- **so slots `clothes` e `shield_pattern`** (n = 70) -- o subconjunto onde a
  H1 (translacao rigida) da 0% de exatos e o motor de transplante tambem;
  exatamente onde H3 deveria compensar se fosse a resposta. Esses 70 sao as
  pecas NAO legadas de `clothes` (22 de 35) e `shield_pattern` (48 de 48,
  nenhuma legada nesse slot) -- as unicas com quadro real para validar
  contra; as 13 legadas de `clothes` ficam de fora por nao ter groundtruth,
  igual ao resto do estudo.

## Resultado -- todos os slots (amostra principal)

Baseline recalculado nesta amostra ao lado de cada variante:

| par | variante | n | exatos | mediana | media |
|---|---|---|---|---|---|
| walk->idle (facil) | **global (baseline)** | 457 | **18,8%** | **25** | 42,7 |
| | regiao, mesma doadora | 457 | 15,5% | 27 | 44,8 |
| | regiao, doadora por regiao | 457 | 15,3% | 28 | 44,4 |
| walk->run (foco H3) | **global (baseline)** | 421 | **11,6%** | **41** | 70,7 |
| | regiao, mesma doadora | 421 | 7,1% | 45 | 74,2 |
| | regiao, doadora por regiao | 421 | 7,1% | 44 | 74,2 |
| walk->combat_idle (foco H3) | **global (baseline)** | 416 | **14,7%** | **35** | 55,8 |
| | regiao, mesma doadora | 416 | 11,5% | 38 | 58,7 |
| | regiao, doadora por regiao | 416 | 11,5% | 39 | 59,5 |

Cobertura (doadora mesmo slot disponivel): 457/493, 421/452, 416/444 --
consistente com o resto do estudo. Controle nulo (nao mover nada) fica em
0,0% a 5,3% de exatos, mediana 115 a 189 -- todas as variantes de campo
continuam MUITO melhores que nao mover nada; a pergunta e so global vs
regiao.

Note que o baseline recalculado em walk->idle (18,8% / mediana 25 / media
42,7) bate com o numero oficial reportado nas fases anteriores (20,0% /
mediana 28 / media 42,7) -- confirma que a amostra e o pipeline estao
consistentes com o resto do estudo.

**Em nenhum dos 3 pares, em nenhuma metrica, a regionalizacao ganha do
campo global.** A perda cresce com a dificuldade do par: -3,3pp de exatos em
walk->idle (facil), -4,5pp em walk->run, -3,2pp em walk->combat_idle.

## Resultado -- fronteira (custura)

Erro medio de pixels errados na faixa de 1px ao redor das 8 divisas de
regiao, alvo a alvo, comparando o campo global com o campo por regiao
(variante a) no MESMO alvo:

| par | fronteira, global | fronteira, regiao | interior, global | interior, regiao |
|---|---|---|---|---|
| walk->idle | 5,34 | 6,58 (+23%) | 37,34 | 38,21 (+2%) |
| walk->run | 10,71 | 13,21 (+23%) | 59,99 | 61,00 (+2%) |
| walk->combat_idle | 7,80 | 9,81 (+26%) | 48,01 | 48,88 (+2%) |

A costura cria erro novo e sistematico bem na emenda (+23% a +26% de pixels
errados so na faixa de 1px ao redor das divisas) e o interior tambem piora
um pouco (+2%) -- nao ha regiao onde o corte compensa com folga. Isso e
esperado pela mecanica do motor: `campo_de_deslocamento` usa patch 5x5 e
raio de busca 6px, ou seja depende de ate 6px de contexto ao redor de cada
pixel; ao recortar o quadro em sub-regioes de ate 48px de lado, o padding
`mode="edge"` do motor passa a repetir a borda ARTIFICIAL do recorte em vez
do pixel real que existia do outro lado da divisa -- perde exatamente o
contexto de que o casamento por patch depende, o que penaliza tanto a
fronteira quanto boa parte do "interior" das sub-regioes menores (o raio de
6px alcanca quase toda sub-regiao pequena).

## Resultado -- escopo legado (clothes + shield_pattern, n=70)

Subconjunto onde a H1 (translacao rigida) ja dava 0% de exatos e onde H3
deveria ter a melhor chance de ajudar:

| par | variante | n | exatos | mediana | media |
|---|---|---|---|---|---|
| walk->idle | global | 70 | 0,0% | 48,0 | 47,8 |
| | regiao, mesma doadora | 70 | 0,0% | 49,5 | 48,1 |
| | regiao, doadora por regiao | 70 | 0,0% | 47,5 | 47,3 |
| walk->run | global | 70 | 0,0% | 59,5 | 60,9 |
| | regiao, mesma doadora | 70 | 0,0% | 60,0 | 61,4 |
| | regiao, doadora por regiao | 70 | 0,0% | 60,0 | 64,7 |
| walk->combat_idle | global | 70 | 0,0% | 54,5 | 53,2 |
| | regiao, mesma doadora | 70 | 0,0% | 55,0 | 54,0 |
| | regiao, doadora por regiao | 70 | 0,0% | 55,0 | 58,7 |

**Nenhuma variante sai de 0,0% de exatos em nenhum dos 3 pares neste
subconjunto.** Na melhor leitura (walk->idle, doadora por regiao) a mediana
melhora de 48,0 para 47,5 -- 0,5 pixel, dentro do ruido, e ainda com 0%
exatos nas tres variantes; nos outros dois pares a regionalizacao so piora.
Regionalizar o campo nao resgata o caso onde a translacao rigida ja falhava:
so acrescenta ruido de costura ao caso facil.

## Por que perde

1. **O movimento anatomico e local, mas a busca de pixel do motor tambem
   ja e local** (patch 5x5, raio 6px) -- ela nao precisa de fronteira
   explicita para achar deslocamento local, e ja o faz pixel a pixel dentro
   do campo global. Cortar o quadro em regioes so tira contexto de busca
   sem dar nada em troca, porque o motor nunca olhava "regiao errada" pra
   comecar -- o raio de 6px e curto.
2. **A costura e cara e nao e amortizada.** Toda sub-regiao pequena (a
   menor tem 48px de area) tem quase toda sua area a menos de 6px de uma
   borda, entao o efeito de contexto perdido na fronteira nao fica
   contido na faixa fina que medimos -- ele vaza pro "interior" tambem (+2%
   la, alem do +23-26% na propria faixa).
3. **Doadora por regiao (variante b) nao ajuda em relacao a doadora unica
   (variante a)** -- os numeros de (a) e (b) sao estatisticamente iguais
   nos 6 experimentos (diferenca de 0,0 a 0,2pp de exatos, 0 a 5 pixels de
   mediana, sem direcao consistente). Isso indica que a doadora de maior
   IoU no quadro inteiro ja e, na pratica, tambem a melhor doadora por
   regiao na maioria dos casos -- reforcando o achado anterior (fase de
   movimento) de que a escolha de doadora por IoU global ja captura quase
   todo o ganho disponivel, e que o gargalo nos pares dificeis (run,
   combat_idle) e o modelo de campo, nao a doadora.

## Parametros -- nao aplicavel

Como a hipotese perde em toda a matriz testada, nao ha limiar, peso ou
criterio de campo-por-regiao a recomendar para o build. A recomendacao e
MANTER o campo global unico (variante c, ja em producao) e nao investir em
regionalizar o campo de deslocamento.

## Limitacoes

- Medido so na direcao frontal, corpo male, camada composta por alpha-over
  em zPos -- nao testado em female/child/teen/muscular/pregnant.
- Sub-regioes sao retangulos fixos por banda anatomica do corpo (vista de
  cima); nao testei sub-regioes por bounding-box da propria peca (que
  variaria de peca pra peca e teria menos efeito de borda artificial em
  pecas grandes, mas quebraria a comparacao alvo-a-alvo com o campo
  global).
- So testei os pares que cruzam idle/walk (frontal) para run/combat_idle
  (virado) mais o par facil walk->idle; nao testei sit nem os pares
  run<->combat_idle (dentro do grupo virado).
- Amostra do escopo legado (clothes+shield_pattern) e pequena (n=70) por
  construcao -- e o tamanho real do subconjunto nao-legado desses dois
  slots no acervo, nao uma reducao arbitraria.
- `pixels_diferentes` e `sobreposicao` como o motor define -- pixel
  invisivel nao conta como diferenca, silhueta e so o canal alpha.

## Scripts

Nao commitados, em
`/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/h3/`:
`lib.py` (loader do catalogo/atlas + particao de regioes), `build_sets.py`
(monta os conjuntos de pecas completas por par de animacao), `experimento.py`
(roda as 3 variantes x 6 experimentos e grava `resultados.json`).
