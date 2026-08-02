export const meta = {
  name: 'transplante-lpc-pesquisa-fases2a5',
  description: 'Retomada da pesquisa do transplante: H1..H5, combinado com ablacao, ataque adversarial e sintese. Os tres fundamentos ja estao medidos e entram embutidos.',
  phases: [
    { title: 'Hipoteses', detail: 'H1..H5 medidas contra o baseline, validacao por peca' },
    { title: 'Combinado', detail: 'H6: junta as vencedoras, mede e faz ablacao' },
    { title: 'Adversarial', detail: 'tenta derrubar as conclusoes; e o juiz do olho' },
    { title: 'Sintese', detail: 'relatorio unico com metodo, criterios e veredito' },
  ],
}

const SCRATCH = '/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad'

const BASE = `CONTEXTO COMUM -- leia antes de qualquer coisa.

Projeto Waybuilder, acervo de sprites do Liberated Pixel Cup (LPC). Responder SEMPRE em pt-BR. NUNCA usar emoji.

O PROBLEMA: 170 de 627 pecas do acervo sao do formato legado e nao tem as animacoes novas (idle, combat_idle, sit, run). Nao existe essa arte. A solucao em uso e TRANSPLANTE: pegar outra peca que TEM a animacao, medir como os pixels dela se moveram entre duas poses, e aplicar esse mesmo movimento na peca que falta. Deterministico, sem IA.

O MOTOR JA EXISTE e voce DEVE usa-lo, nao reimplementar:
  /home/igor0/waybuilder-avatar/transplante.py
  - sobreposicao(a, b) -> IoU das silhuetas (0 a 1)
  - campo_de_deslocamento(origem, destino, raio=6, patch=5) -> devolve o PAR (campo, silhueta)
  - aplicar_campo(campo, arte, silhueta=None) -> arte transplantada
  - pixels_diferentes(a, b) -> quantos pixels a TELA mostraria diferentes (ignora pixel invisivel; NAO compare os 4 canais crus, isso conta 3.816 diferencas fantasmas por quadro)
  - escolher_doadora(alvo, candidatas)

OS DADOS:
  catalogo: /home/igor0/waybuilder/app/public/avatar/catalogo.json
  atlas: caminhos do campo 'arq', relativos a /home/igor0/waybuilder/app/public/avatar/
  Recorte de um frame: y vem de camadas[N].corpos[CORPO].cores (faixa 'base', ou a primeira se nao houver); x e frames vem da entrada de 'animacoes' com o nome desejado; o frame k fica em x + k*64, altura 64, largura 64.
  Material de cada peca: campo 'material' dentro de canais_de_cor (ex.: body, cloth, metal, wood, eye, hair). Profundidade: zPos em cada camada.
  Fonte original do LPC (spritesheets + codigo do gerador + documentacao): /home/igor0/waybuilder-avatar/fontes/lpc/
  Tabela taxonomica pronta da fase 1: /home/igor0/waybuilder-avatar/docs/2026-08-02_taxonomia.json
  Mapa de movimento pronto da fase 1: /home/igor0/waybuilder-avatar/docs/2026-08-02_mapa-de-movimento.json

O PAR DE FRAMES QUE SE USA: doadora walk k=0 -> idle k=1, aplicado a alvo walk k=0, comparado com alvo idle k=1. ATENCAO: em k=0 as duas poses sao IDENTICAS em varias pecas, e medir ali da resultado bom por acidente.

BASELINE OFICIAL A BATER (medido, 250 pecas do corpo male, doadora do mesmo slot por maior IoU):
  frames exatos (zero pixel errado): 20,0%
  mediana de pixels errados: 28
  media: 42,7
Toda medicao sua TEM de reportar o baseline ao lado, recalculado na SUA amostra. Sem isso o numero nao vale.

REGRAS DE METODO, inegociaveis:
  - Validacao cruzada POR PECA, nunca por frame: a peca de teste jamais entra no treino.
  - Metrica primaria: % de frames EXATOS. Secundaria: mediana de pixels errados.
  - Nunca reporte numero que nao mediu. Declare o tamanho da amostra sempre.
  - Nao arredonde a favor de nenhuma hipotese. Se a hipotese falhar, diga que falhou; se vencer, diga que venceu.
  - numpy esta disponivel no python3 do sistema (~/.local). NAO instale scipy nem torch.
  - Escreva scripts em ${SCRATCH}/ (subpasta propria por agente, use o nome do seu relatorio como pasta). O RELATORIO vai em /home/igor0/waybuilder-avatar/docs/. NAO commite nada, NAO rode git.
  - NUNCA toque no repo /home/igor0/waybuilder -- ele e so leitura de dado.
`

