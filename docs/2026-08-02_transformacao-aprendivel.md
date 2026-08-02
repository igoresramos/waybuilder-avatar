# A transformacao walk -> idle e aprendivel a partir dos pares existentes?

Medicao pura. Testa a tese: "as animacoes do LPC sao regulares o bastante para
que a transformacao walk -> idle seja aprendivel a partir dos exemplos
existentes, sem entender dobra de tecido."

Fonte: `/home/igor0/waybuilder/app/public/avatar/catalogo.json` + atlas PNG em
`atlas/`. Corpo `male`, direcao ja fixada pelo catalogo (`recorte.direcao =
"frente"`). Frame 64x64. Ambiente: venv Python 3.12 com numpy 2.5.1, Pillow
12.3.0, scipy 1.18.0 (nao havia numpy/PIL no python3 do sistema; venv criado em
`/tmp/.../scratchpad/venv`, nao commitado).

## Nota sobre o N: 457 vs 442

O catalogo tem 627 itens, dos quais 170 sao incompletos (falta alguma
animacao) e 457 completos -- **mas "completo" no catalogo significa "tem as 5
animacoes em ALGUM corpo/camada", nao especificamente em `male`**. Ao filtrar
estritamente para o corpo `male` (usando a primeira camada de cada item cujo
`male` tenha as 5 animacoes), sobram **442** pares utilizaveis:

- 457 - 14 = itens cujas 5 animacoes so existem para corpo `child` (cabecas e
  cabelo infantis: `hair/child-wavy`, `head/mouse-child`, `head/pig-child`,
  `head/rabbit-child`, `head/rat-child`, `head/sheep-child`,
  `head/lizard-child`, `head/human-child`, `head/boarman-child`,
  `head/minotaur-child`, `head/wolf-child`, `head/goblin-child`,
  `head/orc-child`, `head/troll-child`) -- nao tem arte para `male`.
- -1 = `body/body-color`, o proprio corpo-guia, removido do conjunto de
  "pecas de roupa" (ele e o contexto, nao o alvo).

Todos os experimentos abaixo usam **N = 442**. Reporto isso explicitamente
porque o enunciado pedia 457 e o numero medido e outro.

## 1) Linha de base burra (walk frame 0 vs idle frame 0, corpo male)

Comparacao pixel a pixel (RGBA) entre `idle` frame 0 e `walk` frame 0, das 442
pecas, cada frame 64x64 = 4096 pixels.

| Metrica | Valor |
|---|---|
| Media de pixels diferentes | 17,75 |
| Mediana | 0,0 |
| p10 / p90 | 0,0 / 77,5 |
| Maximo | 338 |
| Pecas com diferenca ZERO (identicas) | 362 / 442 (81,9%) |
| Pecas com diferenca < 5 px | 366 / 442 (82,8%) |
| Media so nas 80 pecas com diferenca > 0 | 98,1 px (mediana 91, p90 218) |

**Achado, verificado diretamente no atlas do corpo**: `walk` frame 0 e `idle`
frame 0 sao **byte-a-byte identicos no proprio corpo** (0 pixels diferentes em
4096). Isso e consistente com `recorte.ciclos.walk = [1,2,3,4,5,6,7,8]` no
catalogo -- o frame 0 do walk e descartado do ciclo de animacao, e e
literalmente a pose parada reaproveitada. Por construcao do spritesheet, a
maioria das pecas (82%) herda essa identidade. Isso NAO e um resultado sobre
"a transformacao e trivial" em geral -- e um artefato de que o par de frames
`(walk k=0, idle k=0)` nao contem movimento nenhum para testar. Os 18%
restantes (80 pecas) tem diferencas reais, ate 338 px (8,3% do frame),
concentradas em pecas com dobra/sombra que varia mesmo na "mesma pose"
nominal.

