# H6 -- O Combinado

Junta os critérios que venceram nas frentes H1-H4 (mais o achado de doadora livre por IoU da fase 1), mede o conjunto contra o baseline, faz ablação e aplica o preditor de qualidade da H5 por cima.

**Veredito resumido: VENCE, e por larga margem, mas o ganho inteiro vem de UM critério.** A translação rígida por slot (H1) carrega 100% do ganho medido em % de frames exatos, nas três animações onde importa (idle, combat_idle, run). Os outros dois ingredientes do combinado -- doadora livre por IoU no fallback e o roteamento entre os dois métodos -- **não criam nenhum frame exato a mais nesta amostra**: a doadora livre escolhe exatamente a mesma doadora que a doadora do mesmo slot escolheria (ablação idêntica byte a byte), e o roteamento só reduz o tamanho do erro nos casos que já dariam 0% de qualquer jeito. O preditor de qualidade da H5, aplicado sem adaptação ao combinado, **não transfere** -- inverte a seleção (itens "reprovados" saem com mais frames exatos que os "aprovados").

## Nota sobre a H5

O relatório da H5 ("preditor de qualidade sem gabarito") não chegou a esta sessão -- não existe `docs/2026-08-02_pesquisa-h5-preditor-de-qualidade.md` e o resumo das hipóteses recebido como contexto não trazia H5. Encontrei os artefatos de trabalho de uma execução anterior da H5 em `scratchpad/h5-preditor/` (`modelo.json`, `validacao.json`, `lib.py`, `validar.py`, `analise.py`), com um modelo já treinado e validado: regressão linear em 5 sinais (orfaos, area_var, area_antes, mag_max, mudanca_esperada), padronizados por z-score, avaliada por 5-fold CV por peça em n=393 -- **precisão de 82,8% no quartil pior (critério de sucesso >=70%, H5 teria vencido)**. Não tenho como confirmar que esse foi o relatório final entregue (pode ter falhado depois de gravar os artefatos), então tratei os parâmetros do `modelo.json` como "o preditor que a H5 entregaria" e apliquei-os ao combinado exatamente como a tarefa pediu -- com essa ressalva registrada.

## 1. O gerador combinado -- parâmetros exatos

Para os pares `walk k=0 -> {idle, combat_idle, run} k=1`:

1. **Roteamento por slot** (fixado pela tabela de H1, `decisao_por_slot_idle.json`, 44 slots validados por leave-one-out): se o slot tem `usar_transplante_no_lugar = false`, aplica a **translação rígida** `(dy, dx)` daquele slot (moda do deslocamento ótimo, raio de busca 4px). Se `usar_transplante_no_lugar = true` (apenas 3 slots: **clothes, shield_pattern, sleeves** -- os únicos onde a mediana de erro do transplante bate a da translação), cai no fallback de transplante.
2. **Fallback de transplante**: doadora escolhida por **maior IoU no acervo inteiro** (não restrita ao slot -- achado da fase 1/taxonomia), campo de deslocamento **global** (`campo_de_deslocamento` padrão do motor, raio=6 patch=5 -- H3 mediu que campo por região perde), **sem** conversão para índice de rampa (H4 perdeu, e a comparação já é cor-invariante por construção).
3. **Slots fora da tabela validada** (nunca observados com o par completo em H1 -- a maioria dos slots 100% legados: weapon, charm[\*], belt, jacket, etc.): tratados como "sem parâmetro medido", roteados por segurança para o fallback de transplante (nunca aplica translação não-validada).
4. **`sit` fica fora do build.** H1 perde nessa animação (0,0% vs 0,5% do transplante, com erro MAIOR: mediana 245px contra 123px) e H2 já havia medido 0,0% de exatos em todas as 349 peças e todas as regiões. Fallback = pose parada (copiar `walk k=0`).

\* nota: `charm` aparece como slot validado de alta confiança na tabela de H1 (100%→ aqui 96%+ nas medições), mas a maioria das peças `charm` do acervo real é legada e cai em "sem parâmetro medido" porque não tem par completo -- ver seção 5.

## 2. Medido contra o baseline, validação por peça

