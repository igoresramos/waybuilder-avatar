# Pesquisa do transplante de animacao -- documento de decisao

Data: 2026-08-02
Escopo: 170 pecas legadas do acervo Waybuilder/LPC sem idle, combat_idle, sit e run.
Frentes: 3 de fundamentos, 5 de hipotese, 1 de ataque adversarial, 1 de juizo visual.

---

## 1. A PERGUNTA

O acervo tem 627 pecas; 170 sao do formato legado e nao possuem as animacoes novas -- a arte nao existe e ninguem vai desenha-la. A solucao em producao e o TRANSPLANTE: medir como os pixels de uma doadora se moveram entre duas poses e aplicar o mesmo movimento na peca que falta. A pergunta e: da para elevar a taxa de frames corretos acima do baseline atual de 20% e, se sim, mudando o que -- a escolha da doadora, o modelo de movimento, ou o escopo do que se tenta gerar?

Importa porque cada ponto percentual a mais e arte que entra no build sem passar por revisao humana, e cada frame errado que entra silenciosamente e um defeito visivel no avatar do usuario.

---

## 2. METODO

**Como foi medido.** Motor unico e nao reimplementado: `/home/igor0/waybuilder-avatar/transplante.py` (`sobreposicao`, `campo_de_deslocamento`, `aplicar_campo`, `pixels_diferentes`, `escolher_doadora`). Par canonico de frames: doadora walk k=0 -> idle k=1, aplicado ao alvo walk k=0, comparado com o alvo idle k=1. Erro sempre por `pixels_diferentes` (o que a tela mostraria; nao os 4 canais crus).

**Validacao.** Por peca, nunca por frame: a peca de teste jamais entra no treino. Nas hipoteses baseadas em tabela por slot, leave-one-out dentro do slot.

**Metricas.** Primaria: % de frames EXATOS (zero pixel errado). Secundaria: mediana de pixels errados. Terciaria (só para triagem): fracao da area da peca que saiu errada.

**Baseline.** Oficial declarado: 20,0% exatos / mediana 28 / media 42,7 / n=250 (doadora do mesmo slot por maior IoU). Recalculado de forma independente por seis frentes distintas, em amostras entre 250 e 493 pecas: 18,7% / 18,8% / 20,1% / 20,1% / 21,4% / 22,3%. **O baseline e solido: fica na faixa 18,7%-22,3% em toda amostra testada.** Controle nulo (nao mexer, copiar walk k=0): 5,3% a 6,0% de exatos, mediana 111-135 px.

**Criterios de sucesso, fixados antes de medir.**
- Hipotese VENCE se ganha **+3 pontos percentuais** ou mais em frames exatos contra o baseline recalculado na mesma amostra.
- Preditor de qualidade e UTIL se acerta **>= 70% de precisao no quartil pior** (identificar corretamente as pecas que vao sair ruins).

**Limites gerais.** Tudo medido no recorte frontal (o unico que o acervo tem), camada base, quadro k=1 do destino. Corpo male salvo onde indicado.

---

## 3. TABELA DAS HIPOTESES

Ordenada do maior ganho para o menor. Baseline sempre recalculado na mesma amostra da hipotese.