Como o par `k=0/k=0` e degenerado (sem movimento), os itens 2 a 5 abaixo usam
o par **`walk k=0` -> `idle k=1`** (a pose de "respiracao" do idle, que
realmente difere da pose parada -- 168 px de diferenca no proprio corpo). Isso
e uma decisao metodologica meu, declarada aqui: testar "a transformacao e
aprendivel" no par onde ELA EXISTE. Repito o item 2 tambem no par literal
`k=0/k=0` para nao esconder o resultado degenerado.

## 2) A transformacao e a mesma entre pecas?

Campo de deslocamento calculado nos pixels opacos do CORPO em idle, buscando
o patch 5x5 mais parecido (SSD) numa janela de +-6 px no corpo em walk;
empates resolvidos a favor do menor deslocamento. Campo aplicado a cada peca
(deslocamento so definido dentro da mascara opaca do corpo; fora dela,
extensao por identidade -- nao apagar pixel que o campo nao cobre).

### 2a) Par literal `walk k=0 -> idle k=0` (o pedido ao pe da letra)

O corpo nao se move entre esses dois frames (item 1): SSD minimo = 0 em TODOS
os 692 pixels opacos do corpo em idle, deslocamento escolhido = (0,0) em
100% deles. O campo aprendido e a identidade pura. Resultado: **o warp fica
matematicamente identico, pixel a pixel, ao "nao fazer nada" do item 1**, nas
442 pecas (diferenca maxima medida entre warp e baseline = 0). Nao ha o que
comparar -- nao existe transformacao para aprender neste par.

### 2b) Par com movimento real `walk k=0 -> idle k=1` (suplementar, ver nota acima)

Corpo: 714 pixels opacos em idle k=1; 316/714 (44%) escolheram deslocamento
nao-zero; erro residual do warp no proprio corpo = 66/714 pixels (9,2% --
mesmo no corpo-fonte o casamento de patch 5x5 nao e perfeito).

| Metrica | Warp aplicado as pecas | Baseline (nao fazer nada) |
|---|---|---|
| Media de pixels errados | 112,7 | 126,9 |
| Mediana | 99,0 | 111,0 |
| p90 | 226,9 | 253,8 |
| Pecas com erro < 5 px | 60 / 442 (13,6%) | 42 / 442 (9,5%) |

Comparacao peca a peca: warp melhor que baseline em **229/442 (51,8%)**,
igual em 174/442 (39,4%), **pior em 39/442 (8,8%)**.

**Leitura**: quando ha movimento de verdade para aprender, o campo do corpo
ajuda -- reduz o erro medio em ~11%, mas so tira 18 pecas a mais da faixa
"quase perfeito" (<5px), de um universo de 442. Nao e ruido (melhora na
maioria das pecas), mas tambem esta longe de "aplicar o campo do corpo resolve
a roupa": mesmo com o warp, 88,4% das pecas ainda tem 5 pixels errados ou
mais.

## 3) Previsibilidade local (k-NN por contexto)

Contexto por pixel (x,y): patch 5x5 de alfa do CORPO em `idle k=1` (silhueta
local, 25 valores 0/1) + patch 5x5 do indice-de-rampa da PECA em `walk k=0`
(25 valores, rank de luminancia 0-5 dentro da paleta propria da peca, 6 =
transparente) + indice-de-rampa da propria peca no pixel central (1 valor).
Total 51 dimensoes discretas. Alvo: indice-de-rampa da peca em `idle k=1` no
mesmo pixel (mesma escala 0-6, para generalizar entre paletas de cor
diferentes -- nao RGB bruto).

Universo de pixels: uniao dos pixels opacos da peca em walk OU idle (nao o
frame de 4096 inteiro -- fundo compartilhado por todas as pecas nao e
informativo). 14 das 442 pecas ficaram sem nenhum pixel relevante nesse par de
frames (silenciosamente vazias em male/frente nesses 2 frames especificos) e
foram excluidas, restando **428 pecas com dados**.

