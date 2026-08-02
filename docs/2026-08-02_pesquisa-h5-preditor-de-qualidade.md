# H5 v2 -- preditor de qualidade sem gabarito, retreinado sobre a TRANSLACAO

Retomada da pesquisa H5 depois de queda de conexao na rodada anterior. A rodada
anterior treinou o preditor prevendo o erro do TRANSPLANTE e passou o criterio
(precisao OOF 82,8%, n=99). Mas a pesquisa mudou embaixo dele: o metodo
recomendado deixou de ser o transplante e virou a TRANSLACAO RIGIDA por slot
(ver `docs/2026-08-02_PESQUISA-transplante.md`, secao 6). Aplicado sobre a
saida da translacao, o preditor antigo **inverte** a selecao (spearman
score/erro = -0,08; aprovados mais errados que reprovados). Esta rodada
retreina do zero sobre o alvo certo.

**Veredito, adiantado: NAO passa o criterio de 70%.** Precisao OOF no quartil
pior = **50,5%** (melhor modelo testado). Pior: sob a translacao o criterio
como foi definido (25% sinalizados) e **matematicamente impossivel de
cumprir** nesta populacao -- ver secao 5.

---

## 1. Metodo -- o que mudou em relacao a rodada anterior

Motor reaproveitado sem reimplementacao: `pixels_diferentes`, `aplicar_campo`
de `/home/igor0/waybuilder-avatar/transplante.py`. A busca de translacao
otima e a moda por slot **nao existiam no motor** (sao do H1, nao do
transplante) -- reimplementadas em `lib2.py` seguindo a letra do protocolo
descrito em `docs/2026-08-02_pesquisa-h1-translacao-rigida.md` ("Parametros
exatos"): busca exaustiva `dy,dx in [-4,4]`, desempate por menor `|dy|+|dx|`,
depois `|dy|`, `|dx|`, `dy`, `dx`; moda por slot com desempate por menor
magnitude, depois lexicografico.

**Alvo novo:** `erro_translacao` = `pixels_diferentes(traduzida, idle1_real)`,
onde a traducao usa o `(dy,dx)` da MODA DO SLOT calculada por
**leave-one-out por peca** (a peca de teste nunca entra na moda que a
translada -- mesma disciplina do H1 e do H5 v1). Reproduz de forma
independente o numero do H1: **82,4% de exatos, mediana 0, media 15,1
(n=393)** contra os 77,6% do H1 (n=428) -- mesma ordem de grandeza; a
diferenca vem de detalhes de implementacao (a translacao aqui zero-preenche
a borda que sai do canvas, em vez de repetir; populacao filtrada de forma
levemente diferente).

**Par:** `walk k=0 -> idle k=1`, corpo `male`, `camadas[0]`. Nao medido em
`k=0`.

## 2. Exclusao do vazio-contra-vazio

Igual armadilha do H2 (13 de 366 pecas com `camadas[0]` vazia pontuando
grátis), aplicada aqui na propria populacao desta rodada (467 candidatas
antes do filtro, denominador diferente do H2 porque a base de partida e
outra -- pecas com `walk`+`idle` completos, nao o catalogo inteiro):

- **40 de 467** candidatas excluidas por `walk k=0` inteiramente transparente
  em `camadas[0]`.
- **0** excluidas por `idle k=1` vazio com `walk k=0` nao-vazio (nao houve
  caso; se houvesse, contaria como erro real de qualquer forma, nao inflaria).
- Populacao final: **427** pecas completas; **393** com pelo menos 1 peca de
  treino no proprio slot (LOO possivel) -- as outras **34** ficam sem
  cobertura (slot inteiramente sozinho na amostra).

## 3. Sinais que morreram, e por que

| Sinal (H5 v1) | Por que morre sob translacao |
|---|---|
| `iou` (parecenca com a doadora) | Nao ha doadora. A translacao nao busca peca nenhuma -- usa a moda do slot |
| `mag_media`, `mag_max` (magnitude do campo por pixel) | O campo e **constante** dentro da peca (todo pixel anda o mesmo `(dy,dx)`) -- variancia zero DENTRO da peca. Reencarna em dois sinais distintos: `slot_disp_mag` (magnitude do deslocamento do slot, um escalar por peca) e, principalmente, `desvio_dy_dx` (o quanto o movimento NATURAL da propria peca discorda do deslocamento assumido pelo slot -- essa e a versao informativa) |
| `orfaos`, `duplicados` (pixels da origem nunca usados / usados 2x) | Propriedade do campo por PATCH MATCHING nao-rigido, que pode mapear varios-para-um. Uma translacao rigida e injetora a menos do recorte de borda -- essencialmente sempre zero, nao mede nada |

Sobrevivem, recalculados sobre a peca de PARTIDA (`walk0`) e a peca GERADA
(nunca sobre o gabarito): `frag_*`, `area_*`, `compac_*`, `buracos_*`,
`mudanca_esperada`, `natural_change`, `coerencia_ratio` (essa ultima trinca
nunca usou gabarito nem no H5 v1 -- compara a peca gerada com `walk0`/`walk1`,
que toda peca legada tem).

## 4. Sinais novos

| Sinal | Definicao | Precisa de gabarito? |
|---|---|---|
| `concordancia_slot` | fracao das OUTRAS pecas do slot cujo deslocamento otimo bate com a moda usada (LOO) | Nao -- usa gabarito de OUTRAS pecas (treino), nunca da peca alvo |
| `n_amostra_slot` | quantas pecas treinaram a moda do slot | Nao |
| `desvio_dy_dx` | distancia entre o deslocamento OTIMO da propria peca em `walk0->walk1` (que toda legada tem) e o `(dy,dx)` do slot | Nao -- nunca toca `idle` |
| `slot_disp_mag` | magnitude do `(dy,dx)` do slot | Nao |
| `bbox_partida`, `bbox_gerada`, `bbox_queda` | area do bbox antes/depois; queda = perda de bbox por corte na borda do canvas | Nao |
| `tons_partida` | numero de cores RGB distintas dentro da silhueta de `walk0` | Nao |

Sinais do **juizo visual** (`docs/2026-08-02_pesquisa-juizo-visual.md`) --
razao do maior componente conexo, queda de bbox, fracao da area errada --
todos **PRECISAM do gabarito** tal como definidos la (comparam o gerado ao
REAL). Entram como diagnostico (secao 5), nao como feature do preditor.

## 5. Correlacao de cada sinal isolado com `erro_translacao` (n=393)

Sinais **sem gabarito** (os que podem alimentar o preditor de producao),
ordenados por `|spearman|`:

| sinal | spearman | pearson-biserial (com erro>0) |
|---|---|---|
| `natural_change` | +0,516 | +0,259 |
| `concordancia_slot` | -0,348 | **-0,545** |
| `coerencia_ratio` | -0,328 | -0,285 |
| `desvio_dy_dx` | -0,252 | -0,250 |
| `slot_disp_mag` | -0,189 | -0,211 |
| `frag_partida` | -0,144 | -0,103 |
| `area_var`, `bbox_queda`, `compac_delta` | ~0,11 | ~0,11 |
| `tons_partida` | +0,003 | +0,095 |

`concordancia_slot` e o sinal mais forte contra o alvo binario (peca vai
errar ou nao): quanto mais as outras pecas do slot concordam no
deslocamento, menos provavel a peca alvo errar -- exatamente a intuicao do
"3 pecas e 80% de concordancia" que a secao 6 do documento principal ja
tinha proposto sem medir. `natural_change` (o quanto a peca ja se move
naturalmente entre `walk0` e `walk1`) e o segundo mais forte -- peca que ja
se move sozinha tende a confundir mais a translacao rigida.

**Achado metodologico capturado e corrigido durante a rodada:** a primeira
passada da tabela de precisao-por-sinal-isolado deu `buracos_partida` com
50,5% de precisao (aparentando ser um sinal forte) -- mas 365 das 393 pecas
tem `buracos_partida=0` (quase constante), e o desempate por ordem de indice
do `argsort` reproduzia a ordem do catalogo (que agrupa por slot), vazando
informacao posicional espuria em vez de medir o sinal. Corrigido trocando o
desempate por `lexsort` com chave aleatoria fixa; `buracos_partida` cai para
20,2% (perto do acaso, 17,6%). Toda a tabela de precisao isolada abaixo ja
esta com a correcao.

### Diagnostico -- sinais do juizo visual, COM gabarito (n=393)

| sinal | spearman com `erro_translacao` |
|---|---|
| `fracao_area_errada_real` | +0,997 (quase tautologico: e o proprio erro reescalado por area, nao um sinal novo) |
| `razao_maior_componente` (gerado/real) | **-0,612** |
| `queda_bbox_real` (gerado vs real) | **+0,585** |
| `maior_componente_real`, `bbox_real` | ~+0,13 (fraco isolado -- so o tamanho da peca) |

**Confirma a descoberta do juizo visual sob o metodo novo:** quando a
translacao erra, o erro tende a vir acompanhado de fragmentacao (razao do
maior componente cai) e perda de bbox -- os dois sinais que a frente de
juizo visual apontou como melhores preditores de INACEITAVEL do que o erro
em pixels sozinho. So que os dois **exigem o gabarito** (comparam com o
`idle` real), entao **nao entram no preditor de producao** -- servem para
priorizar a fila de revisao humana quando ja se tem a peca completa pra
comparar (ex.: QA de pecas nao-legadas), nao para decidir sobre uma legada
que nunca teve `idle`.

**Checagem contra os 30 julgamentos visuais existentes -- resultado fraco e
por que:** os 30 ids julgados existem todos na populacao desta rodada, mas
o julgamento humano foi feito olhando a saida do **TRANSPLANTE**, nao da
translacao. Recalculando os sinais sob translacao para os mesmos 30 ids e
correlacionando com o julgamento original: `spearman(erro_translacao,
julgamento) = +0,103`, `razao_maior_componente = +0,103`, `queda_bbox_real =
+0,051`, `fracao_area_errada_real = +0,113` -- todos fracos. **Isso nao
invalida o achado do juizo visual** (que e sobre o transplante, e mediu
correlacao 0,92 la); so mostra que comparar pixels gerados por um metodo com
rotulos humanos dados olhando OUTRO metodo nao e um teste valido -- as duas
pecas geradas para o mesmo id sao imagens diferentes. **Fica em aberto**: um
julgamento visual novo, sobre saida de translacao, e necessario para validar
os limiares de gate em cima do metodo que de fato vai pro build (ja listado
como pendencia na secao 7 do documento principal).

## 6. Preditor combinado -- regressao vs classificador, e por que o segundo venceu

Regressao linear (mesmo desenho do H5 v1, alvo = magnitude do erro) treinada
nos top-6 sinais por `|spearman|`, OOF 5-fold por peca: **35,4% de precisao,
50,7% de recall**.

**Problema identificado:** o alvo tem 82,4% de massa em zero (a translacao
acerta a maioria). Uma regressao que minimiza erro quadratico da magnitude
otimiza a pergunta errada -- "quao grande vai ser o erro" quando a pergunta
de produto e binaria, "vai ter erro ou nao". Troquei para um classificador
logistico (gradiente descendente com L2, numpy puro, sem scipy/sklearn),
alvo `erro_translacao > 0`, features escolhidas por correlacao ponto-bisserial:
**50,5% de precisao, 72,5% de recall** -- melhor, e estavel: testado com 21
sinais (todos), 3/4/6/8/10 sinais e L2 de 0,5 a 16, o resultado fica entre
48,5% e 50,5% em todas as variacoes. Nao e sensibilidade a escolha de
features -- e o teto real do sinal disponivel.

### O teto matematico do criterio, sob esta distribuicao

O criterio de sucesso foi fixado ANTES de medir: precisao >= 70% ao isolar o
**quartil pior** (25% da amostra sinalizados), OOF por peca. Sob o
transplante (baseline ~20% de exatos, a maioria da amostra ERRA), essa
definicao fazia sentido -- 25% sinalizados cabiam dentro de uma populacao
majoritariamente ruim. Sob a translacao, so **17,6%** das pecas (69 de 393)
tem erro > 0. Isso significa que, com o orcamento de sinalizacao fixo em 25%
(k=99), **nenhum classificador, nem um perfeito, consegue passar de
69/99 = 69,7% de precisao** -- sobram 30 vagas do "quartil" preenchidas
necessariamente por pecas que na verdade sairiam exatas. **O teto matematico
ja fica abaixo dos 70% exigidos**, antes mesmo de julgar a qualidade do
modelo.

| abordagem | k | precisao OOF | recall OOF |
|---|---|---|---|
| regressao linear (top6 spearman) | 99 (25%) | 35,4% | 50,7% |
| **classificador logistico (top6 biserial)** | 99 (25%) | **50,5%** | 72,5% |
| teto matematico dado o desbalanceamento | 99 (25%) | 69,7% | -- |
| diagnostico: `k` = quantidade real de erros (69) | 69 | 63,8% | 63,8% |
| diagnostico: `k` = top 10% de maior confianca | 40 | **82,5%** | 47,8% |

As duas ultimas linhas sao diagnostico, nao o veredito oficial (o criterio
foi fixado em 25%, nao em 10% nem no tamanho real da classe). Mas sao uteis
para produto: **um gate mais conservador (so os 10% mais suspeitos) cruza os
70% de precisao**, as custas de so pegar 47,8% dos casos ruins de fato --
ainda deixa mais da metade dos erros passar batido se usado sozinho.

## 7. Veredito contra o criterio de 70%

**NAO PASSA.** Precisao OOF no quartil pior (k=25% fixo, conforme o criterio
fixado antes de medir) = **50,5%**, contra o corte de 70%. E mais que "nao
alcancou por pouco": o proprio desenho do criterio (quartil fixo de 25%)
esta descasado da distribuicao real do erro sob translacao (so 17,6% erra),
o que capa qualquer classificador em 69,7% antes mesmo de comparar
qualidade de sinal.

**Isso e informacao valiosa, nao falha da pesquisa** (conforme a instrucao
de nao maquiar): confirma que a saida da translacao, quando erra, nao tem
sinal disponivel forte o bastante (sem olhar o gabarito) para separar
automaticamente "vai pro build" de "vai pra fila humana" com confianca alta
o suficiente para um gate de 25%. Um gate MUITO mais conservador
(sinalizar so os ~10% mais suspeitos) tem precisao aceitavel, mas continua
sendo triagem parcial, nao substituto de revisao.

## 8. Resposta de produto: quantas lacunas reais o preditor reprovaria

**Contagem usada, e por que:** nenhum dos tres numeros em disputa (3.666 /
2.041 / 2.864) -- todos somam varias animacoes (`idle`+`combat_idle`+`run`+
`sit`) e/ou varios corpos. O escopo desta pesquisa e so `idle`, corpo
`male`, `camadas[0]` (mesmo recorte da validacao das secoes 1-6, pra manter
o preditor e a producao na mesma populacao). Contagem propria, medida
diretamente do catalogo nesta rodada:

**62 lacunas reais de `idle`** (pecas com `walk` mas sem `idle` completo,
corpo male, `camadas[0]` nao-vazia) -- **todas** com a flag `legado=true` da
taxonomia (esperado: e exatamente a definicao do problema). Mais 27
excluidas por `camadas[0]` vazia (a mesma armadilha da secao 2, do lado da
lacuna: peca cuja camada 0 nao tem arte nenhuma, chifre/asa/cauda -- essas
nao sao resolviveis por NENHUM metodo de pixel, precisam de decisao de
produto, nao de preditor).

Funil, aplicando a tabela de producao (moda do slot treinada em TODAS as
pecas completas, sem LOO -- correto para deploy, porque a peca alvo real
nunca tem `idle` e portanto nunca poderia vazar pro proprio treino):

| etapa | n | % das 62 |
|---|---|---|
| lacunas reais (idle ausente, male, camada0) | 62 | 100% |
| sem par de treino no slot -> direto pra fila humana, preditor nem roda | 32 | 51,6% |
| com par de treino -> traduzivel, preditor roda | 30 | 48,4% |
| -- aprovadas pelo preditor (score < limiar) | 14 | 22,6% |
| -- **reprovadas pelo preditor** (score >= limiar) | 16 | 25,8% |

Distribuicao da nota (probabilidade logistica de erro>0) sobre as 30
traduziveis: minimo 0,012, mediana 0,126, media 0,260, maximo 0,804; limiar
usado e o p75 do TREINO (0,117, nao recalculado sobre esta amostra pequena).
**16 de 30 pecas traduziveis (53,3%) cairiam no limiar de reprovacao** --
mais da metade do que sobra depois do corte de cobertura.

**Leitura de produto:** das 62 lacunas reais de idle, so 14 (22,6%) sairiam
aprovadas para build automatico por este preditor; **48 das 62 (77,4%)** vao
para revisao humana de um jeito ou de outro -- 32 por falta de par de treino
no slot (nem chegam a gerar nada), 16 por reprovacao do preditor. Dado que o
preditor nao passa no criterio de 70%, essa reprovacao deve ser lida como
"suspeita, prioriza revisao" -- nao como um gate confiavel de aprovacao
automatica sozinho.

## 9. Limitacoes declaradas

- Amostra de validacao (n=393) e as 62 lacunas reais sao **so corpo male,
  camadas[0]** -- nao testado em female/child/teen/muscular/pregnant nem em
  pecas multi-camada.
- Classe positiva rara (17,6%) deixa o classificador com pouco material
  (69 casos de erro) para aprender nuance -- 5-fold OOF usa so ~14 exemplos
  positivos por fold de teste.
- Os sinais do juizo visual (`razao_maior_componente`, `queda_bbox_real`)
  confirmaram correlacao forte com o erro real SOB GABARITO, mas a checagem
  cruzada contra os 30 julgamentos humanos existentes e invalida por
  descompasso de metodo (rotulo dado olhando transplante, sinal calculado
  sobre translacao) -- fica pendente um julgamento visual novo sobre saida
  de translacao.
- O limiar de decisao (`limiar_score_p75`) foi calibrado no p75 da propria
  populacao de TREINO (n=393), nao recalibrado especificamente para a
  distribuicao das 62 lacunas reais (n pequeno demais para recalibrar sem
  overfit).
- `desvio_dy_dx` usa `walk0->walk1` como proxy do movimento natural da peca;
  para as poucas lacunas sem `walk k=1` (nenhuma nesta amostra, mas
  possivel em outro corte), o codigo usa o proprio deslocamento do slot como
  neutro -- decisao de fallback nao testada por falta de caso.

## Arquivos

- Codigo (scratchpad, nao versionado, reaproveita `lib.py`/`transplante.py`):
  `lib2.py`, `construir_v2.py`, `analise_v2.py`, `produto_v2.py` em
  `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/h5-preditor/`
- Dados: `validacao_v2.json` (393 registros, sinais + erro_translacao),
  `modelo_v2.json` (pesos da regressao e do logistico, correlacoes),
  `produto_v2.json` (score das 30 pecas traduziveis das 62 lacunas reais),
  `juizo_30_traducao.json` (sinais recalculados para os 30 ids julgados)
  -- todos no mesmo diretorio do scratchpad.
- Artefatos da rodada anterior (reaproveitados): `lib.py`, `validar.py`,
  `analise.py`, `modelo.json`, `validacao.json` no mesmo diretorio --
  mantidos como estao, o preditor deles segue valido SO para o transplante,
  nao para a translacao (ver `docs/2026-08-02_PESQUISA-transplante.md`,
  linha do H5 na tabela "O que NAO fazer").