| # | Hipotese | Amostra | Baseline (exatos / mediana) | Medido (exatos / mediana) | Delta p.p. | Veredito |
|---|---|---|---|---|---|---|
| H1-idle | Translacao rigida por slot dispensa a doadora (walk->idle) | n=428 | 20,1% / 22 | **77,6% / 0** | +57,5 | VENCE -- mas ver secao 4, o numero e das pecas completas |
| H1-combat | Idem, walk->combat_idle | n=362 | 16,9% / 32 | **68,0% / 0** | +51,1 | VENCE (tabela reaplicada por aproximacao, nao revalidada por LOO) |
| H1-run | Idem, walk->run | n=369 | 13,3% / 37 | **59,3% / 0** | +46,0 | VENCE (idem) |
| Fundamento | Translacao rigida 1px (frente gramatica), LOO por slot | n=463 | 18,5% | **71,9%** | +53,4 | VENCE -- reproduz H1 de forma independente |
| H5 | Preditor de qualidade pre-transplante (regressao em 5 sinais) | n=393 (359 com doadora) | -- | precisao OOF **82,8%**, recall 81,2%, spearman 0,85 no quartil pior (k=99) | passa o corte de 70% | PARCIAL -- passa no proprio setup (prever erro do TRANSPLANTE); aplicado sobre a saida da TRANSLACAO inverte (spearman -0,08; aprovados 72,2% exatos contra reprovados 82,9%). **Relatorio final ausente em docs/; so existem artefatos de scratch** |
| H2 | Cortar sit do build | n=366 | sit: 3,3% (fazer-nada) | sit: 3,6% | +0,3 | PERDE em sit -- e por isso CONFIRMA o corte: gerar sit nao bate nem o fazer-nada |
| H4 | Indice de rampa amplia o pool de doadoras | n=427 (282 indexaveis) | 20,1% / 20 | 19,9% / 20 | -0,2 | PERDE |
| H3 | Campo de deslocamento por regiao em vez de global | n=457 / 421 / 416 | 18,8% / 25 | 15,5% / 27 | -3,3 | PERDE em todos os 6 experimentos |
| H1-sit | Translacao rigida em walk->sit | n=374 | 0,5% / 123 | 0,0% / 245 | -0,5 | PERDE |
| Taxonomia | Doadora restrita ao mesmo material | n=493 | 18,7% / 25,5 | 14,2% / 33 | -4,5 | PERDE -- unica restricao que perde nas tres metricas |
| Taxonomia | Doadora livre por IoU (sem restricao de slot) | n=493 | 18,7% / 25,5 | 18,5% / 22 | -0,2 | EMPATA em exatos, melhora mediana e cobertura (493/493 contra 460/493) |

Ablacao do pipeline combinado (n=428, idle): retirar a translacao derruba os exatos de 77,6% para 20,3%; retirar a doadora livre por IoU deixa **exatamente 77,6%**. **Todo o ganho vem de H1. Nenhuma outra hipotese cria um unico frame exato a mais nesta amostra.**

---

## 4. O QUE O ATAQUE DERRUBOU

Seis ataques confirmaram, tres nao confirmaram. Em ordem de gravidade.

### 4.1 O numero de manchete e das pecas que JA TEM a arte (ATAQUE 6 -- decisivo)

Mesmo par, mesmo protocolo LOO, separando a populacao:

| Populacao | n | Exatos | Media de erro |
|---|---|---|---|
| Pecas completas (ja tem idle) | 388 | **82,0%** | 18,6 |
| Pecas de formato legado (as que faltam) | 76 | **53,0%** | 42,7 |
| Legadas, com treino vindo so de completas | 15 de 76 | **13,2% efetivo** (cobertura 15/76) | -- |

**Invalida:** o 77,6% como numero de entrega. O numero honesto para o problema real e **53,0%**, e cai para 13,2% efetivo quando o slot nao tem outra legada para ensinar o deslocamento -- que e o caso normal, porque 113 das 166 legadas medidas nao tem NENHUMA peca nao-legada no proprio slot.

**A premissa da H1 nao vale nas legadas.** Existe (dy,dx) com erro zero em 83,5% das completas contra 55,3% das legadas. E o deslocamento otimo e (0,0) -- nao mexer -- em 39,5% das legadas contra 12,1% das completas. A tabela aprendida nas completas tem moda esmagadora (-1,0): ela vai empurrar 1 px para cima peca que nao se mexe.

As legadas sao outra populacao de arte, medido no walk k=0: area mediana 101 px contra 209,5; 25,8% com mais de 6 tons contra 18,3% (37,9% no subgrupo sem idle); alfa parcial em 1,8% contra 6,2%.