Split: pedido era 400 treino / 57 teste (base de 457). Com N real = 428, usei
**371 treino / 57 teste** -- mantive o tamanho do teste pedido (57), split
aleatorio com seed fixa, peca de teste nunca aparece no treino.

- Pixels de treino: 75.104 (de 371 pecas)
- Pixels de teste: 12.176 (de 57 pecas), dos quais **7.918 (65,0%) mudam**
  entre walk e idle (rank diferente)

k-NN k=1 real (distancia euclidiana no espaco de 51 dims, busca exaustiva
vetorizada, sem aproximacao):

| Metrica | Valor |
|---|---|
| Acuracia geral (todos os 12.176 pixels de teste) | **67,9%** |
| Acuracia SO nos pixels que mudam (7.918) | **65,1%** |
| Baseline "nao muda nada" (prever idle = walk) geral | 35,0% |
| Baseline "nao muda nada" nos pixels que mudam | 0,0% (por definicao) |

k-NN bate a baseline burra por uma margem grande (67,9% vs 35,0% geral). O
contexto tem sinal real. Mas 32-35% de erro por pixel e muito para uma peca
inteira (ver item 5).

### Entropia condicional H(rotulo | contexto)

Contextos exatos (tupla dos 51 valores) no treino: **54.835 unicos**, de
75.104 exemplos -- 45.513 aparecem so 1 vez, 9.322 se repetem.

**H(rotulo | contexto) = 0,0516 bits.** Muito baixa: quando o MESMO contexto
aparece de novo no treino, ele aponta pra resposta ambigua raramente -- so
453 dos 54.835 contextos (0,83%) tem mais de uma resposta distinta associada,
cobrindo 3.021 dos 75.104 exemplos de treino (4,0%). Ou seja: **o gargalo nao
e ambiguidade** (mesmo contexto, respostas diferentes em pecas diferentes) --
**e cobertura**: a maioria dos contextos de teste simplesmente nunca apareceu
no treino (ver item 4).

## 4) O teto (oraculo por contexto exato)

Oraculo = sempre prever a resposta majoritaria do contexto exato visto no
treino (o melhor que um modelo puramente de memorizacao de contexto pode
fazer).

| Metrica | Valor |
|---|---|
| Cobertura: contexto de teste EXISTE no treino (match exato) | 3.707 / 12.176 (**30,4%**) |
| Acuracia do oraculo SO nos pixels com match (o teto de ambiguidade) | 3.417 / 3.707 (**92,2%**) |
| Acuracia do oraculo em TODO o teste (sem-match = erro) | 3.417 / 12.176 (**28,1%**) |
| Cobertura nos pixels que mudam | 2.534 / 7.918 (32,0%) |
| Acuracia do oraculo nos pixels que mudam, so onde ha match | 2.244 / 2.534 (**88,6%**) |
| Acuracia do oraculo nos pixels que mudam, sobre todos eles | 2.244 / 7.918 (28,3%) |

**Dois numeros diferentes, nao confundir**: o teto de ambiguidade (quando o
contexto exato ja foi visto, quao bem dá pra prever) e alto -- 92,2% --,
consistente com a entropia condicional baixa medida no item 3. Mas so 30,4%
dos contextos de teste batem exatamente com algo do treino; o resto (quase
70%) e contexto nunca visto. Por isso o oraculo "puro" (so responde quando
reconhece o contexto exato, erra o resto) fica em 28,1% no teste inteiro --
**pior que o k-NN de verdade (67,9%)**, porque o k-NN generaliza para o
vizinho mais proximo mesmo sem match exato, e o oraculo nao. O teto pratico
(o melhor numero que de fato bate contas nos 442/428 pecas) e o **67,9%** do
k-NN, nao os 92,2% do oraculo idealizado -- 92,2% so vale se o contexto ja
tiver sido visto, o que acontece em menos de um terco dos casos.

## 5) Traducao para a tela