const CONTEXTO = "--- A gramatica do LPC: rampa fechada de 6 tons, alfa binario, e o idle como translacao rigida de 1 px ---\nA rampa de cor tem exatamente 6 tons para todo material (3 para olho), ordenada sombra->luz, e o recolor casa RGB exato com tolerancia +-1 por canal (PALETTE_RECOLOR_GUIDE.md:147-172, palette-recolor.ts:86) -- a paleta de saida de qualquer peca e fechada.\nNao existe regra de sombreamento escrita no repositorio: CONTRIBUTING.md:11 recomenda dois guias de estilo EXTERNOS e diz explicitamente 'it is not required'; nenhum arquivo menciona direcao de luz.\nMedido em 80 pecas: alfa e estritamente binario (95,23% em 0 e 4,76% em 255, zero valores intermediarios) e o tom 0 da rampa e o contorno (66,5% dos pixels de borda contra 5,2% dos internos).\nMedido em 120 pecas: a luz vem de cima sem componente lateral (dy medio -1,30 px, 78% das pecas; dx mediano -0,01 px, 50/50) -- espelhar uma doadora horizontalmente nao quebra o sombreamento.\nO ciclo de walk comeca em 1, nao em 0 (constants.ts:127): o quadro 0 e a pose neutra parada, e medido em 493 pecas ele e identico byte a byte ao idle k=0 em 88,4% dos casos -- o problema tem UM quadro de saida, nao dois.\nidle tem apenas 2 quadros (constants.ts:132, PNG 128x256), igual a combat_idle; hurt e climb tem uma unica linha, sem versao por direcao (constants.ts:130-131).\nO gerador JA deriva animacao de animacao em custom-animations.ts:39-661, mas sempre por reindexacao de quadro inteiro (copia, inverte, repete, congela, recentra) -- 32 sheets, 85 camadas; deformar pixel a pixel nao tem precedente na fonte.\nzPos e uma escala anatomica de dentro pra fora e de baixo pra cima (0 shadow, 10 body, 20 legs, 35 clothes, 60 arms, 100 head, 130 hat, 150 weapon), e zPos < 10 significa 'atras do corpo' -- camadas bg e fg da mesma peca sao geometrias distintas (cape_tattered.json).\nACHADO PRINCIPAL, validado por peca em 463 pecas: idle k=1 e walk k=0 transladado rigidamente 1 px para cima, com os pes plantados -- 71,9% de frames exatos (leave-one-out por slot) contra 18,5% do baseline transplante recalculado na mesma amostra.\nO deslocamento e coerente por slot e as duas excecoes delimitam o escopo: head/charm/hat_trim/facial_eyes/accessory/visor/ears acertam 100%, shoes e legs tem moda 'parado', mas clothes (bracos nao acompanham o tronco) e shield_pattern (mao anda +20 px em x) dao 0% -- e o baseline tambem da 0% nos dois.\nAplicavel: Muda a escolha da doadora de tres formas concretas. (1) Na maioria dos slots a doadora fica DESNECESSARIA: o par (walk k=0 -> idle k=1) e uma translacao rigida inteira, entao basta uma tabela slot -> (dx,dy) aprendida com leave-one-out. Isso ja da 71,9% de frames exatos em 463 pecas contra 18,5% do baseline transplante na mesma amostra -- 3,9x, sem campo de deslocamento, sem patch matching. A tabela e minuscula: 1 px pra cima em tudo que esta preso a cabeca ou ao tronco (head, hat, hair, ears, charm, visor, neck, accessory, hat_trim, facial_eyes), 'parado' no que toca o chao (shoes, legs). (2) A doadora com campo de deslocamento deve ser reservada aos slots onde a translacao rigida falha -- clothes (0%) e shield_pattern (0%) --, e nesses dois o baseline tambem da 0%, ou seja o transplante como esta nao esta resolvendo o caso dificil nem o facil. (3) Quando a doadora for usada, tres filtros baratos vindos da gramatica: nunca cruzar camada bg (zPos < 10) com camada fg da mesma peca porque sao geometrias diferentes; permitir doadora espelhada horizontalmente porque a luz do LPC nao tem componente lateral (dobra o pool); e projetar a saida de volta na rampa de 6 tons da peca com alfa binario 0/255 no fim do pipeline, o que e gratuito, nao pode piorar nenhum frame e corrige qualquer pixel de cor invalida. Alem disso, so idle k=1 precisa ser gerado: idle k=0 sai de graca copiando walk k=0 (identico em 88,4% de 493 pecas), o que corta o escopo do trabalho pela metade.\nRelatorio: /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-gramatica-lpc.md\n--- Taxonomia dos assets: material nao serve, zPos e apelido do slot, regiao e o unico eixo que cobre o acervo inteiro ---\n113 das 166 pecas legadas medidas nao tem NENHUMA peca nao-legada dentro do proprio slot -- slots inteiros sao legados de ponta a ponta (weapon 26, charm 16, belt 8, jacket 6, necklace 5, vest 4, dress 4, apron 4, bracers, chainmail, quiver, wrists, earrings, cape, arms), entao o criterio 'doadora do mesmo slot' simplesmente nao produz resposta para 68% do problema.\nMaterial FALHOU como criterio de agrupamento: IoU intra de metal x metal = 0,213 e praticamente igual a metal x hair = 0,212, e cloth (o maior grupo, n=133) tem o menor IoU intra do acervo (0,112); controlado por permutacao dos rotulos, material rende so 1,68x o acaso, o pior de todos os eixos.\nNa prova de transplante real (493 pecas, walk k=0 -> idle k=1), restringir a doadora ao mesmo material derruba os frames exatos de 18,7% para 14,2% e piora a mediana de 25,5 para 33 -- a unica restricao que perde do baseline nas tres metricas.\nzPos e quase um apelido do slot: 30 dos 57 valores de zPos correspondem a um unico slot e 84 dos 102 slots tem um unico zPos, entao seu ganho aparente de 5,20x sobre o nulo e emprestado do slot, nao informacao nova.\nzPos COLAPSA exatamente onde seria preciso: para as 113 legadas sem doadora no slot, restringir a doadora ao mesmo zPos da IoU mediano de 0,021 e ZERO pecas acima de 0,50 -- porque o slot inteiro sendo legado, sobram so candidatas de outro slot que dividem o z por acidente.\nRegiao (7 grupos, rotulagem puramente geometrica) empata com slot na prova de transplante -- 18,5% exatos contra 18,7%, mediana 23 contra 25,5 -- mas cobre 493/493 contra 460/493 do slot, e em 91,0% dos casos o melhor par dentro da regiao e tambem o melhor par do acervo inteiro.\nNenhuma restricao taxonomica bate a busca livre por IoU: soltar a doadora para o acervo inteiro da a melhor mediana (22 pixels errados, media 39,7) com o mesmo percentual de exatos -- o IoU ja sabe sozinho o que a taxonomia tentaria dizer, entao o valor dela e diagnostico, nao prescritivo.\n232 pecas (37%) nao declaram material nenhum e isso nao e aleatorio: 140 delas sao legadas, ou seja das 170 legadas apenas 30 tem material declarado -- o eixo esta ausente justamente onde o problema esta.\nOrfas de silhueta sao poucas e todas minusculas: so 10 pecas tem melhor par do acervo abaixo de IoU 0,20 (wings_dots 0,049, hairtie_rune 0,056, wound_eye 0,154, mustache 0,167) e todas tem area entre 2 e 56 pixels -- IoU e cruel com area pequena e para essas a escolha de doadora vira loteria.\n4 pecas (backpack/backpack, backpack/jetpack, backpack/square-pack, cargo/jetpack-fins) tem silhueta VAZIA na direcao frontal: mochilas nao aparecem de frente, o problema delas nao e falta de doadora e sim falta de pixel.\nAplicavel: Concretamente, tres mudancas na escolha da doadora. (1) PARE de usar material e zPos como criterio -- material derruba os exatos de 18,7% para 14,2% e zPos da IoU mediano 0,021 nas pecas que mais precisam. (2) SUBSTITUA a regra 'mesmo slot' por busca livre por IoU no acervo inteiro: ela cobre 493/493 em vez de 460/493, mantem os exatos (18,5% vs 18,7%, diferenca dentro do ruido) e melhora a mediana de 25,5 para 22; e a unica opcao que atende as 113 legadas cujo slot nao tem doadora. Os pares que ela acha sozinha fazem sentido visual: cargo/ore <- hat/kettle-helm (0,808), belt/leather-belt <- sash/obi (0,792), vest/vest <- armour/legion (0,792), jacket/tabard <- armour/plate (0,777), chainmail <- clothes/longsleeve (0,681). Migracoes recorrentes: charm->neck (11x), weapon->legs (8x), belt->sash (6x), jacket->clothes (5x). (3) USE a regiao como filtro de sanidade, nao como restricao: se a doadora livre cair em outra regiao E o IoU ficar abaixo de 0,30, marque a peca para revisao manual -- sao 37 das 166 legadas, e quase todo o slot weapon esta nessa faixa (scythe 0,150, rapier 0,163, cane 0,176), onde o transplante vai produzir lixo com qualquer criterio. A tabela para as outras frentes consumirem esta em /home/igor0/waybuilder-avatar/docs/2026-08-02_taxonomia.json, 627 pecas chaveadas pelo id, com material, zPos, regiao, area, compacidade, tons, bbox, centroide, lateralidade e o flag 'legado'.\nRelatorio: /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-taxonomia.md\n\nTabela JSON pedida (item 5): /home/igor0/waybuilder-avatar/docs/2026-08-02_taxonomia.json -- 347 KB, 627 pecas, chaveada pelo id do catalogo. Cada entrada traz {material, materiais, zPos, zPos_camadas, regiao, area, compacidade, tons, bbox, bbox_px, centroide, lateralidade, slot, grupo, categoria, legado, n_camadas, corpo_medido, anim_medida}. Alem dos campos pedidos incluí 'legado' (se a peca precisa de transplante), 'bbox_px' (sem normalizar, para recorte direto), 'lateralidade' (fracao da area fora do tronco central x=[19,45), que e o que separa braco/mao de torso/perna) e 'anim_medida' (rastreabilidade).\n\nMETODO. Silhueta = uniao de TODAS as camadas da peca (necessario: lendo so a camada de menor ordem, 93 pecas -- chifres, asas, caudas -- saiam com area zero porque a L1 delas e vazia), faixa de cor 'base', frame walk k=0, corpo male. IoU via transplante.sobreposicao; a matriz 623x623 em lote foi conferida contra a funcao do motor em 200 pares sorteados, 0 divergencias. Pixels errados via transplante.pixels_diferentes. Regiao rotulada por regra PURAMENTE geometrica (bbox + centroide + lateralidade), de proposito sem olhar slot nem zPos -- senao o eixo viraria copia de outro e a comparacao dos tres ficaria viciada.\n\nAMOSTRAS. Descritiva: 627. IoU: 623 (4 tem silhueta vazia de frente). Prova de transplante: 493 pecas do corpo male com walk k=0 e idle k=1.\n\nBASELINE, recalculado na minha amostra ao lado do oficial:\n- oficial declarado: 20,0% exatos / mediana 28 / media 42,7 / n=250\n- recalculado aqui (mesmo slot, maior IoU): 18,7% / 25,5 / 44,0 / n=493 (cobre 460)\n- controle nulo (nao transplantar, copiar walk k=0): 5,3% / 111,0 / 132,8 / n=493\n\nPROVA DE TRANSPLANTE POR CRITERIO DE DOADORA (n=493, nenhuma peca e doadora de si mesma):\n- mesmo slot (baseline): cobre 460/493, 18,7% exatos, mediana 25,5, media 44,0\n- mesma regiao: cobre 493/493, 18,5%, mediana 23,0, media 41,3\n- mesmo zPos exato: cobre 484/493, 18,2%, mediana 25,0, media 43,9\n- mesmo material: cobre 372/493, 14,2%, mediana 33,0, media 52,2  <-- PERDEU\n- livre por IoU: cobre 493/493, 18,5%, mediana 22,0, media 39,7  <-- melhor mediana\n\nCOMPARACAO JUSTA DOS EIXOS (IoU global de referencia = 0,0852; 'nulo' = mesmos tamanhos de grupo com rotulos embaralhados, 30 sorteios; 'ganho' = intra/nulo, unica leitura justa entre eixos com numeros de grupos diferentes):\n- slot: 102 grupos, cobre 623/623, intra 0,4846, nulo 0,0850, ganho 5,70x, coincide com a livre 80,2%\n- zPos: 57 grupos, 623/623, intra 0,4419, nulo 0,0851, ganho 5,20x, coincide 77,5%\n- regiao: 7 grupos, 623/623, intra 0,2031, nulo 0,0853, ganho 2,38x, coincide 91,0%\n- material: 9 grupos, cobre so 395/623, intra 0,2025, nulo 0,1207, ganho 1,68x, coincide 79,2%\nOrdem pelo ganho: zPos > regiao > material. Mas o ganho do zPos e emprestado do slot, e na aplicacao ele colapsa (ver abaixo).\n\nMATRIZ MATERIAL x MATERIAL (diagonal = intra):\nbody 0,213 | cloth 0,024 | hair 0,140 | metal 0,183\ncloth: 0,024 | 0,112 | 0,034 | 0,045\nhair: 0,140 | 0,034 | 0,299 | 0,212\nmetal: 0,183 | 0,045 | 0,212 | 0,213\nA diagonal mal se destaca -- metal x metal (0,213) empata com metal x hair (0,212).\n\nMATRIZ REGIAO x REGIAO (diagonal): bracos 0,189 / cabeca 0,202 / corpo_inteiro 0,188 / maos 0,125 / pernas 0,219 / pes 0,424 / torso 0,204. Fora da diagonal quase tudo abaixo de 0,12, com zeros literais (nenhuma peca de cabeca encosta em peca de pernas). Unica fronteira fraca: maos (0,125 intra contra 0,108 com bracos).\n\nAS 113 ORFAS DE SLOT -- melhor IoU alcancavel sob cada restricao (doadoras = 457 nao-legadas):\n- livre: cobre 113/113, IoU mediano 0,409, 34,5% acima de 0,50\n- mesma regiao: cobre 113/113, mediano 0,356, 29,2% acima de 0,50, retem 66,4% da escolha livre\n- mesmo material: cobre so 14/113, mediano 0,296\n- faixa zPos(10): cobre 45/113, mediano 0,194\n- mesmo zPos exato: cobre 30/113, mediano 0,021, ZERO acima de 0,50  <-- colapso total\n\nDISTRIBUICOES. Material: 232 sem declarar (37%, sendo 140 legadas), cloth 133, hair 124, body 62, metal 51, body+eye 8, cloth+metal 5, metal+wood 5, wood 4, cloth+hair 3. Regiao: cabeca 279 (7 legadas), torso 134 (59), pernas 65 (47), bracos 60 (15), corpo_inteiro 41 (21), maos 23 (13), pes 21 (4), invisivel 4 (4). zPos: 57 valores distintos em [0,150], concentrados em z=120 (86 pecas, 83 hair), z=130 (49, 46 hat), z=112 (49, 48 shield_pattern). Area: mediana 161 px (q1 56, q3 287, max 1202). Compacidade: mediana 0,596. Tons: mediana 6 (q1 4, q3 6, max 153) -- e tons por material sao indistinguiveis entre si (cloth 5, hair 6, metal 6, body 7), ou seja cor tambem nao separa material.\n\nLIMITES DECLARADOS. Tudo medido na direcao frontal e no corpo male -- nao verifiquei se a taxonomia se sustenta em female/child, onde a proporcao muda. A regiao usa a faixa de cor 'base'. A fronteira maos/bracos e fraca e precisa ser refeita se alguma frente depender dela. A prova de transplante cobriu 1 par de frames (walk k=0 -> idle k=1); nao testei se a ordem dos eixos muda em sit, run ou combat_idle. O baseline nulo usa 30 permutacoes e fica ruidoso em grupos pequenos (wood, n=4). Nao existe regiao 'costas' na taxonomia porque o acervo so tem a direcao frontal -- quem precisar de costas deve ler zPos <= 8.\n\nScripts (nao commitados): /tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/taxonomia/ na ordem medir.py -> regiao.py -> analise2.py -> analise3.py -> prova.py -> resumo.py\n--- Anatomia do movimento: as cinco animacoes formam dois grupos de pose, e o campo de deslocamento so funciona dentro de um deles ---\nAs cinco animacoes se dividem em dois grupos de pose: idle/walk/sit desenham o corpo de frente (silhueta de 30, 30 e 26-28 px de largura) e combat_idle/run o desenham virado (21 e 22-25 px); todo par que cruza os grupos e uma rotacao, nao uma translacao.\nidle k=0 e walk k=0 sao o MESMO quadro no corpo (0 pixels de diferenca) e em 362 das 391 pecas completas (92,6%), entao o ponto de partida do preenchimento e unico e as linhas idle->X e walk->X do mapa sao identicas.\nwalk->idle, o par do baseline, e de longe o mais facil dos 25: 82% dos pixels ficam parados, pernas e pes ficam 100% parados e o maior deslocamento medio e -0,6 px na cabeca.\nO movimento e local e nao regional: nos 25 pares as regioes anatomicas explicam entre 0,5% e 23% da variancia do deslocamento (mediana 9,6%), ou seja 77% a 99,5% da variacao esta DENTRO de uma mesma regiao.\nUm campo unico global recupera apenas 12% (mediana) do erro que o campo por pixel recupera e em 5 dos 25 pares (run->idle, run->walk, run->combat_idle, walk/idle->combat_idle) ele PIORA o resultado em relacao a nao mover nada; um campo por regiao recupera 28%.\nO campo tem um teto proprio: aplicado a propria doadora que o gerou, ele erra 5% dos pixels em walk->idle mas 46% a 58% nos 12 pares que cruzam os grupos de pose -- nenhuma alvo pode sair melhor que isso.\nNos pares dificeis 11% a 32% dos pixels saturam o raio=6 do motor e a coerencia entre pixels vizinhos cai de 92% para 34-42%, assinatura de casamento por ruido em vez de movimento.\nAs pecas nao se movem como o corpo e na maioria dos casos nem tocam nele: a mediana de pixels em comum entre peca e corpo e 6, metade das pecas tem menos de 8 px de sobreposicao e 72,8% tem menos de 30% da propria area sobre o corpo.\nA classe que mais se descola do corpo e o cabelo comprido lateral (hairextl/hairextr, 14 pecas, divergencia de 3,7 a 7,1 px na regiao dos bracos), seguida de sleeves, ponytail/updo e shoes/socks; 16 pecas (wings, tail, shield, horns) tem quadros VAZIOS no recorte de frente e nem chegam a ter movimento.\nPor regiao, o transplante e trivial em pes e pernas no destino idle (66,7% e 50,0% de frames exatos, mediana 0 e 2 px) e e sempre ruim em pernas e pes nos destinos combat_idle e run (0,0% de exatos nas quatro celulas) e na cabeca no destino sit (0,0% de exatos, mediana de 122 pixels errados).\nAplicavel: Testei todas as doadoras do mesmo slot para cada alvo (331 alvos, media de 37 candidatas). Tres consequencias concretas. (1) A regra atual, maior IoU no quadro de partida, esta certa e vale muito: contra a candidata media corta a mediana de erro de 60 para 20 px em idle e captura 86% a 94% do ganho que um oraculo teria -- nao ha o que ajustar nela para idle, combat_idle e sit. (2) Mas o teto da escolha e baixo: mesmo escolhendo perfeitamente, os exatos vao so de 23,6% para 30,2% em idle, de 15,1% para 21,1% em run e de 0,0% para 0,0% em sit; o gargalo nao e QUAL doadora, e o modelo de campo. Investir em escolha de doadora rende no maximo +6 pontos percentuais de frames exatos. (3) Para o destino run a correlacao entre IoU e erro e ZERO (-0,001), contra -0,60 em idle: silhueta parecida na pose de partida nao prediz nada quando o destino e uma pose girada. Ou seja, escolher doadora por IoU do quadro de partida e, especificamente para run, escolher no escuro, e a doadora deveria ser escolhida por outro criterio (ou o par run deveria ser tratado por outro mecanismo que nao campo de deslocamento). E, sobre o que preencher: sit tem 0,0% de frames exatos em todas as 349 pecas e em todas as regioes, com mediana de 123 pixels errados -- gerar sit por transplante nao produz arte aproximada, produz ruido, e vale decidir se entra no build.\nRelatorio: Relatorio completo: /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-movimento.md\nMapa em JSON (item 5 da tarefa): /home/igor0/waybuilder-avatar/docs/2026-08-02_mapa-de-movimento.json -- contem, por (animacao_origem, animacao_destino, regiao), dy/dx medio, desvio, magnitude, variancia interna e fracao de pixels parados, mais as secoes transplante_por_regiao, pecas_contra_o_corpo e escolha_da_doadora. Scripts (nao commitados) em /tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/movimento/.\n\nAMOSTRA. Corpo male, camada 0, direcao frente (o unico recorte do acervo). 391 itens tem as cinco animacoes; 349 deles tem doadora do mesmo slot. 25 pares de animacao medidos com todos os quadros distintos do destino; 110 campos no corpo e 1.564 campos nas pecas. Motor usado sem reimplementacao (campo_de_deslocamento, aplicar_campo, pixels_diferentes, sobreposicao).\n\nBASELINE. Oficial (250 pecas, doadora do mesmo slot por maior IoU, walk k=0 -> idle k=1): 20,0% exatos, mediana 28, media 42,7. Recalculado na minha amostra (349 pecas, mesmo protocolo): 22,3% exatos, mediana 20, media 36,4 -- amostra maior e um pouco mais facil. Piso na mesma amostra (nao mover nada): 6,0% exatos, mediana 135. Teto (peca reconstruida pelo campo dela mesma): 84,3% exatos, 2,2% de erro relativo.\n\n1. TABELA DE MOVIMENTO. Bandas anatomicas lidas da silhueta do corpo (vista de cima): cabeca y<38, torso 38<=y<50 e 23<=x<41, bracos mesma faixa nas laterais, pernas 50<=y<57, pes y>=57, externo x<15 ou x>=49. A tabela completa dos 25 pares esta no relatorio e no JSON. Resumo: walk->idle move -0,6 px na cabeca e 0,00 px em pernas e pes; walk->sit move +1,2/+0,3 no torso e 4,3 px de magnitude nas pernas; walk->run e walk->combat_idle movem 3 a 5,5 px em TODA regiao. A regiao que mais anda e quase sempre bracos (ate 6,6 px em run->idle), a que menos anda e pes, exceto quando o par cruza os grupos de pose.\n\n2. UNIFORME OU LOCAL. Local, e por larga margem. Variancia explicada pelas regioes: mediana 9,6%, maximo 23%. Custo por granularidade (erro em pixels reconstruindo o proprio destino do corpo): walk->idle parado 81, global 81, por regiao 52, por pixel 33; walk->run parado 355, global 324, regiao 314, pixel 230; run->walk parado 519, global 532 (pior que parado), regiao 524, pixel 362. Um campo global recupera 12% (mediana) e um por regiao 28% do que o campo por pixel recupera. Alem disso o proprio campo por pixel ja falha nos pares dificeis: saturacao do raio=6 em 11-32% dos pixels, coerencia com o vizinho caindo de 92% para 34-42%, e teto de erro de 46% a 58%.\n\n3. PECAS CONTRA O CORPO. Metade do acervo completo nem toca o corpo no quadro de destino (mediana de 6 px em comum; 50,8% com menos de 8 px; 72,8% com menos de 30% da propria area sobre o corpo) -- cabelo, chapeu, visor, orelha e acessorio ficam acima da calota do cranio, onde o campo do corpo e zero por construcao. Onde coexistem, o campo e identico ao do corpo em 72,4% dos pixels em walk->idle mas so 7,3% a 14,7% em combat_idle, run e sit (desalinho de 2,9 a 4,1 px). Em erro: campo proprio 2,2% / campo do corpo 52,9% / parado 61,8% em walk->idle; restringindo as 92 pecas realmente sobre o corpo, 6,7% / 23,1% / 39,6% -- o movimento do corpo devolve 50% do caminho no melhor caso. Classes nomeadas que nao seguem o corpo: hairextl/hairextr (cabelo comprido lateral, 3,7 a 7,1 px de divergencia nos bracos, e em walk->sit o campo do corpo praticamente nao explica nada), sleeves (5,9 px no torso), ponytail/updo (ate 6,4 px na cabeca), neck e shoes/socks. E 16 pecas (wings, tail, shield, horns, cavalier-feather) tem 330 quadros vazios no recorte de frente, com 2 casos em que a origem esta vazia e o destino nao.\n\n4. REGIAO TRIVIAL E REGIAO PERDIDA. Trivial: pes (66,7% exatos, mediana 0) e pernas (50,0%, mediana 2) no destino idle -- as unicas celulas majoritariamente exatas do estudo, com 18 e 24 pecas de amostra. Sempre ruim: pernas e pes em combat_idle e run (0,0% exatos nas quatro celulas, mediana 10 a 38 px) e cabeca em sit (0,0% exatos, mediana 122 px errados, o pior numero do estudo -- em sit k=1 a cabeca do corpo desce para fora da banda y<38). A animacao sit inteira e insalvavel pelo metodo atual: 0,0% de exatos em todas as regioes e todas as 349 pecas, contra 22,3% em idle, 17,8% em combat_idle e 14,3% em run."