Baseline recalculado na mesma amostra em cada linha: transplante, doadora do mesmo slot por maior IoU (protocolo oficial).

| destino | n | baseline exatos | baseline mediana | baseline média | **combinado exatos** | **combinado mediana** | **combinado média** |
|---|---|---|---|---|---|---|---|
| idle | 428 | 20,1% | 22,0 | 42,1 | **77,6%** | **0,0** | **16,4** |
| combat_idle | 362 | 16,9% | 32,0 | 56,6 | **68,0%** | **0,0** | **49,0** |
| run | 369 | 13,3% | 37,0 | 73,3 | **59,3%** | **0,0** | **63,5** |
| sit | 374 | 0,5% | 123,0 | 140,7 | **excluído do build** | -- | -- |

Os números de idle/combat_idle/run reproduzem exatamente os que a H1 já havia reportado (77,6% / 68,0% / 59,3%) -- não é coincidência: a maior parte do combinado É a tabela de H1, como a ablação abaixo confirma. `combat_idle` e `run` usam a MESMA tabela de roteamento derivada em `idle` (nenhum slot fora da tabela apareceu nessas populações), o que é uma aproximação não revalidada por LOO separadamente para essas duas animações -- ver Limitações.

## 3. Ablação -- qual critério carrega o ganho

Retirando um critério de cada vez, mesma amostra (idle, n=428; padrão idêntico em combat_idle e run, tabela completa abaixo):

| variante | exatos | mediana | média |
|---|---|---|---|
| **(A) combinado completo** (translação roteada + transplante livre-IoU no fallback) | **77,6%** | 0,0 | 16,4 |
| (B) sem translação -- 100% transplante livre-IoU | 20,3% | 21,0 | 37,5 |
| (C) sem livre-IoU -- fallback usa mesmo-slot em vez de livre | 77,6% | 0,0 | 16,4 |
| (D) sem roteamento -- translação aplicada cegamente em tudo, sem fallback | 77,6% | 0,0 | 22,3 |

Mesmo padrão em combat_idle (n=362) e run (n=369):

| destino | (A) completo | (B) sem translação | (C) sem livre-IoU | (D) sem roteamento |
|---|---|---|---|---|
| combat_idle | 68,0% / 0,0 / 49,0 | 16,9% / 32,0 / 53,1 | 68,0% / 0,0 / 49,0 | 68,0% / 0,0 / 59,8 |
| run | 59,3% / 0,0 / 63,5 | 13,6% / 37,0 / 71,0 | 59,3% / 0,0 / 63,5 | 59,3% / 0,0 / 71,1 |

**Leitura, com número:**

- **(A) vs (B): a translação carrega TODO o ganho de % exatos.** Tirá-la derruba os exatos de 77,6% para 20,3% (idle), de 68,0% para 16,9% (combat_idle), de 59,3% para 13,6% (run) -- de volta ao patamar do baseline. Este é o único critério indispensável.
- **(A) vs (C): a doadora livre por IoU não muda NADA neste combinado -- 77,6% = 77,6%, byte a byte.** Motivo medido: nos 51 itens dos 3 slots roteados para transplante (clothes/shield_pattern/sleeves), a busca livre no acervo inteiro escolhe **exatamente a mesma doadora** que a busca restrita ao mesmo slot escolheria (mediana de erro idêntica, 44,0px, nos dois casos). O achado "livre-IoU melhora a mediana" da fase 1 (taxonomia) era verdadeiro na amostra ampla daquela frente, mas não se manifesta neste subconjunto específico -- aqui o critério é enfeite.
- **(A) vs (D): o roteamento não cria nenhum frame exato a mais** -- % exatos idêntico entre aplicar translação em tudo (D) e rotear (A)/(C). O que o roteamento faz é reduzir o tamanho do estrago nos casos que já davam 0% de qualquer jeito: nos 51 itens de clothes/shield_pattern/sleeves, translação cega dá mediana 98px de erro contra 44px do transplante -- por isso a MÉDIA da população cai (22,3 -> 16,4 em idle; 59,8 -> 49,0 em combat_idle; 71,1 -> 63,5 em run) mesmo com % exatos igual. Roteamento vale para a média/mediana de dano, não para taxa de acerto.

