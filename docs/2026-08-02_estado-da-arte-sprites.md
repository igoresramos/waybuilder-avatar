# Estado da arte: geracao/derivacao automatica de animacoes de pixel art (sprites)

Pesquisa para decidir se vale investir em modelo proprio para gerar as animacoes
faltantes de pecas do acervo LPC (`combat_idle`, `sit`, `run`, e parte de `idle`)
a partir das animacoes que a peca ja tem, usando o corpo base (que tem todas as
poses) como guia de pose alvo. Ver `2026-08-02_reuso-de-poses.md` para a medicao
que descarta remapeamento deterministico (0 dos 170 itens incompletos seriam
recuperados so por copia de pixel).

## 1. Trabalho academico mais proximo do nosso problema (confirmado)

**"On the Challenges of Generating Pixel Art Character Sprites Using GANs"**
Flavio Coutinho e Luiz Chaimowicz (UFMG), AIIDE 2022, vol. 18, p. 87-94.
https://ojs.aaai.org/index.php/AIIDE/article/view/21951
Tambem em versao arXiv: https://arxiv.org/pdf/2208.06413 (ar5iv:
https://ar5iv.labs.arxiv.org/html/2208.06413)

- O que fazem: dado um sprite de personagem numa direcao/pose, gerar o mesmo
  personagem em OUTRA direcao (ex: de frente para de lado), via GAN estilo
  Pix2Pix (gerador U-Net + discriminador PatchGAN), imagens RGBA 64x64.
- Datasets: Tiny Hero (912 imagens, 64x64) e tres datasets RPG Maker (32x24 a
  48x32).
- **Tiny Hero e derivado do proprio Universal LPC Spritesheet Generator** --
  confirmei na fonte (GitHub AgaMiko/pixel_character_generator e footnote do
  paper seguinte, item abaixo): personagens gerados aleatoriamente com o
  gerador LPC, capturados em 4 angulos. E literalmente o mesmo acervo do
  Waybuilder, resolucao identica (64x64).
- Resultado numerico (FID): 0,115 no Tiny Hero (teste); 2,306 a 9,493 nos
  datasets RPG Maker (piores porque tem menos exemplos e mais variacao de
  estilo).
- **Diferenca chave para o nosso caso**: eles trocam ANGULO DE CAMERA (mesma
  pose, direcao diferente), nao ANIMACAO (pose diferente, mesma direcao). E
  "view synthesis", nao "motion retargeting". Nao ha coerencia temporal
  entre frames porque cada direcao e um frame estatico isolado, nao uma
  sequencia.

**"A Missing Data Imputation GAN for Character Sprite Generation"**
Coutinho e Chaimowicz (mesmo grupo), SBGames 2024.
https://arxiv.org/pdf/2409.10721 (ar5iv: https://ar5iv.labs.arxiv.org/html/2409.10721)

- Evolucao do trabalho acima: reformulam o problema de "traducao de dominio
  A para B" para "imputacao de dado faltante" -- o modelo (CollaGAN
  adaptado) recebe as direcoes DISPONIVEIS do personagem e reconstroi a(s)
  direcao(oes) faltante(s), testando cenarios com 1, 2 ou 3 direcoes ausentes.