const ACHADOS = {
  type: 'object',
  properties: {
    titulo: { type: 'string' },
    veredito: { type: 'string', description: 'VENCE, EMPATA ou PERDE contra o baseline, com uma frase de porque' },
    amostra: { type: 'string', description: 'quantas pecas/pares foram medidos' },
    baseline_exatos: { type: 'number', description: 'percentual de frames exatos do baseline NA SUA amostra' },
    medido_exatos: { type: 'number', description: 'percentual de frames exatos da hipotese' },
    baseline_mediana: { type: 'number' },
    medido_mediana: { type: 'number' },
    numeros: { type: 'array', items: { type: 'string' }, description: 'ate 8 numeros-chave, cada um uma frase curta' },
    limitacao: { type: 'string', description: 'o que esta medicao NAO prova' },
    relatorio: { type: 'string', description: 'caminho do arquivo escrito' },
  },
  required: ['titulo', 'veredito', 'amostra', 'numeros', 'limitacao', 'relatorio'],
}

const TEXTO = {
  type: 'object',
  properties: {
    titulo: { type: 'string' },
    achados: { type: 'array', items: { type: 'string' }, description: 'ate 10 achados, cada um uma frase' },
    aplicavel: { type: 'string', description: 'como isto muda a escolha da doadora, concretamente' },
    relatorio: { type: 'string' },
  },
  required: ['titulo', 'achados', 'aplicavel', 'relatorio'],
}

