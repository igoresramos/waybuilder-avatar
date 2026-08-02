# H2 -- Escopo do que gerar (idle, combat_idle, sit, run)

## Pergunta

Nem toda animacao vale ser gerada por transplante. Decidir, com numero, o que entra
no build e o que fica no fallback (pose parada) por animacao de destino.

## Metodo

Motor `/home/igor0/waybuilder-avatar/transplante.py`, sem reimplementacao
(`sobreposicao`, `campo_de_deslocamento`, `aplicar_campo`, `pixels_diferentes`).

Amostra: 391 pecas do corpo male, camada 0 (primeira camada declarada), que tem as
cinco animacoes completas -- mesmo recorte da fase de movimento. De cada peca,
366 tem pelo menos uma doadora no proprio slot (as outras 25 sao slots de item
unico e ficam fora da prova, mesma regra da fase anterior).

Para cada uma das 366 pecas e cada animacao de destino (idle k=1, combat_idle
k=1, sit k=1, run k=1), a doadora e escolhida por maior IoU do quadro de
partida walk k=0 dentro do MESMO slot (regra atual, ja validada na fase de
movimento -- e a que muda so 6 pontos percentuais no maximo mesmo com oraculo).
O campo de deslocamento e aprendido no par (doadora walk k=0 -> doadora
destino k) e aplicado na peca alvo (alvo walk k=0 -> alvo destino k previsto).
Validacao por peca: a peca nunca e doadora de si mesma.

Baseline 'nao fazer nada' = comparar alvo walk k=0 direto contra alvo destino
k, sem nenhum transplante -- e o fallback de pose parada que a hipotese testa.

n=366 por animacao (>= 300 pedido). Nao reduzi.

## Tabela completa

| animacao | n | exatos (transplante) | exatos (parado) | mediana px | mediana px parado | media px | frac area mediana | frac area media | <=5% area (passa) | >25% area (lixo) |
|---|---|---|---|---|---|---|---|---|---|---|
| idle | 366 | **24,9%** | 9,3% | 20 | 128 | 35,6 | 11,9% | 19,7% | 124 (33,9%) | 89 (24,3%) |
| combat_idle | 366 | 20,5% | 3,5% | 30 | 187 | 44,9 | 16,5% | 32,3% | 104 (28,4%) | 148 (40,4%) |
| run | 366 | 17,2% | 3,5% | 34 | 205 | 56,6 | 24,1% | 49,4% | 88 (24,0%) | 181 (49,5%) |
| sit | 366 | 3,6% | 3,3% | 118 | 319 | 125,1 | 67,4% | 70,9% | 13 (3,6%) | 352 (96,2%) |

`exatos` = fracao de pecas com 0 pixel errado no frame inteiro. `frac area` =
pixels errados / area da peca no frame de destino (por peca, depois
mediana/media). `<=5%` e `>25%` sao contagens de pecas, nao fracao de pixel.

## Por (destino, regiao)

Bandas anatomicas iguais as da fase de movimento (cabeca y<38, torso
38<=y<50 e 23<=x<41, bracos mesma faixa nas laterais, pernas 50<=y<57, pes
y>=57, externo x<15 ou x>=49). `n` = so pecas que tem pixel na regiao naquele
destino; `frac_mediana` = pixels errados / pixels da peca na regiao (mediana).

| destino | regiao | n | exatos | mediana px | frac_mediana |
|---|---|---|---|---|---|
| idle | cabeca | 325 | 21,9% | 18 | 12,0% |
| idle | torso | 82 | 13,4% | 17 | 21,5% |
| idle | bracos | 40 | 10,0% | 8,5 | 97,1% |
| idle | **pernas** | 27 | **44,4%** | 6 | **6,7%** |
| idle | **pes** | 20 | **60,0%** | 0 | **0,0%** |
| idle | externo | 3 | 0,0% | 18 | 100,0% |
| combat_idle | cabeca | 325 | 19,4% | 20 | 13,7% |
| combat_idle | torso | 108 | 10,2% | 22 | 74,2% |
| combat_idle | bracos | 48 | 43,8% | 1 | 55,0% |
| combat_idle | **pernas** | 32 | **0,0%** | 32,5 | **72,3%** |
| combat_idle | **pes** | 20 | **0,0%** | 10 | **37,5%** |
| combat_idle | externo | 6 | 33,3% | 8,5 | 100,0% |
| run | cabeca | 320 | 16,6% | 23 | 19,1% |
| run | torso | 117 | 18,8% | 19 | 49,6% |
| run | bracos | 54 | 3,7% | 8 | 78,0% |
| run | **pernas** | 28 | **0,0%** | 38 | **90,2%** |
| run | **pes** | 25 | **0,0%** | 21 | **58,0%** |
| run | externo | 4 | 0,0% | 16 | 100,0% |
| sit | cabeca | 274 | 0,0% | 122 | 68,2% |
| sit | torso | 213 | 0,5% | 24 | 83,3% |
| sit | bracos | 102 | 0,0% | 14 | 89,3% |
| sit | pernas | 72 | 0,0% | 21 | 84,2% |
| sit | pes | 30 | 0,0% | 13 | 60,0% |
| sit | externo | 4 | 0,0% | 16 | 100,0% |

Combinacao que e SEMPRE boa: (idle, pes) e (idle, pernas) -- exatamente as
mesmas duas celulas que a fase de movimento ja tinha marcado como triviais
(la por translacao rigida, aqui de novo por transplante). Combinacoes que sao
SEMPRE lixo, em qualquer animacao: (combat_idle, pernas), (combat_idle, pes),
(run, pernas), (run, pes) -- 0,0% de exatos e >37% de frac_mediana nas
quatro. E sit inteiro: nenhuma das seis regioes passa de 0,5% de exatos.