**Conclusão da ablação: dos 3 critérios do combinado, só 1 (translação rígida por slot) é responsável pelo ganho de %exatos. Os outros 2 (doadora livre, roteamento) têm efeito zero ou marginal nesta amostra específica -- valem por reduzirem o pior caso, não por criarem acerto novo.**

## 4. Preditor de qualidade da H5, aplicado por cima -- FALHA a transferir

Apliquei o modelo da H5 (coeficientes congelados, sem retreinar) ao combinado inteiro (idle, n=428): `score = intercepto + Σ peso_i · z(sinal_i)`, sinais = orfãos/area_var/area_antes/mag_max/mudança_esperada, corte no percentil 75 do score de treino original (limiar=52,44).

| | n | % exatos |
|---|---|---|
| todos | 428 | 77,6% |
| **aprovados** (score < limiar) | 212 | **72,2%** |
| **reprovados** (score >= limiar) | 216 | **82,9%** |
| spearman(score, erro real) neste pipeline | -- | **-0,08** (ruído) |

**Isso é o preditor invertido: os "reprovados" saem MAIS exatos que os "aprovados".** Cortar pelas piores segundo H5 pioraria a seleção, não melhoraria. Diagnóstico com número:

- H5 foi calibrado numa população onde o erro é quase sempre positivo e contínuo (baseline: só 20,1% de exatos, a maioria dos frames erra ALGO). No combinado, **77,6% dos frames saem com erro exatamente zero** -- a distribuição do erro deixou de ser contínua e virou bimodal (zero ou muito grande). A própria fórmula do "quartil pior" degenera: `quantile(erro, 0.75) = 0`, então o corte de quartil não separa mais nada de útil (confirmado: precisão 100%/recall 25% no cálculo cru, mas isso é artefato de o quartil de 0,75 cair dentro da massa de zeros, não sinal real).
- Restrito ao subconjunto onde o mecanismo de geração é o mesmo que treinou a H5 -- os 51 itens do fallback de transplante (clothes/shield_pattern/sleeves) --, o preditor **retém sinal parcial**: spearman sobe para **+0,56** (contra 0,85 na população nativa de H5, mas ainda direcionalmente correto e longe de ruído). No subconjunto de translação (n=377), o spearman é **-0,06**, ruído puro -- não há "orfãos" nem "campo" de verdade numa translação rígida, os sinais da H5 não descrevem esse mecanismo.

**Recomendação corrigida** (não pedida literalmente no passo 4, mas necessária para responder honestamente "quantas sobram"): não aplicar o preditor da H5 em itens gerados por translação -- ali a confiabilidade já é conhecida de forma determinística pela própria tabela de H1 (33 slots de alta confiança, 8 de baixa, ver seção 5). Aplicar H5 (com a ressalva de spearman 0,56, não 0,85) só nos itens que passam pelo fallback de transplante.

**Resposta literal ao passo 4:** com o combinado + corte das piores pelo preditor de H5 tal como entregue, sobram 212 itens (49,5% da amostra) com 72,2% de exatos entre eles -- **pior** que os 77,6% da população inteira e pior que os 82,9% dos "reprovados". O corte, aplicado sem adaptação, não deveria entrar em produção.

## 5. As 3.666 lacunas reais -- quantas em cada faixa

**Não tive acesso, nesta sessão, ao método que produziu o número oficial de 3.666.** Recalculei de forma independente via `taxonomia.json` + `catalogo.json`: para cada uma das 170 peças legadas, para cada um dos 6 corpos onde a peça existe **por completo** (todas as camadas da peça têm aquele corpo), conto as animações de `{idle, combat_idle, sit, run}` que faltam. Cheguei a **2.041** lacunas -- número diferente do declarado, provavelmente porque a contagem oficial usa um critério mais permissivo de "corpo disponível" (ex.: contar se QUALQUER camada tem o corpo, não todas). Reporto a distribuição nos dois números: a minha (2.041, medida) e a proporcional ao 3.666 oficial (fator 1,796, assumindo a mesma composição -- **essa proporcionalidade não foi verificada**, é a melhor aproximação possível sem o método original).