**Consequencia direta:** H1 permanece na tabela de recomendacoes, mas **com o numero corrigido de 53,0% e nao 77,6%**, e com cobertura de 28,2% das lacunas.

### 4.2 Frames vazios contavam como acerto (ATAQUE 1b)

A H2 mediu `camadas[0]` e 13 das 366 pecas tem essa camada VAZIA (chifres, asas, caudas, escudo). Vazio contra vazio pontuava como frame exato. Recontando nos proprios `resultados.json` da H2:

| Animacao | H2 publicado | H2 corrigido |
|---|---|---|
| idle | 24,9% | **22,1%** |
| combat_idle | 20,5% | **17,6%** |
| run | 17,2% | **14,2%** |
| sit | 3,6% | **0,0%** |

**Invalida:** todos os percentuais publicados pela H2, e em particular o "empate estatistico" de sit -- 12 dos 13 exatos de sit eram quadros vazios. **sit sai do build por 0,0% de exatos reais, nao por empate.** A conclusao qualitativa da H2 (cortar sit, cortar pernas/pes em combat_idle e run) sobrevive; os numeros dela nao.

### 4.3 Arte duplicada infla toda medicao (ATAQUE 1)

13 grupos de arte byte a byte identica sob ids diferentes (26 itens), todos dentro do mesmo slot -- `hat/bascinet` = `hat/round-bascinet`, `head/wolf-female` = `head/wolf-male`. Como a doadora e a alvo sao o mesmo PNG, os dois metodos acertam 100%.

Removendo-as: baseline transplante cai de 20,1% para **14,9%**; translacao cai de 77,6% para **76,1%**.

**Invalida:** ate 5 pontos percentuais de qualquer medicao futura. Favorece a hipotese vencedora (o baseline cai mais que a translacao), mas contamina o pool de doadoras -- essas pecas nao ensinam nada.

### 4.4 A translacao particiona o acervo, nao o melhora (ATAQUE 4)

| Subpopulacao | n | Translacao | Transplante |
|---|---|---|---|
| Pecas rigidas (existe (dy,dx) exato) | 337 | **98,5% exatos** | 25,5% |
| Pecas nao-rigidas | 91 | **0,0% exatos**, mediana 88 | 0,0% exatos, mediana **51** |

Nas nao-rigidas a translacao e **pior** que o transplante, e o proprio teto teorico dela ja e mediana 76. E quando ela falha, falha mais fundo: fracao de area errada mediana 0,454 e 80,2% dos fracassos acima de 25% da area, contra 0,192 e 38,9% do transplante.

**Invalida:** a leitura de que H1 "melhora o pipeline". Ela melhora dramaticamente 78,7% das pecas e piora a cauda. O roteador correto nao e por slot, e por **rigidez da peca**.

### 4.5 Regressao pura medida

Transladar e pior que nao mexer em 13 de 428 pecas. Em 2 delas -- `hat/formal-bowler-hat` e `hat/tiara` -- **nao mexer era EXATO** e a tabela do slot introduziu 193 e 40 pixels de erro. Prova visual em `docs/2026-08-02_ataque-metrica.png`. E em 25 pecas (5,8%) o deslocamento do slot discorda do otimo da propria peca.

### 4.6 O tamanho da entrega nao esta estabelecido

Tres contagens independentes do numero de lacunas reais, nenhuma reconciliada:

- 3.666 -- numero oficial em circulacao, **nao reproduzido por nenhuma frente**
- 2.041 -- contagem da frente combinado (definicao mais estrita)
- 2.864 celulas item x corpo x animacao / 11.495 frames -- contagem da frente de ataque

Cobertura da tabela por slot sobre as 2.864: **28,2%** no total -- idle 61,4%, combat_idle 33,4%, run 18,9%, sit 16,9%. `shield_pattern` (240 celulas), `weapon` (117) e `charm` (80) nao tem parceiro nenhum.