- Dataset expandido: Tiny Hero (LPC, confirmado no texto: "Source:
  https://lpc.opengameart.org/") + 14.202 imagens raspadas/montadas de outras
  fontes (12.074 treino / 2.128 teste), ainda em 64x64.
- Resultado numerico: FID 1,508 e L1 0,04078 (CollaGAN-3, faltando 3 de 4
  direcoes) contra FID 2,288 (StarGAN) e FID 4,091 (Pix2Pix baseline) --
  ganho claro sobre baselines de traducao par-a-par.
- **Mesma diferenca do item anterior**: ainda e reconstrucao de ANGULO
  faltante a partir de angulos existentes da MESMA pose, nao geracao de uma
  ANIMACAO (pose de movimento) nova. O "dado faltante" deles e direcao de
  camera; o nosso e quadro de animacao.

Conclusao sobre este par de papers: e a linha de pesquisa mais proxima em
resolucao, estilo e ate dataset-fonte (LPC), mas ataca um problema
estruturalmente mais simples que o nosso -- interpolar entre 4 vistas da
MESMA pose estatica, sem exigir coerencia entre uma sequencia de frames em
movimento. Nao ha evidencia nestes papers de que o metodo se estenda para
gerar uma animacao completa (varios frames coerentes entre si) a partir de
outra animacao da mesma peca.

## 2. Inbetweening de animacao (mais proximo do "faltam frames de movimento")

**"SketchBetween: Video-to-Video Synthesis for Sprite Animation via Sketches"**
Dagmar Lukka Loftsdottir e Matthew Guzdial (U. Alberta), 2022.
https://arxiv.org/pdf/2209.00185

- O que fazem: dado keyframes de uma animacao MAIS um sketch (rascunho) dos
  frames intermediarios, sintetizam os frames finais renderizados
  (video-to-video, nao imagem-para-imagem isolada). Abstract confirma que o
  metodo supera um baseline existente, mas nao encontrei no abstract/pagina
  publica metricas numericas nem resolucao/dataset explicitos -- teria que
  abrir o PDF completo para confirmar (nao consegui extrair o texto do PDF
  neste ambiente).
- **Diferenca critica**: exige um SKETCH humano do movimento intermediario
  como input. Nao gera a animacao do zero/so a partir da pose alvo do corpo
  base -- ainda depende de um artista desenhar a trajetoria aproximada. Nao
  resolve o nosso caso (queremos zero input humano por peca).

**"Sprite Sheet Diffusion: Generate Game Character for Animation"**
Cheng-An Hsieh, Jing Zhang, Ava Yan, dez/2024 (v2 mar/2025).
https://arxiv.org/pdf/2412.03685

- Proposta: usar modelo de difusao para automatizar geracao de sprite
  sheets de animacao completa a partir de poucas poses de referencia.
  Conceitualmente e o que mais se aproxima da nossa pergunta em termos de
  objetivo declarado.
- **Nao consegui verificar resolucao, dataset nem nenhuma metrica numerica**
  -- o PDF nao foi extraivel neste ambiente e nao encontrei versao HTML
  (ar5iv) nem pagina de projeto com resultados. Sem esses dados, nao da para
  avaliar se o resultado e utilizavel ou so uma prova de conceito qualitativa.
  Tratar como "existe, mas resultado nao verificado" -- nao usar como base de
  decisao sem abrir o PDF por outro meio.

## 3. Ferramentas praticas

**Retro Diffusion** (https://retrodiffusion.ai/) -- produto comercial, modelo
de difusao fine-tunado especificamente para pixel art, gera em grades reais
de baixa resolucao (16-384px), com controle de paleta. Anuncia suporte a
walk cycles, sprites de batalha e rotacao em 8 direcoes a partir de prompt,
ou "animar" uma imagem pixel art ja pronta. Nao encontrei benchmark numerico
publicado nem confirmacao de que preserva EXATAMENTE o design de uma peca de
roupa existente entre frames (o caso de uso deles e gerar personagem novo do
zero via prompt, nao "vestir" um design ja fixado como o LPC exige). Tratar
como ferramenta de geracao criativa, nao de derivacao fiel de asset
existente -- nao verificado para o nosso caso de uso.

Nenhuma outra ferramenta open-source madura encontrada especificamente para
"completar animacao faltante de uma peca de roupa dado o corpo-alvo e outras
animacoes da mesma peca". As buscas por "garment transfer 2D pixel art" e
"pixel-level clothing transfer sprites" nao retornaram nenhum trabalho
dedicado a esse subproblema -- so o par Coutinho/Chaimowicz (view synthesis,
nao clothing-on-pose) e ferramentas genericas de geracao de personagem.

## 4. Comunidade LPC -- ninguem tentou automatizar isso

Verifiquei o forum oficial "Improving LPC" (OpenGameArt,
https://lpc.opengameart.org/forumtopic/improving-lpc) e a issue catch-all de
animacoes faltantes no gerador oficial (GitHub, issue #38, **aberta**):
https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator/issues/38

- Nenhuma mencao a machine learning, GAN, difusao ou qualquer automacao
  para gerar animacoes faltantes nos dois canais.
- A estrategia documentada e 100% manual: reaproveitar frames
  duplicados/espelhados dentro da propria peca (ex: "walkcycle tem 94
  frames, dos quais 40 sao duplicatas ou espelhamentos") e pedir
  contribuicao voluntaria de artistas para desenhar o resto.
- Issue #38 e explicita: "do not have any expectations of them getting
  completed as it all depends on who wishes to contribute" -- ou seja, o
  proprio projeto trata isso como debito de arte manual em aberto ha anos,
  sem qualquer tentativa registrada de automacao.

## Veredito

Ninguem, nem na academia nem na comunidade LPC, atacou exatamente o nosso
problema (gerar animacao de MOVIMENTO faltante para uma peca de roupa, dado
o corpo-alvo com a pose definida e outras animacoes da mesma peca como
exemplo de estilo/cor). O trabalho mais proximo (Coutinho & Chaimowicz, UFMG,
2022/2024) usa o mesmo acervo (LPC/Tiny Hero) e a mesma resolucao (64x64) com
resultados numericos solidos (FID 0,115 a 1,508) -- mas resolve um problema
mais facil: sintetizar um ANGULO de camera faltante a partir de outros
angulos da MESMA pose estatica, nao uma pose de movimento nova. Nao ha
evidencia de coerencia temporal entre frames sendo tratada por esses metodos.
SketchBetween trata inbetweening real mas exige sketch humano por frame --
nao e "zero esforco". Sprite Sheet Diffusion (2024) declara o objetivo certo
mas nao tem resultado verificavel neste levantamento.

**Nao vale a pena investir num modelo proprio agora**, pelos seguintes
motivos, nesta ordem de peso:

1. O subproblema exato ("vestir" uma pose alvo conhecida com o estilo de uma
   peca dada, mantendo coerencia entre os multiplos frames de uma animacao
   inteira) nao tem precedente publicado com metrica de sucesso. O trabalho
   mais proximo resolve so a metade mais facil (mudar angulo, nao mudar
   pose), e mesmo assim e trabalho de mestrado/doutorado de um grupo de
   pesquisa dedicado, com dataset de 14 mil imagens pareadas -- o Waybuilder
   tem 627 pecas, das quais so 457 completas (dataset de treino ainda menor,
   por corpo/animacao a contagem de exemplos pareados cai bem abaixo de mil).
2. Treinar do zero, sem literatura que comprove viabilidade no subproblema
   exato, e apostar cego: o risco de gastar semanas de engenharia e nao
   atingir qualidade de producao (pixel-perfect, paleta de 5-6 cores, sem
   artefatos) e alto e nao mensuravel de antemao.
3. A comunidade LPC, que tem o MESMO problema ha anos (issue aberta,
   discussao ativa), nunca tentou nem propos ML para isso -- optou por
   trabalho manual. E sinal indireto, mas relevante, de que a rota manual
   /semi-automatica (reuso de frames espelhados/duplicados, contratar
   pixel artist para completar as 170 pecas) e mais previsivel em custo do
   que P&D de modelo generativo.

Alternativa recomendada: tratar como problema de composicao/reuso
(camadas de sprite por parte do corpo, como sugerido no proprio forum LPC)
ou contratar trabalho manual pontual para as 170 pecas incompletas, em vez
de pesquisa de modelo proprio. Se a pressao por automacao voltar no futuro,
reavaliar quando (e se) "Sprite Sheet Diffusion" ou sucessor publicar
resultado verificavel para ANIMACAO completa (nao so troca de angulo).