// ------------------------------------------------------------------ hipoteses
phase('Hipoteses')

const HIPOTESES = [
  {
    id: 'H1', label: 'h1-translacao-rigida', effort: 'high',
    texto: `H1 -- A TRANSLACAO RIGIDA POR SLOT DISPENSA A DOADORA. Esta e a hipotese mais importante da pesquisa, e voce vai ATACA-LA, nao confirma-la.

A frente de gramatica mediu, em 463 pecas com leave-one-out por slot, que idle k=1 e simplesmente walk k=0 transladado 1 px para cima, com os pes plantados: 71,9% de frames exatos contra 18,5% do transplante na mesma amostra. E que idle k=0 e byte a byte igual a walk k=0 em 88,4% de 493 pecas.

Se isso resistir, o transplante inteiro fica obsoleto para o par walk->idle e vira uma tabela slot -> (dx, dy).

O QUE MEDIR, nesta ordem:
1. REPRODUZA o numero de forma independente. Monte a tabela slot -> (dx,dy) por leave-one-out (a peca de teste nunca entra na estimativa do slot dela) e reporte frames exatos e mediana, com o baseline do transplante ao lado.
2. ONDE ELA FALHA: a tabela por slot da 0% em clothes e shield_pattern segundo a frente de gramatica. Confirme, e liste TODOS os slots por taxa de acerto. Onde a translacao falha, o transplante por doadora resolve? Meça os dois no mesmo subconjunto -- essa e a pergunta que decide se o transplante continua existindo.
3. AS OUTRAS ANIMACOES: a translacao rigida vale para combat_idle, sit e run, ou so para idle? Meça os quatro destinos a partir de walk k=0. A frente de movimento diz que idle/walk/sit sao de frente e combat_idle/run sao virados -- se for isso, a translacao so pode valer no primeiro grupo. Confirme com numero.
4. GENERALIZACAO: vale nos seis corpos ou so no male? Meça em pelo menos male, female e child.
5. O TESTE QUE MAIS IMPORTA: tudo isso foi medido em pecas COMPLETAS. As 170 legadas podem ser diferentes. Existe alguma peca legada que TENHA idle (mesmo sem as outras)? Se existir, teste nela -- e a unica evidencia direta. Se nao existir, diga que nao existe e explique o que isso limita.
6. Combine: a tabela por slot para quem ela acerta, transplante para o resto. Qual a taxa global?
7. ENTREGUE A TABELA em JSON, pronta para virar codigo: slot -> {dx, dy, n_amostra, taxa_exatos, usar_transplante_no_lugar: bool}. Diga o caminho.`,
  },
  {
    id: 'H2', label: 'h2-escopo-do-que-gerar', effort: 'medium',
    texto: `H2 -- NEM TODA ANIMACAO VALE SER GERADA. Decida, com numero, o que entra no build e o que fica no fallback parado.

A frente de movimento mediu que sit da 0,0% de frames exatos em 349 pecas, com mediana de 123 pixels errados -- nao e arte aproximada, e ruido. E que para run a correlacao entre IoU e erro e ZERO (-0,001) contra -0,60 em idle: escolher doadora por silhueta ali e escolher no escuro.

MEÇA, por animacao de destino (idle, combat_idle, sit, run) e reporte a tabela completa:
1. frames exatos, mediana e media de pixels errados, com o baseline 'nao fazer nada' ao lado;
2. a fracao da peca que sai errada (pixels errados / area da peca) -- 30 px numa peca de 60 e destruicao, 30 numa de 400 e retoque;
3. quantas pecas ficam ABAIXO de um limiar de 5% da propria area errada (a faixa 'passa sem revisao') e quantas acima de 25% (a faixa 'lixo');
4. o mesmo recorte por REGIAO do corpo, para achar combinacoes (destino, regiao) que sejam sempre boas ou sempre lixo;
5. VEREDITO por animacao: entra no build, entra com revisao, ou nao entra. Justifique cada um com o numero que o sustenta.

Reporte no campo 'medido_exatos' a taxa da MELHOR animacao e no 'numeros' a tabela inteira.`,
  },
  {
    id: 'H3', label: 'h3-campo-local', effort: 'medium',
    texto: `H3 -- CAMPO POR REGIAO bate campo global.
Hoje um unico campo de deslocamento cobre o quadro inteiro. Teste dividir o quadro em regioes (use o mapa da frente de movimento, em docs/2026-08-02_mapa-de-movimento.json) e montar um campo por regiao, cada um possivelmente de uma DOADORA DIFERENTE -- a melhor para aquela regiao.
Variantes a medir: (a) campo por regiao, mesma doadora; (b) campo por regiao, doadora escolhida por regiao; (c) campo global (baseline).
Cuidado com a costura entre regioes: meça quantos pixels errados aparecem nas fronteiras, e se a emenda cria defeito novo.
ATENCAO AO ESCOPO: se a H1 estiver certa, esta hipotese so importa nos slots onde a translacao rigida falha (clothes, shield_pattern) e nas animacoes fora do grupo de frente. Meça PRIORITARIAMENTE nesse subconjunto -- e onde ela pode agregar.`,
  },
  {
    id: 'H4', label: 'h4-indice-de-rampa', effort: 'medium',
    texto: `H4 -- TRANSPORTAR POR INDICE DE RAMPA amplia o pool de doadoras.
Hoje a comparacao doadora/alvo usa RGB. Se converter cada pixel para o INDICE na rampa de cor da peca (0 a 5, mais vazio), duas pecas de cores diferentes viram comparaveis -- o pool de doadoras cresce muito.
Meça: (a) a escolha de doadora melhora quando a similaridade e calculada por indice em vez de RGB? (b) o transplante em si melhora? (c) quantas doadoras novas ficam disponiveis para as pecas que hoje nao tem nenhuma?
Para achar o indice: a faixa 'base' do atlas e a arte crua; a rampa de origem esta no campo 'base' do canal de cor (formato 'versao.rampa'), e os arquivos de paleta estao em paletas/<material>/<material>_<versao>.json.
A fase 1 mediu que a rampa e fechada em 6 tons com casamento RGB exato (tolerancia +-1) e alfa binario -- ou seja, a indexacao e possivel sem perda. Confirme isso antes de medir o resto.`,
  },
  {
    id: 'H5', label: 'h5-preditor-de-qualidade', effort: 'high',
    texto: `H5 -- A QUALIDADE E PREDIZIVEL SEM GABARITO.
Esta e a hipotese mais importante para o produto: nas 3.666 lacunas reais NAO existe original para comparar. Precisamos de uma nota de confianca calculada so a partir do que da para ver.
Sinais candidatos, todos computaveis sem gabarito -- meça a correlacao de CADA UM com o erro real, na validacao cruzada:
  - IoU entre alvo e doadora
  - magnitude media e maxima do campo de deslocamento
  - quantos pixels do alvo ficaram orfaos (sem origem) ou duplicados (mesma origem para varios destinos)
  - buracos na peca gerada: pixels vazios cercados de opacos
  - fragmentacao: numero de componentes conexos, antes e depois
  - variacao de area entre a peca de partida e a gerada
  - coerencia temporal: quanto muda entre frames consecutivos da animacao gerada, comparado com o quanto muda numa animacao REAL da mesma peca (peca que pisca demais e defeito)
  - compacidade antes e depois
Depois monte um preditor simples (limiar, ou arvore rasa, ou regressao linear -- numpy puro) e reporte:
  - correlacao de cada sinal isolado com o erro real
  - a precisao ao isolar o QUARTIL PIOR (criterio de sucesso: >=70%)
  - quantas das 3.666 lacunas reais seriam reprovadas por esse preditor, e a distribuicao da nota
O criterio de sucesso desta hipotese NAO e % de frames exatos: e a precisao ao pegar as ruins. Reporte assim.`,
  },
]