**Invalida:** qualquer projecao de entrega feita sobre o numero de 3.666.

### 4.7 O erro em pixels sozinho nao decide o aceite (frente de juizo visual)

30 pecas julgadas a olho (10 baixo / 10 medio / 10 alto erro): 16 aceitavel, 9 duvidosa, 5 inaceitavel. Contra-exemplo confirmado nas duas pontas: `hat_accessory/bicorne-athwart-admiral-cockade` com erro de **21 px** e INACEITAVEL (peca de so 37 px de area, fragmentou), enquanto `clothes/longsleeve` com erro de **51 px** -- mais que o dobro -- e ACEITAVEL (forma continua certa, so o sombreamento escorregou).

O erro absoluto correlaciona bem no agregado (Spearman 0,92, melhor que o percentual da area, 0,78), mas erra exatamente nas pontas. O que decide e o TIPO de pixel errado: fragmentacao (pior) > amputacao de ponta/mecha > cor errada > falta de detalhe fino.

**Invalida:** qualquer gate de aceite baseado em limiar unico de `pixels_diferentes`.

### 4.8 O que o ataque NAO derrubou

- **ATAQUE 2 (medicao em k errado):** nao confirma. A H1 mediu k=1 mesmo; reproduzidos 77,6/0/22,3 e 20,1/22/42,1. Medir em k=0 daria 87,1% de graca e inverteria o veredito nas 55 pecas nao triviais -- mas nao foi o que foi feito.
- **ATAQUE 3 (ganho vem de pecas faceis):** nao confirma. Macro-media por slot 78,1%; sem os 6 maiores slots sobe para 82,6%; tirando as ja-exatas do baseline, 71,9%.
- **ATAQUE 5 (nao generaliza entre corpos):** nao confirma. male 77,6%, female 77,4%, teen 77,1%, muscular 84,7%, pregnant 83,0%, child 90,1% -- os 6 corpos, so em walk->idle.

---

## 5. O QUE SOBROU DE PE

Com numero, depois do ataque.

1. **A translacao rigida bate o transplante, com folga, no problema real.** Em alvo legado de fato: **53,0% de frames exatos contra 0,0% do transplante** (n=76, LOO). Em alvo legado com par de treino utilizavel: **64,3% contra 0,0%** (n=14 de 50).
2. **O deslocamento e majoritariamente (-1, 0) e coerente por slot.** 78,7% das pecas do acervo admitem uma translacao exata; nelas a doadora e irrelevante (98,5% de exatos).
3. **idle k=0 sai de graca.** walk k=0 e identico byte a byte ao idle k=0 em 88,4% de 493 pecas (e em 92,6% de 391 na frente de movimento). Metade do escopo de idle nao precisa ser gerada.
4. **sit nao entra no build.** 0,0% de exatos reais em 349 e em 366 pecas, todas as regioes, mediana 118-123 px de erro; 96,2% das pecas com mais de 25% da area errada. Nem a translacao (0,0%) nem o transplante (0,5%) produzem arte aproximada.
5. **Material e zPos estao mortos como criterio de doadora.** Material derruba os exatos de 18,7% para 14,2% e piora a mediana de 25,5 para 33. zPos, restrito as 113 legadas orfas de slot, da IoU mediano **0,021** e zero pecas acima de 0,50 -- colapso total exatamente onde seria preciso.
6. **A busca livre por IoU e o melhor fallback, mas nao um ganho.** Cobre 493/493 contra 460/493 do slot, melhora a mediana de 25,5 para 22 -- e na ablacao do pipeline final produz **efeito zero** em frames exatos. Vale pela cobertura, nao pela qualidade.
7. **Campo por regiao (H3) e indice de rampa (H4) estao descartados.** H3 perde nos 6 experimentos e cria erro de costura de +23% a +26% na fronteira entre regioes. H4 nao toca o gargalo: a comparacao doadora/alvo ja e cor-invariante hoje, e das 14 orfas indexaveis **zero** ganharam candidata nova.
8. **A escolha da doadora tem teto baixo.** Com oraculo (melhor doadora possivel), os exatos vao de 23,6% para 30,2% em idle e de 15,1% para 21,1% em run. Investir em escolha de doadora rende no maximo **+6 p.p.** O gargalo e o modelo de movimento, nao a doadora.
9. **Para run, o IoU e cego.** Correlacao entre IoU da pose de partida e erro final: **-0,001** em run contra -0,60 em idle. Escolher doadora por IoU para uma pose girada e escolher no escuro.
10. **A gramatica do LPC e fechada -- com uma ressalva.** Alfa binario (95,23% em 0, 4,76% em 255, zero intermediario em 80 pecas), rampa de 6 tons, luz sem componente lateral (dx mediano -0,01, 50/50) -- o que autoriza doadora espelhada horizontalmente. **Ressalva:** 25,8% das legadas tem mais de 6 tons (37,9% no subgrupo sem idle), entao a projecao de volta na rampa de 6 tons **nao e gratuita** para elas, ao contrario do que a frente de gramatica afirmou.

