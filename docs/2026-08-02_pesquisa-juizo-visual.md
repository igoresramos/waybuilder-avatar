# O juiz do olho -- a metrica de pixel prediz o julgamento visual?

Pergunta: as metricas do transplante contam pixel; ninguem joga olhando pixel.
Este relatorio olha 30 pecas geradas pelo motor (`transplante.py`, sem
alteracao) e classifica cada uma a olho -- aceitavel, duvidosa, inaceitavel --
para checar se `pixels_diferentes` prediz o veredito visual.

## Metodologia

- Amostra: validacao cruzada leave-one-out, corpo **male**, restrita a pecas
  de **1 camada** (480 de 627 no catalogo -- multi-camada fica de fora porque
  decidir como compor N camadas antes de medir e um problema separado do
  julgamento visual pedido aqui).
- Elegiveis: 386 pecas com `walk` e `idle` (>=2 frames) no corpo male. Das
  quais 350 tem doadora no mesmo `slot` (`escolher_doadora`, IoU da silhueta
  em walk k=0) e par `walk k0 -> idle k1` completo dos dois lados.
- Par usado: doadora `walk k=0 -> idle k=1` (`campo_de_deslocamento`),
  aplicado ao alvo `walk k=0` (`aplicar_campo`), comparado ao alvo `idle k=1`
  real com `pixels_diferentes` -- as tres funcoes sao do motor, sem reimplementacao.
- Amostragem: as 350 pecas ordenadas por erro, cortadas em 3 tercos (116/117/117
  pecas), 10 escolhidas por passo constante dentro de cada terco pra variar o
  slot. Buckets: **baixo** (0-4px), **medio** (6-32px), **alto** (34-206px).
- Figuras: `/home/igor0/waybuilder-avatar/docs/2026-08-02_amostra-visual/`,
  4 paineis (entrada, real, gerado, erro em vermelho), ampliado 6x. Cada uma
  foi conferida com o assert `erro_medido == erro_relatado` antes de eu olhar.

### Baseline recalculado nesta amostra

n = 350 (corpo male, 1 camada -- restricao explicada acima, por isso o n
difere do baseline oficial de 250 pecas):

| metrica | baseline oficial (n=250) | recalculado aqui (n=350) |
|---|---|---|
| frames exatos | 20,0% | **21,4%** (75/350) |
| mediana erro | 28 px | **19 px** |
| media erro | 42,7 px | **36,9 px** |
| min / max | -- | 0 / 423 |

Mesma ordem de grandeza do baseline oficial; a diferenca (mediana mais baixa)
e coerente com a restricao a pecas de 1 camada, que tende a incluir mais
acessorios pequenos (menos area pra errar).

## Os 30 casos, julgados a olho