const medidas = await parallel(HIPOTESES.map((h) => () => agent(`${BASE}

FUNDAMENTOS JA MEDIDOS pela fase 1 desta pesquisa -- use, NAO repita, NAO remeça:
${CONTEXTO}

SUA TAREFA -- TESTAR A HIPOTESE ${h.id}, e so ela.

${h.texto}

Meça contra o baseline recalculado na SUA amostra. Use pelo menos 300 alvos; se reduzir, diga o tamanho e por que. Validacao por peca.
Se a hipotese VENCER, diga que vence e entregue os parametros exatos que a fazem vencer (limiares, pesos, criterios) -- eles viram codigo depois.
Se PERDER, diga que perde e diga POR QUE, com numero.

Escreva o relatorio em /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-${h.label}.md`,
  { label: h.label, phase: 'Hipoteses', schema: ACHADOS, model: 'sonnet', effort: h.effort })))

const vivas = medidas.filter(Boolean)
const vencedoras = vivas.filter((m) => /VENCE/i.test(m.veredito))
log(`Hipoteses medidas: ${vivas.length}/${HIPOTESES.length} | vencedoras: ${vencedoras.length}`)

const resumoHip = vivas.map((m) =>
  `--- ${m.titulo} [${m.veredito}] ---\namostra: ${m.amostra}\n`
  + `exatos: baseline ${m.baseline_exatos ?? '?'}% -> medido ${m.medido_exatos ?? '?'}%\n`
  + `mediana: baseline ${m.baseline_mediana ?? '?'} -> medido ${m.medido_mediana ?? '?'}\n`
  + m.numeros.join('\n') + `\nlimitacao: ${m.limitacao}\nrelatorio: ${m.relatorio}`,
).join('\n\n')