---

## 6. RECOMENDACAO

**Houve ganho real, e ele e grande -- mas e menor do que o numero de manchete e cobre menos de um terco do problema.** O pipeline recomendado entrega frame exato para cerca de **53% das lacunas de idle que tem par de treino no slot**, e ha par de treino em apenas **28,2% das 2.864 lacunas** (61,4% em idle, 18,9% em run). Tudo o mais e preenchimento plausivel para fila humana, nao arte correta. Nenhuma das outras quatro hipoteses testadas produziu ganho.

### O que virar codigo, em ordem

**1. Copiar walk k=0 para idle k=0.** Zero processamento. Correto em 88,4% de 493 pecas medidas. Corta metade do escopo de idle.

**2. Remover as 26 pecas de arte duplicada do pool de doadoras** (13 pares byte a byte dentro do mesmo slot: `hat/bascinet`=`hat/round-bascinet`, `head/wolf-female`=`head/wolf-male`, etc.). Elas nao ensinam nada e inflam qualquer medicao futura em ate 5 p.p.

**3. Roteador por rigidez, nao por slot.** Para cada peca legada, antes de aplicar qualquer coisa:
   - Se o slot tem **>= 3** pecas de treino nao-legadas e **>= 80%** delas concordam no (dy,dx) otimo -> aplicar a translacao do slot.
   - Caso contrario -> **nao mexer** (copiar walk k=0).
   - **Parametros 3 e 80% NAO foram medidos.** Sao escolha conservadora derivada de dois fatos medidos: o deslocamento otimo e (0,0) em 39,5% das legadas, e o slot discorda do otimo da peca em 5,8% dos casos. Calibrar antes do build (custo: ~1h, ver secao 7).

**4. Tabela de deslocamento: usar so os 44 slots validados por leave-one-out.** O arquivo `docs/2026-08-02_h1-tabela-slot.json` traz 80 slots com (dx,dy), mas **36 deles vem de 1 unica peca de treino, sem validacao cruzada** -- esses vao para revisao manual, nao para o build. Os 22 slots restantes do catalogo nao tem parametro nenhum.

**5. Fallback de doadora: busca livre por IoU no acervo inteiro,** nunca restrita a material, zPos ou slot. Cobre 493/493. Filtros baratos vindos da gramatica: nunca cruzar camada bg (zPos < 10) com camada fg da mesma peca (geometrias distintas); permitir doadora espelhada horizontalmente (a luz do LPC nao tem componente lateral -- dobra o pool). **Esperar mediana ~22 px de erro e ~0% de exatos em alvo legado (medido: 1,3% de exatos, mediana 36,5). Isso e fila de revisao, nao build.**