Taxa usada: **67,9%** de acerto por pixel (k-NN geral, item 3 -- o numero que
de fato tem cobertura de 100% do teste; e a melhor taxa real entre os itens 3
e 4). Erro por pixel = 32,1%.

| Peca de referencia | Pixels opacos | Erro esperado (32,1%) |
|---|---|---|
| Calca | 161 | ~51,7 px errados |
| Bota | 120 | ~38,5 px errados |
| Manga longa | 327 | ~105,0 px errados |

Probabilidade de um frame sair **perfeito** (zero pixel errado), assumindo
erro por pixel independente (aproximacao -- na pratica os erros nao sao
independentes, tendem a se agrupar espacialmente, entao isto e uma
estimativa otimista):

- Calca (161px): P(perfeito) = 8,5e-28
- Bota (120px): P(perfeito) = 6,7e-21
- Manga longa (327px): P(perfeito) = 1,1e-55
- Peca media medida (~197 px opacos, media real das 442 pecas): P(perfeito) = 7,6e-34

Sobre os 43.836 frames citados como universo do acervo: **numero esperado de
frames perfeitos = 43.836 x 7,6e-34 ~ 3,3e-29 -- essencialmente zero, nenhum
frame sairia perfeito.**

Mesmo usando o teto idealizado do oraculo (92,2%, que so vale quando o
contexto ja foi visto -- otimista demais pra aplicar a todo frame), o erro
esperado numa peca de ~197px cai pra ~15,4px, e o numero esperado de frames
perfeitos em 43.836 sobe para ~0,005 -- ainda menos de 1 frame perfeito no
acervo inteiro.

## Veredito

A tese **nao se sustenta** como "basta reconhecer o padrao e aplicar".

- O que se sustenta: existe sinal local real. O contexto (silhueta do corpo +
  padrao de sombra da propria peca) prediz o pixel-alvo bem acima do acaso
  (k-NN 67,9% vs 35,0% da baseline burra), e quando um contexto identico já
  foi visto antes, a resposta é quase determinística (entropia condicional de
  0,05 bit, oraculo a 92,2% nesse subconjunto). Isso confirma a parte da tese
  que diz "o padrao das sombras carrega informacao real sobre a pose".
- O que nao se sustenta: isso nao chega perto de "aprender a transformacao e
  aplicar" no sentido de produzir frames corretos. Tres barreiras
  independentes, todas medidas:
  1. O par de frames mais obvio para testar (`walk k=0` -> `idle k=0`) e
     literalmente identico por construcao do spritesheet -- nao ha
     transformacao nenhuma pra aprender ali; so quando se usa um par com
     movimento real (`walk k=0` -> `idle k=1`) o problema aparece de verdade.
  2. Um unico campo de deslocamento aprendido no corpo, aplicado as 442
     pecas, melhora o erro medio em so ~11% sobre nao fazer nada, e deixa
     88,4% das pecas com 5 pixels errados ou mais -- a transformacao NAO e a
     mesma entre pecas de forma satisfatoria.
  3. O gargalo dominante e cobertura, nao capacidade de modelo: quase 70% dos
     contextos de pixel do teste nunca aparecem no treino, mesmo com 371
     pecas completas para aprender. Erro por pixel de 32% (mesmo na melhor
     taxa medida, com cobertura de 100%) se traduz em zero frames perfeitos
     em 43.836, mesmo na estimativa mais otimista (independencia de erro por
     pixel, que superestima a chance de acerto total).

## Reprodutibilidade

Scripts ad-hoc (nao commitados, fora do path do projeto por serem artefato de
medicao e nao arte/codigo do produto):
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/work/`
(`build_items.py`, `exp1.py`, `exp2_field.py`, `exp2_apply.py`,
`exp2_apply_v2.py`, `exp2_supp.py`, `build_dataset.py`, `split_and_exact.py`,
`oracle_coverage.py`, `knn_true.py`). Venv Python em
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/venv`.