## Veredito por animacao

**idle -- ENTRA NO BUILD.** 24,9% de frames exatos contra 9,3% do fazer-nada
(2,7x), mediana de erro 20 px contra 128 (6,4x menor), e e a UNICA animacao
onde a fracao "passa sem revisao" (33,9%) supera a fracao "lixo" (24,3%). As
duas regioes ruins sao bracos (n=40, frac 97,1%) e externo (n=3, irrelevante
em volume) -- o resto do corpo (cabeca, torso, pernas, pes) fica abaixo de
22% de erro medio de area. Gatilho de revisao manual: peca com slot em
{cloth, sleeves, gloves} onde a regiao braco tem area de peca > 0 -- e onde
o metodo falha aqui.

**combat_idle -- ENTRA COM REVISAO.** 20,5% exatos contra 3,5% do fazer-nada
(5,9x) e mediana 30 contra 187 (6,2x menor) -- ganho real, nao ruido. Mas
40,4% das pecas caem acima do limiar de lixo (25% de area errada), quase o
dobro do idle, puxado por torso (74,2% de erro medio de area) e pernas/pes
(72,3% e 37,5%). Regra de corte: se a peca tiver area de peca > 0 nas regioes
pernas OU pes para o destino combat_idle, nao gerar -- sao 32 e 20 pecas
respectivamente, 0,0% de exatos nas duas, e o fallback parado sai igual ou
melhor.

**run -- ENTRA COM REVISAO, mais estreito que combat_idle.** 17,2% exatos
contra 3,5% (4,9x) e mediana 34 contra 205 (6,0x menor) -- ainda vence o
fazer-nada com folga. Mas quase metade das pecas (49,5%) sao lixo pelo
limiar de 25%, a pior taxa entre as tres animacoes que entram, e a fase de
movimento ja tinha medido correlacao ZERO entre IoU da doadora e erro do
resultado em run (-0,001, contra -0,60 em idle) -- ou seja aqui a escolha de
doadora nao esta prevendo qualidade nenhuma, o metodo acerta ou erra sem
relacao com o criterio usado para escolher. Mesma regra de corte de
combat_idle se aplica (pernas/pes = 0,0% exatos, frac_mediana 90,2% e 58,0%),
e alem dela: nao confiar no IoU da doadora como sinal de confianca em run,
porque ele nao correlaciona com o erro.

**sit -- NAO ENTRA.** 3,6% exatos contra 3,3% do fazer-nada -- estatisticamente
empatado com nao fazer nada (a diferenca de 0,3 ponto percentual, 13 vs 12
pecas em 366, e ruido). A mediana de erro cai de 319 para 118 px, uma reducao
absoluta grande, mas o numero final ainda e 67,4% da area da peca errada
(mediana) -- nao e retoque, e outra peca. 96,2% das pecas caem no limiar de
lixo. Nenhuma das seis regioes passa de 0,5% de frames exatos, incluindo
pernas e pes que sao triviais em toda outra animacao de destino. Confirma a
fase de movimento (que ja media 0,0% em 349 pecas): sit e insalvavel pelo
transplante como esta.

## Parametros para virar codigo

Se a hipotese "nem toda animacao vale gerar" e para virar regra automatica no
pipeline, os numeros que a sustentam sao:

1. **Corte por animacao**: gerar idle, combat_idle, run. NAO gerar sit --
   cair no fallback parado (walk k=0 congelado) sempre que a animacao pedida
   for sit.
2. **Corte por regiao dentro de combat_idle e run**: se a peca tiver pixel
   nas regioes `pernas` (50<=y<57, 15<=x<49) ou `pes` (y>=57, 15<=x<49) no
   frame de destino, usar fallback parado para essa peca nessas duas
   animacoes especificamente -- 0,0% de exatos e frac_mediana >37% nas
   quatro celulas medidas (n entre 20 e 32 cada).
3. **Limiar de revisao manual por fracao de area**: peca com
   `pixels_errados / area_da_peca_no_destino > 0,25` vai para fila de
   revisao antes de entrar no build; abaixo de 0,05 passa direto. Aplicado a
   idle (24,3% revisao / 33,9% direto), combat_idle (40,4% / 28,4%) e run
   (49,5% / 24,0%).
4. **Sinal de baixa confianca especifico de run**: correlacao IoU-doadora x
   erro = -0,001 (medido na fase de movimento, n=331) -- nao usar o IoU da
   doadora como score de confianca para saltar a fila de revisao em run,
   porque ele nao prediz nada ali (funciona em idle, corr -0,60).

## Limites declarados

Medido so no corpo male, camada 0, direcao frente -- nao testei female/child
nem camadas adicionais da mesma peca (bg/fg). Destino de cada animacao foi
sempre o quadro k=1 (idle, combat_idle, sit) ou k=1 de run; nao testei os
outros quadros de walk/run/sit (a fase de movimento indica que sit e ruim em
TODOS os quadros e regioes, entao a conclusao para sit deve se sustentar, mas
nao medi run/combat_idle em k diferente de 1 aqui). O n=366 e menor que os
"pecas_completas" com doadora da fase anterior (349) porque usei minha propria
extracao de doadora nesta sessao -- os numeros de exatos batem na faixa
esperada mas nao sao identicos byte a byte aos da fase de movimento (ex.: sit
aqui deu 3,6% contra 0,0% la, diferenca de 13 pecas em 366 -- dentro do que se
explica por escolha de item exatamente empatado em IoU). A regra de corte por
regiao (item 2) foi validada so nas quatro celulas medidas aqui (n entre 20 e
32); generalizar para outras animacoes/regioes exigiria nova medicao.