**6. Corte de escopo, em codigo:**
   - `sit` -> **nunca gerar**, sempre fallback parado. 0,0% de exatos reais.
   - Dentro de `combat_idle` e `run` -> peca com pixel em pernas ou pes cai no fallback parado (0,0% de exatos nas 4 celulas, mediana 10-38 px, fracao de area errada 37,5% a 90,2%).
   - `idle` em pes e pernas -> caso trivial, 60,0% e 44,4% de exatos.

**7. Gate de aceite com tres sinais, nao um limiar de pixels.** Manda para fila humana se qualquer um disparar:
   - `maior_componente_gerado / maior_componente_real < 0,75` (fragmentacao -- inaceitavel nos 3 piores casos julgados: cockade 0,43, bandana/mail 0,46)
   - queda de altura ou largura do bbox **> 15-20%** (amputacao de ponta/mecha)
   - fracao da area errada **> 0,25**
   - **Limiares derivados de n=30 pecas julgadas a olho por um unico avaliador.** Direcionalmente corretos, quantitativamente nao validados.

### O que NAO fazer, e por que

| Nao fazer | Motivo medido |
|---|---|
| Escolher doadora por **material** | Derruba exatos de 18,7% para 14,2% e mediana de 25,5 para 33 (n=493). Alem disso metal x metal (IoU 0,213) empata com metal x hair (0,212), e 140 das 170 legadas nao declaram material |
| Escolher doadora por **zPos** | Nas 113 legadas orfas de slot: IoU mediano 0,021, zero pecas acima de 0,50. E o ganho aparente de 5,20x e emprestado do slot (84 de 102 slots tem um unico zPos) |
| **Campo de deslocamento por regiao** (H3) | Perde nos 6 experimentos (15,5% contra 18,8% em idle; 7,1% contra 11,6% em run). A costura entre regioes adiciona +23% a +26% de erro na fronteira e ~2% no interior |
| **Indice de rampa** para ampliar o pool (H4) | 19,9% contra 20,1%. A comparacao doadora/alvo ja e cor-invariante (usa so alfa). Das 14 orfas indexaveis, zero ganham candidata nova. E a indexacao nem e lossless: so 81,3% das pecas casam 100% da rampa |
| Investir em **melhor escolha de doadora** | Teto de oraculo: +6,6 p.p. em idle, +6,0 em run, +0,0 em sit. O gargalo e o modelo de movimento |
| Escolher doadora por **IoU quando o destino e run** | Correlacao IoU x erro = -0,001. Escolha no escuro |
| Gerar **sit** | 0,0% de exatos reais em duas amostras independentes (n=349 e n=366) |
| Usar o **preditor H5 como esta** sobre a saida da translacao | Spearman(score, erro) = -0,08; aprovados 72,2% exatos contra reprovados 82,9% -- ele **inverte** a selecao. Ele foi treinado para prever erro do transplante, nao da translacao |
| Projetar a saida na **rampa de 6 tons** como passo "gratuito" | 25,8% das legadas tem mais de 6 tons (37,9% no subgrupo sem idle). Para essas a projecao destroi informacao |
| Dimensionar a entrega pelo numero **3.666** | Nao reproduzido por nenhuma frente. As contagens proprias deram 2.041 e 2.864 |

---

## 7. O QUE CONTINUA EM ABERTO