// ------------------------------------------------------------------ combinado
phase('Combinado')

const combinado = await agent(`${BASE}

FUNDAMENTOS:
${CONTEXTO}

RESULTADO DE TODAS AS HIPOTESES:
${resumoHip}

SUA TAREFA -- H6: O COMBINADO. Junte os criterios que VENCERAM e meça o conjunto. Se nenhum venceu, meça mesmo assim a melhor combinacao possivel dos que menos perderam, e diga isso com todas as letras.

1. Monte o gerador combinado, com os parametros exatos que as frentes vencedoras entregaram. Se a H1 venceu, o combinado e "translacao rigida onde ela acerta, transplante onde ela falha" -- e o criterio de roteamento entre os dois e o que voce tem de fixar por numero.
2. Meça contra o baseline, na mesma amostra, com validacao por peca. Metrica primaria: % de frames exatos.
3. Faca ABLACAO: tire um criterio de cada vez e meça de novo. Isso diz qual criterio realmente carrega o ganho e qual e enfeite. Reporte a tabela completa.
4. Aplique o preditor de qualidade da H5 por cima e reporte: com o combinado MAIS o corte das piores, qual a taxa de frames exatos entre as que SOBRAM, e quantas sobram.
5. Diga, com numero, quantas das 3.666 lacunas reais o conjunto entregaria em cada faixa de qualidade.

Escreva o relatorio em /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-combinado.md`,
  { label: 'combinado-e-ablacao', phase: 'Combinado', schema: ACHADOS, model: 'sonnet', effort: 'high' })