| bucket | peca | erro (px) | % da area | julgamento | por que |
|---|---|--:|--:|---|---|
| baixo | hat_overlay/tricorne-captain-skull | 0 | 0% | aceitavel | identico |
| baixo | hat/simple-armet | 0 | 0% | aceitavel | identico |
| baixo | facial_eyes/halfmoon-glasses | 0 | 0% | aceitavel | identico |
| baixo | mustache/chevron-mustache | 0 | 0% | aceitavel | identico |
| baixo | head/human-female-small | 0 | 0% | aceitavel | identico |
| baixo | ears/elven-ears | 0 | 0% | aceitavel | identico |
| baixo | shoes/sandals | 0 | 0% | aceitavel | identico |
| baixo | visor/round-visor | 2 | 1,1% | aceitavel | 2px isolados, imperceptivel |
| baixo | eyebrows/thin-eyebrows | 2 | 25,0% | aceitavel | 2px numa peca de 8px, mas sao pontas finas, nao muda o desenho |
| baixo | wrists/lace-cuffs | 4 | 11,8% | aceitavel | ponta da renda, imperceptivel |
| medio | facial_eyes/secretary-glasses | 6 | 7,9% | aceitavel | quina do aro, imperceptivel |
| medio | nose/big-nose | 8 | 57,1% | **duvidosa** | some o brilho/narina -- nariz fica "achatado" |
| medio | hair/parted-2 | 12 | 8,4% | aceitavel | cabelo um pouco mais curto, silhueta ok |
| medio | shoes_toe/thick-plated-toe | 14 | 28,0% | **duvidosa** | amputa a ponta do bico da bota |
| medio | neck/necktie | 16 | 36,4% | aceitavel | encurta a ponta, silhueta ok |
| medio | ears/dragon-ears | 19 | 23,2% | **duvidosa** | perde as pontas claras do chifre/orelha |
| medio | hat_accessory/bicorne-athwart-admiral-cockade | 21 | 56,8% | **inaceitavel** | peca de 37px vira um traco de 16px -- colapso de forma |
| medio | hat_trim/tricorne-stitching | 24 | 57,1% | aceitavel | textura ja e sutil no original; erro fica dentro do ruido visual da propria peca |
| medio | hat/bicorne-athwart-commodore | 28 | 10,5% | **duvidosa** | perde as duas pontas laterais do bicorne |
| medio | hat/tricorne-captain | 32 | 12,3% | aceitavel | so perde a linha de destaque do topo |
| alto | bandana/pirate-bandana | 34 | 16,7% | **duvidosa** | encolhe e perde a borda inteira |
| alto | armour/legion | 36 | 14,6% | **duvidosa** | mancha de cor errada na base |
| alto | hat_trim/tricorne-lieutenant-trim | 44 | 78,6% | **inaceitavel** | fragmenta -- so sobram tracos soltos |
| alto | hair/swoop | 48 | 17,1% | **duvidosa** | perde mecha caida na base |
| alto | clothes/longsleeve | 51 | 14,4% | aceitavel | so ruido de sombra na borda, silhueta certa |
| alto | hair/bangs-bun | 57 | 20,3% | **duvidosa** | amputa as duas mechas laterais |
| alto | clothes/tshirt-vneck | 64 | 24,1% | **duvidosa** | "auro" de sombreamento deslocado no contorno inteiro |
| alto | hair/curly-long | 79 | 18,6% | **inaceitavel** | perde um cacho inteiro de um lado -- fica assimetrico |
| alto | hair/spiked-liberty2 | 118 | 29,1% | **inaceitavel** | perde as pontas -- deixa de parecer "spiked" |
| alto | bandana/mail | 206 | 53,6% | **inaceitavel** | some a saia de malha inteira, so sobra o gorro |

Distribuicao: **16 aceitavel, 9 duvidosa, 5 inaceitavel** (n=30).

## A metrica prediz o julgamento visual?

Em bloco, sim: Spearman entre `pixels_diferentes` bruto e o julgamento (0/1/2)
= **0,92** nesta amostra -- mas a amostra foi estratificada exatamente por
essa metrica, entao a correlacao alta e parcialmente esperada por construcao;
o que importa e onde ela FALHA, e falha nas duas pontas pedidas:

**Erro baixo (relativo) que fica horrivel:**
`hat_accessory/bicorne-athwart-admiral-cockade`, erro=21px, **inaceitavel** --
pior a olho que `clothes/longsleeve`, erro=51px (mais que o dobro),
**aceitavel**, e que `hat/tricorne-captain`, erro=32px, aceitavel. A peca do
cockade tem so 37px de area total; 21px errados e 57% dela, e o formato
colapsa de um pompom redondo pra um traco fino. Erro absoluto baixo, mas
relativo (e visual) catastrofico.

**Erro alto que fica aceitavel:**
`clothes/longsleeve`, erro=51px, **aceitavel** -- e uma peca grande (355px de
area), o erro e so 14% dela e esta todo espalhado em ruido de sombra na
borda, nao em pixel que falta no meio da forma. `hat_trim/tricorne-stitching`,
erro=24px (57% da area!), tambem ficou aceitavel: e um padrao de pontilhado
sutil que ja era quase invisivel no original, entao errar metade dele nao
muda a leitura da peca.

**Conclusao do achado:** nem o erro absoluto nem o percentual da area
isoladamente predizem bem o julgamento -- percentual da area, sozinho,
correlaciona pior com o julgamento (Spearman 0,78) que o erro absoluto
(0,92) nesta amostra. O que decide e o **tipo** de pixel que erra, nao so a
quantidade -- ver secao seguinte.