| Pergunta | Por que importa | O que custaria responder |
|---|---|---|
| **Quantas lacunas existem de fato?** 3.666, 2.041 ou 2.864 celulas? | Toda projecao de entrega depende disso; a divergencia e de 80% | Acordar a definicao (item x corpo x animacao x frame?) e rodar uma contagem unica sobre o catalogo. ~1h |
| **Os 36 slots inteiramente legados** (weapon, charm, belt, bracers, chainmail, ring, prosthesis_hand/leg, bauldron...) -- qual (dy,dx)? | Sao 437+ celulas sem nenhuma peca de referencia no proprio slot. Nao existe como medir generalizacao | Nao ha caminho automatico. Revisao visual peca a peca, ou aceitar (0,0) e mandar para fila humana |
| **Calibrar o roteador por rigidez** (limiares de 3 pecas e 80% de concordancia) | Sao os unicos parametros do pipeline que foram chutados | Varredura de limiar por LOO sobre as 428 pecas ja medidas, otimizando exatos e penalizando regressoes. ~1-2h |
| **O guard de regressao e implementavel?** O ataque recomenda escolher entre transladar e nao-mexer pelo menor erro -- mas isso exige o frame verdadeiro, que nao existe nas legadas | Recuperaria as 13 pecas que a tabela piora, inclusive as 2 que eram exatas | Precisa de um proxy sem verdade (ex.: concordancia do slot, ou o proprio preditor H5 retreinado sobre saida de translacao). ~1 dia |
| **H5 -- o relatorio final nunca chegou** | O modelo passa o criterio de 70% (precisao OOF 82,8%, n=99 no quartil pior), mas so foi validado prevendo erro do transplante; sobre a translacao ele inverte | Retreinar sobre `erro_translacao` como alvo e revalidar OOF. Artefatos ja existem em scratch (`modelo.json`, `validacao.json`, n=393). ~2-3h |
| **combat_idle e run: a tabela por slot nao foi revalidada por LOO** | Os 68,0% e 59,3% vem de reaplicacao por aproximacao da tabela de idle | Rodar o mesmo protocolo LOO nesses dois pares. ~2h |
| **A regra de rigidez vale nos outros 5 corpos?** | Generalizacao foi testada so em walk->idle (male 77,6% a child 90,1%); a taxonomia toda foi medida so no male | Repetir a particao rigida/nao-rigida nos 6 corpos. ~2h |
| **O juizo visual tem n=30 e um unico avaliador** | Os tres limiares do gate de aceite saem dai | Julgamento humano (Igor) sobre 60-100 pecas estratificadas, cegas quanto ao erro medido. ~1-2h de revisao |
| **Direcao: so frontal** | O acervo so tem frontal, entao a pergunta so aparece se o build precisar de costas | Ler zPos <= 8 como proxy de costas. Nao medido |
| **4 pecas com silhueta vazia de frente** (backpack/backpack, backpack/jetpack, backpack/square-pack, cargo/jetpack-fins) | Nao e falta de doadora, e falta de pixel -- nenhum metodo resolve | Decisao de produto: excluir ou desenhar |

---

## Indice das frentes

| Frente | Relatorio |
|---|---|
| Gramatica do LPC | `docs/2026-08-02_pesquisa-gramatica-lpc.md` |
| Taxonomia dos assets | `docs/2026-08-02_pesquisa-taxonomia.md` + `docs/2026-08-02_taxonomia.json` |
| Anatomia do movimento | `docs/2026-08-02_pesquisa-movimento.md` + `docs/2026-08-02_mapa-de-movimento.json` |
| H1 translacao rigida | `docs/2026-08-02_pesquisa-h1-translacao-rigida.md` + `docs/2026-08-02_h1-tabela-slot.json` |
| H2 escopo do que gerar | `docs/2026-08-02_pesquisa-h2-escopo-do-que-gerar.md` |
| H3 campo local | `docs/2026-08-02_pesquisa-h3-campo-local.md` |
| H4 indice de rampa | `docs/2026-08-02_pesquisa-h4-indice-de-rampa.md` |
| H5 preditor de qualidade | **AUSENTE** -- so artefatos de scratch (`h5-preditor/modelo.json`, `validacao.json`) |
| Combinado | `docs/2026-08-02_pesquisa-combinado.md` |
| Ataque adversarial | `docs/2026-08-02_pesquisa-ataque.md` + `docs/2026-08-02_ataque-metrica.png` |
| Juizo visual | `docs/2026-08-02_pesquisa-juizo-visual.md` + `docs/2026-08-02_amostra-visual/` (30 PNG) |