Classifiquei cada lacuna pelo slot da peça, usando a tabela de roteamento de H1 (idle-derivada, aplicada às 4 animações por aproximação -- mesma ressalva da seção 2):

| faixa de qualidade | critério | minha contagem (n=2.041) | % | proporcional a 3.666 |
|---|---|---|---|---|
| **excluído do build** | animação = sit, qualquer slot | 538 | 26,4% | ~966 |
| **alta confiança** | slot com taxa_exatos_translacao >=80% (33 slots: hair, hat, head, ears, neck, shoes, vest...) | 301 | 14,8% | ~541 |
| **baixa confiança / revisão** | slot validado mas taxa_exatos_translacao <80% (8 slots: legs, armour, cape, overalls, sash_tie, hairextl/r, wings) | 183 | 9,0% | ~329 |
| **lixo esperado / revisão obrigatória** | slot roteado para transplante (clothes, shield_pattern, sleeves) -- medido 0% de exatos | 45 | 2,2% | ~81 |
| **sem parâmetro medido** | slot nunca observado com par completo em nenhuma frente (weapon, charm[a maioria], belt, jacket, necklace[a maioria], bracers, chainmail, quiver, wrists[a maioria], earrings, arms...) | **974** | **47,7%** | **~1.749** |

**O achado que mais importa aqui: quase metade das lacunas reais (47,7%) caem em slots para os quais NENHUMA frente desta pesquisa tem parâmetro medido -- nem translação, nem doadora, nem preditor.** Não é que o método falhe nelas; é que não há dado para prever o resultado. Isso bate com o achado já registrado pela frente de taxonomia ("113 das 166 peças legadas medidas não têm NENHUMA peça não-legada dentro do próprio slot") e pela H1 ("36 dos 50 peças legadas reais não têm par de treino no próprio slot"). É o maior buraco aberto da pesquisa inteira, maior que qualquer diferença entre os métodos testados.

## 6. Limitações declaradas

- Medido só no corpo `male`, camada 0, direção frente -- não testado em female/child/muscular/pregnant/teen nesta sessão (H1 testou parcialmente e generalizou: 77,6% male / 77,4% female / 90,1% child).
- A tabela de roteamento por slot foi validada por LOO **só para `walk->idle`**. Apliquei a mesma tabela em `combat_idle` e `run` por aproximação -- os números dessas duas animações reproduzem os que a própria H1 já havia medido usando essa mesma aproximação, mas não refiz a validação LOO slot-a-slot dentro de cada uma. Se a composição ótima de dx,dy diferir por animação (plausível -- combat_idle/run são poses viradas, ver frente de movimento), este número está otimista.
- O preditor de qualidade da H5 usado aqui vem de artefatos de scratch de uma execução cujo relatório final não foi entregue nesta sessão -- os parâmetros (`modelo.json`) foram tratados como definitivos, mas não há como confirmar se essa foi a versão que o autor da H5 pretendia publicar.
- O número de 3.666 lacunas reais não foi reproduzido -- minha contagem própria (2.041) usa um critério diferente e mais estrito de "corpo disponível". A distribuição por faixa de qualidade proporcional ao 3.666 assume que a composição se mantém, o que não foi verificado.
- Não recomputei a doadora livre por IoU para TODOS os itens legados reais (só para a população de peças completas, n=428/362/369) -- a extrapolação da seção 5 assume que o comportamento medido nessa população se sustenta nos itens legados de verdade, que a própria pesquisa (H1, ataque não realizado ainda) já sinalizou como possivelmente diferentes.
- Não testei sensibilidade do limiar `ALTA=80%` usado para separar "alta confiança" de "baixa confiança" na seção 5 -- é um corte razoável mas arbitrário, não otimizado.

## Scripts

Não commitados, em `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/combinado/`: `livre_iou.py` (transplante com doadora livre, motor sem reimplementação), `combinar_idle.py` (combinado + ablação, idle), `combinar_generico.py` (combinado + ablação, combat_idle/run), `h5_overlay.py` (aplica o modelo da H5 e mede transferência). Reusa `scratchpad/h1-translacao/` (loader.py, core.py, tabelas de H1) e `scratchpad/h5-preditor/` (lib.py, modelo.json) sem reimplementar.