## Que tipo de defeito e mais feio

Decompus `pixels_diferentes` nas 30 pecas em `falta` (pixel que devia estar e
nao esta), `sobra` (pixel que nao devia estar e esta) e `cor_errada` (pixel no
lugar certo, cor/alpha errada), e contei componentes conexos da silhueta
gerada vs real (BFS 4-conexo, sem scipy). Dados completos em
`decomposicao.json` no scratchpad. Achados:

1. **Fragmentacao (pior)** -- a peca gerada quebra em varios pedacos soltos
   onde a real era uma forma continua (ou o maior pedaco encolhe muito em
   relacao ao maior pedaco real). Os 3 piores casos da amostra tem esse
   padrao: `hat_trim/tricorne-lieutenant-trim` (6 componentes gerados contra
   21 na real, mas o maior vai de 6px pra 4px -- o traco inteiro se desfaz),
   `hair/spiked-liberty2` (perde as pontas, maior componente cai pra 71% do
   da real) e `bandana/mail` (maior componente cai pra 46% -- a saia de malha
   inteira sumiu). **Deteccao automatica:** razao `maior_componente_gerado /
   maior_componente_real` -- abaixo de ~0,75 no dado desta amostra e
   inaceitavel toda vez.
2. **Amputacao assimetrica de parte que define a silhueta** -- falta
   concentrada numa ponta, mecha ou canto que muda o "tipo" da peca
   reconhecivel (bicorne perde as pontas, cabelo perde uma mecha de um lado
   so). O `falta` domina o erro (quase 100% dele) mas o maior componente
   continua unico -- so encolhe e perde simetria. **Deteccao automatica:**
   comparar bbox (altura/largura) da peca gerada com a real; queda de
   >15-20% num eixo sinaliza amputacao numa ponta.
3. **Cor errada / mancha de sombreamento** -- pixel no lugar certo, cor
   errada, formando uma faixa ou "auro" ao longo do contorno
   (`clothes/tshirt-vneck`: 50 de 64px do erro sao `cor_errada`;
   `clothes/longsleeve`: 41 de 51px). Menos grave visualmente que os dois
   tipos acima -- a forma continua correta, so o sombreamento desliza.
   **Deteccao automatica:** razao `cor_errada / erro_total` alta (>60% nesta
   amostra) com `falta` baixo -- e sinal de que a forma esta certa e so a cor
   escorregou; pode ser tolerado com limiar de erro mais alto que os outros
   dois tipos.
4. **Falta de detalhe fino (menos grave)** -- ponta de brilho, linha de
   contorno, pontinho de textura que some mas nao muda a leitura da peca
   (`hat/tricorne-captain` perde so a linha de destaque do topo; `nose/big-nose`
   perde o brilho da narina). Erro concentrado em poucos pixels isolados,
   longe da massa principal da peca. **Deteccao automatica:** pixels de
   `falta` cuja vizinhanca 3x3 no REAL ja tem baixa variancia de cor (ou seja,
   e detalhe fino sobre area lisa) -- tendem a ser cosmeticos, nao estruturais.

Ordem de gravidade visual: **fragmentacao > amputacao assimetrica > cor
errada > detalhe fino**. Um detector automatico de "peca pra revisar manual"
deveria olhar primeiro a razao de maior-componente e a queda de bbox, nao so
o total de `pixels_diferentes` -- e o que este relatorio mostrou que falha
com o cockade e acerta demais com o longsleeve.

## Arquivos

- Figuras (30 PNG): `/home/igor0/waybuilder-avatar/docs/2026-08-02_amostra-visual/`
- Scripts (scratchpad, nao versionados): `medir.py`, `amostrar.py`,
  `gerar_figuras.py`, `decompor.py` em
  `/tmp/claude-1000/-mnt-c-Users-igor0/c3f8f958-20dc-4712-9efc-fdaeea60e7dc/scratchpad/juizo-visual/`
- Dados brutos: `resultados.json` (350 pecas), `amostra.json` (30 escolhidas),
  `manifest.json` (30 + arquivo da figura), `decomposicao.json` (decomposicao
  falta/sobra/cor + componentes conexos) -- todos no mesmo scratchpad.