// ---------------------------------------------------------------- adversarial
phase('Adversarial')

const ataque = await parallel([
  () => agent(`${BASE}

FUNDAMENTOS DA FASE 1 (tambem sujeitos a ataque):
${CONTEXTO}

CONCLUSOES A ATACAR:
${resumoHip}

COMBINADO:
${combinado ? `${combinado.veredito}\n${combinado.numeros.join('\n')}\nlimitacao: ${combinado.limitacao}` : '(o combinado falhou)'}

SUA TAREFA -- REFUTAR. Voce nao esta aqui para concordar. Tente derrubar cada conclusao, e so aceite o que resistir.

Procure especificamente:
1. VAZAMENTO. Alguma medicao treinou e testou na mesma peca? Doadora e alvo sao a mesma arte com outro nome (variantes de cor da mesma peca)? Isso infla tudo -- CHEQUE relendo os scripts em ${SCRATCH}/.
2. O PAR DE FRAMES. Alguem mediu em walk k=0 -> idle k=0, onde as poses sao identicas? Isso da resultado perfeito por acidente. O achado da fase 1 de que "idle k=0 e igual a walk k=0 em 88,4%" e exatamente o tipo de coisa que pode ter contaminado a medicao da H1 -- verifique se a H1 mediu k=1 mesmo.
3. AMOSTRA. Os ganhos vem de um punhado de pecas faceis? Refaca o corte: o ganho se sustenta se voce tirar as pecas cujo baseline ja era exato?
4. A METRICA. % de frames exatos pode subir enquanto a arte fica pior aos olhos? Procure caso concreto e mostre.
5. GENERALIZACAO. O que foi medido no corpo male vale em female/child/muscular? Teste em pelo menos um outro corpo.
6. O NUMERO QUE INTERESSA. As conclusoes foram tiradas nas 442 pecas COMPLETAS. As 3.666 lacunas reais sao de pecas LEGADAS, que podem ser sistematicamente diferentes -- pecas antigas, de outro estilo. MEÇA essa diferenca: as legadas se parecem com as completas? Se nao, tudo isto pode nao transferir. Este e o ataque mais importante dos seis.

Para cada ataque: CONFIRMA (o defeito existe, com numero) ou NAO CONFIRMA (testei e resistiu, com numero). Nao especule.

Escreva em /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-ataque.md`,
    { label: 'refutacao', phase: 'Adversarial', schema: TEXTO, effort: 'high' }),

  () => agent(`${BASE}

SUA TAREFA -- O JUIZ DO OLHO. As metricas contam pixel; ninguem joga olhando pixel. Voce vai verificar se a metrica corresponde ao que se VE.

1. Gere, com o transplante atual, uma amostra variada de pecas: 10 com erro medido baixo, 10 medio, 10 alto.
2. Para cada uma, monte uma figura PNG comparando: peca de partida, peca real, peca gerada, e o mapa de erro em vermelho. Amplie pelo menos 4x. Salve em /home/igor0/waybuilder-avatar/docs/2026-08-02_amostra-visual/.
3. OLHE as figuras (use a ferramenta de leitura de imagem) e classifique cada uma: aceitavel, duvidosa, inaceitavel.
4. RESPONDA: a nota de pixel prediz o julgamento visual? Ha peca com erro BAIXO que fica visualmente horrivel, ou erro ALTO que fica aceitavel? Se houver, isso e o achado mais importante desta frente -- descreva o padrao.
5. Que TIPO de defeito e mais feio: falta de pixel, cor errada, sobra, fragmentacao? Ordene por gravidade visual e diga como identifica-los automaticamente.

Escreva em /home/igor0/waybuilder-avatar/docs/2026-08-02_pesquisa-juizo-visual.md`,
    { label: 'juizo-visual', phase: 'Adversarial', schema: TEXTO, model: 'sonnet' }),
])

// --------------------------------------------------------------------- sintese
phase('Sintese')

const ataques = ataque.filter(Boolean).map(
  (a) => `--- ${a.titulo} ---\n${a.achados.join('\n')}\nAplicavel: ${a.aplicavel}\nRelatorio: ${a.relatorio}`,
).join('\n\n')

const sintese = await agent(`${BASE}

Voce e o ultimo passo de uma pesquisa. Todo o material esta abaixo. Sua tarefa e escrever o DOCUMENTO UNICO que o dono do projeto vai ler para decidir.

FUNDAMENTOS (fase 1):
${CONTEXTO}

HIPOTESES:
${resumoHip}

COMBINADO:
${combinado ? `${combinado.veredito}\namostra: ${combinado.amostra}\n${combinado.numeros.join('\n')}\nlimitacao: ${combinado.limitacao}\nrelatorio: ${combinado.relatorio}` : '(falhou)'}

ATAQUE ADVERSARIAL:
${ataques}

ESCREVA /home/igor0/waybuilder-avatar/docs/2026-08-02_PESQUISA-transplante.md com esta estrutura:

1. A PERGUNTA e por que ela importa (3 linhas).
2. METODO: como foi medido, a validacao por peca, o baseline, e os CRITERIOS DE SUCESSO fixados antes -- vencer = +3 pontos percentuais em frames exatos; preditor util = >=70% de precisao no quartil pior.
3. TABELA DAS HIPOTESES: uma linha por hipotese, com baseline, medido, e veredito. Ordenada da que mais ganhou para a que menos.
4. O QUE O ATAQUE DERRUBOU: cada achado adversarial confirmado, e o que ele invalida. Se derrubou uma hipotese vencedora, ela sai da tabela de recomendacoes -- diga isso explicitamente.
5. O QUE SOBROU DE PE: so o que resistiu, com numero.
6. RECOMENDACAO: o que virar codigo, em ordem, com os parametros exatos. E o que NAO fazer, com o motivo medido.
7. O QUE CONTINUA EM ABERTO: perguntas que a pesquisa nao respondeu, e o que custaria responder.

Seja honesto acima de tudo: se a pesquisa nao achou ganho, o documento tem de dizer isso na primeira linha da recomendacao. Nao maquie. Nao invente numero -- todo numero vem das frentes acima, e se uma frente falhou, diga que faltou.

Devolva no campo 'achados' os 8 pontos mais importantes, e em 'aplicavel' a recomendacao em uma frase.`,
  { label: 'sintese-final', phase: 'Sintese', schema: TEXTO, effort: 'high' })

return {
  hipoteses: vivas.map((m) => ({ t: m.titulo, v: m.veredito,
    base: m.baseline_exatos, medido: m.medido_exatos, relatorio: m.relatorio })),
  combinado: combinado ? { v: combinado.veredito, n: combinado.numeros } : 'falhou',
  ataques: ataque.filter(Boolean).map((a) => ({ t: a.titulo, achados: a.achados })),
  sintese: sintese ? { achados: sintese.achados, recomendacao: sintese.aplicavel,
    relatorio: sintese.relatorio } : 'falhou',
}
