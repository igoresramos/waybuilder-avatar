# A gramatica do LPC -- o que a fonte oficial diz

Data: 2026-08-02
Fonte lida: `/home/igor0/waybuilder-avatar/fontes/lpc/` (clone do
Universal-LPC-Spritesheet-Character-Generator)
Escopo: leitura de fonte. Toda afirmacao tem `arquivo:linha`. O que nao esta na
fonte esta marcado como **nao encontrado na fonte**. No fim ha um bloco
separado, `Medicoes`, que e trabalho meu -- nao e documentacao.

---

## 1. A rampa de cor

### O que a fonte declara

**Seis tons por rampa** para todo material, exceto olho, que tem tres.
Medido lendo os 11 arquivos de `palette_definitions/` (script
`scratchpad/gramatica-lpc/ramp_check.py`):

| arquivo | variantes | tons por rampa |
|---|---|---|
| `palette_definitions/body/body_ulpc.json` | 22 | 6 |
| `palette_definitions/body/body_lpcr.json` | 9 | 6 |
| `palette_definitions/cloth/cloth_ulpc.json` | 24 | 6 |
| `palette_definitions/hair/hair_ulpc.json` | 26 | 6 |
| `palette_definitions/hair/hair_lpcr.json` | 20 | 6 |
| `palette_definitions/metal/metal_ulpc.json` | 8 | 6 |
| `palette_definitions/metal/metal_lpcr.json` | 7 | 6 |
| `palette_definitions/wood/wood_ulpc.json` | 4 | 6 |
| `palette_definitions/wood/wood_lpcr.json` | 5 | 6 |
| `palette_definitions/eye/eye_ulpc.json` | 8 | **3** |
| `palette_definitions/eye/eye_lpcr.json` | 7 | **3** |
| `palette_definitions/all/all_lpcr.json` | 75 | 6 |

Nao ha rampa de tamanho variavel na pratica. O guia diz que o sistema aceita
1 a 32 cores (`PALETTE_RECOLOR_GUIDE.md:138`, `:225`), mas o acervo real usa
6 (ou 3, no olho).

### O que cada posicao significa

`PALETTE_RECOLOR_GUIDE.md:147-162` e o unico lugar da fonte que nomeia as
posicoes. Ele documenta um exemplo de 8 posicoes (formato antigo), na ordem
**sombra -> luz**:

```
"#271920",  // Darkest shadow
"#271920",  // Deep shadow
"#99423c",  // Shadow
"#cc8665",  // Mid-tone
"#E4A47C",  // Light mid-tone
"#F9D5BA",  // Highlight
"#FAECE7",  // Bright highlight
"#f8f3eb"   // Lightest highlight
```

E fecha: *"This structure matches how LPC sprites are typically shaded, with
darker colors for shadows and lighter colors for highlights."*
(`PALETTE_RECOLOR_GUIDE.md:162`). A checklist de validacao repete o requisito:
*"Colors represent a logical progression (shadow -> highlight)"*
(`PALETTE_RECOLOR_GUIDE.md:172`).

Nas rampas de 6 tons de hoje isso vira, por posicao: `0` = mais escuro,
`5` = mais claro. Confira `body_ulpc.json` -> `light`:
`["#271920", "#99423c", "#cc8665", "#E4A47C", "#F9D5BA", "#FAECE7"]` -- e o
exemplo do guia com as duas repeticoes removidas.

**A fonte NAO diz que a posicao 0 e o contorno.** Isso e observacao minha, na
secao `Medicoes`.

### De onde vem a luz

**Nao encontrado na fonte.** Nenhum arquivo em `fontes/lpc/` -- markdown, `.ts`
ou JSON -- menciona direcao de luz, "light source", angulo ou convencao de
sombreamento direcional. A busca `grep -rni "light source|shading|outline|
highlight|shadow"` sobre `--include=*.md --include=*.ts` retorna 10 linhas, 9
delas dentro de `PALETTE_RECOLOR_GUIDE.md:147-172` (a progressao acima) e uma em
`renderer.ts:395` (comentario sobre ordem de desenho). A direcao da luz e
implicita na arte. Medi na secao `Medicoes`.

### Como a troca de cor funciona (mecanica)

Casamento **exato por RGB, com tolerancia +-1 por canal**
(`PALETTE_RECOLOR_GUIDE.md:60-73`; implementacao em
`sources/canvas/palette-recolor.ts:86`, parametro `tolerance: number = 1`).
Requisitos formais da paleta em `PALETTE_RECOLOR_GUIDE.md:134-144`: todas as
variantes com o mesmo numero de cores, variante `source` obrigatoria, hex
`#RRGGBB` valido.

Consequencia direta para nos: a paleta de saida de uma peca e **fechada**. Um
pixel que nao caia dentro de +-1 de um tom da rampa nao recolore -- ele fica com
a cor errada quando o usuario troca a variante.

---

## 2. Convencao de sombreamento

**Nao ha regra escrita neste repositorio.** `CONTRIBUTING.md:11` delega para
fora e explicitamente nao obriga:

> *"While it is recommended that all new artwork follows either the refined
> [style guide](https://bztsrc.gitlab.io/lpc-refined/), or the
> [revised guide](https://github.com/ElizaWy/LPC/wiki/Style-Guide), it is not
> required."*

Os dois guias de estilo sao links externos; nenhum dos dois esta no clone. O
que existe de normativo dentro do repo e:

- a progressao sombra->luz da rampa (`PALETTE_RECOLOR_GUIDE.md:147-172`);
- a exigencia de que a arte use **as cores exatas da paleta**, senao a
  recoloracao falha (`PALETTE_RECOLOR_GUIDE.md:471-472`: *"Check that source
  image uses exact palette colors"*);
- uma cor reservada: **magenta `#FF2CE6` (255,44,230) vira transparente** no
  render (`sources/canvas/mask.ts:15-17`). E o unico "pixel com significado"
  codificado na fonte.

Regra sobre licenca/creditos e obrigatoria e barra o build
(`CONTRIBUTING.md:33`); regra sobre desenho, nao.

---

## 3. Organizacao das animacoes no spritesheet

### Grade

- Frame: **64x64** (`sources/state/constants.ts:2`).
- Folha universal completa: **832 x 3456**, isto e 13 colunas x 54 linhas
  (`sources/canvas/renderer.ts:154-155`; 13 frames por linha declarado em
  `constants.ts:6`).
- Direcoes, na ordem das linhas: **`["up", "left", "down", "right"]`**
  (`constants.ts:19`, com o comentario *"LPC sheet row order: should match
  ANIMATION_CONFIGS rows"*). A mesma ordem aparece codificada como
  `{ n: 0, w: 1, s: 2, e: 3 }` em `sources/canvas/draw-frames.ts:72` e
  `:109`.
- Corpos suportados: `male, female, teen, child, muscular, pregnant`
  (`constants.ts:9-16`).

### Tabela de animacoes

`constants.ts:105-121` (`ANIMATION_OFFSETS`, linha inicial) cruzado com
`constants.ts:124-154` (`ANIMATION_CONFIGS`: `row`, `num` = numero de linhas /
direcoes, `cycle` = ordem de reproducao). A coluna "frames" e o numero real de
quadros distintos, que eu conferi medindo a largura dos PNGs de
`spritesheets/body/bodies/male/`:

| animacao | linha | linhas (dir.) | frames | ciclo declarado | PNG male |
|---|---:|---:|---:|---|---|
| spellcast | 0 | 4 | 7 | `[0..6]` | 448x256 |
| thrust | 4 | 4 | 8 | `[0..7]` | 512x256 |
| walk | 8 | 4 | 9 | `[1..8]` | 576x256 |
| slash | 12 | 4 | 6 | `[0..5]` | 384x256 |
| shoot | 16 | 4 | 13 | `[0..12]` | 832x256 |
| hurt | 20 | **1** | 6 | `[0..5]` | 384x64 |
| climb | 21 | **1** | 6 | `[0..5]` | 384x64 |
| idle | 22 | 4 | **2** | `[0, 0, 1]` | 128x256 |
| jump | 26 | 4 | 5 | `[0,1,2,3,4,1]` | 320x256 |
| sit | 30 | 4 | 3 | `[0x5, 1x5, 2x5]` | 192x256 |
| emote | 34 | 4 | 3 | `[0x5, 1x5, 2x5]` | 192x256 |
| run | 38 | 4 | 8 | `[0..7]` | 512x256 |
| combat_idle | 42 | 4 | **2** | `[0, 0, 1]` | 128x256 |
| backslash | 46 | 4 | 13 | `[0..5,7..12]` | 832x256 |
| halfslash | 50 | 4 | 6 | `[0..5]` | 384x256 |

`hurt` e `climb` tem **uma linha so** (`num: 1`, `constants.ts:130-131`) --
nao existe versao por direcao. `hurt` ocupa a linha 20 e `climb` a 21, por isso
o pulo curto entre os offsets.

Tres pontos que importam para nos:

1. **`idle` tem apenas 2 quadros** (`constants.ts:132`, PNG 128x256). Toda a
   animacao de respiro do LPC e um par de poses. Mesma coisa em `combat_idle`
   (`constants.ts:146`).
2. **O ciclo de `walk` comeca em 1, nao em 0** (`constants.ts:127`:
   `cycle: [1,2,3,4,5,6,7,8]`). O quadro 0 de `walk` **existe no arquivo mas
   nao e tocado na animacao**. E o quadro neutro, em pe. A mesma ideia aparece
   nomeada em `custom-animations.ts:336`, `skipFirstFrameInPreview: true` para
   `walk_128`.
3. Os arquivos de arte de hoje sao **um PNG por animacao** (`walk.png`,
   `idle.png`, ...), montados em folha unica so na hora do render
   (`renderer.ts:313`, `:480`: `drawImage(imageToDraw, 0, item.yPos)`, com
   `yPos` vindo de `ANIMATION_OFFSETS`). O caminho e
   `spritesheets/{basePath}{animName}[/{variante}].png`
   (`sources/state/path.ts:157`).

### Nomes que nao batem

`constants.ts:74` declara `{ value: "combat", label: "Combat Idle",
folderName: "combat_idle" }`. Ou seja: **na metadata a animacao se chama
`combat`, no disco a pasta se chama `combat_idle`**. Mesma coisa em
`1h_slash`/`1h_backslash` -> pasta `backslash` (`constants.ts:75-85`) e
`watering`, que **nao tem arte propria**: reusa a linha de `thrust`
(`constants.ts:145`: `watering: { row: 4, ... }`, e a excecao explicita em
`renderer.ts:324-330`).

---

## 4. Animacoes DERIVADAS -- o precedente direto

**Sim, o gerador deriva animacao de animacao, e o mecanismo e exatamente o que
estamos tentando fazer, so que na versao trivial.**

### O mecanismo

`sources/custom-animations.ts` define um dicionario
`customAnimations: Record<string, CustomAnimationDefinition>`
(`custom-animations.ts:39`). Cada definicao e
(`custom-animations.ts:30-37`):

```ts
type CustomAnimationDefinition = {
  frameSize: number;
  frames: string[][];          // [linha][coluna] -> "animacaoBase-direcao,indice"
  skipFirstFrameInPreview?: boolean;
  sourceSingleAnimation?: boolean;
};
```

`frames` e uma **tabela de reindexacao**. Cada celula e uma string
`"<anim>-<dir>,<k>"`, por exemplo `"sit-n,2"` ou `"slash-w,5"`. A animacao
nova nao tem arte nenhuma: ela e uma lista de ponteiros para quadros que ja
existem em outra animacao.

O desenho esta em `sources/canvas/draw-frames.ts:49-93`
(`drawFramesToCustomAnimation`): para cada celula, faz split em `","`, resolve
a linha de origem (`draw-frames.ts:69-76`) e a coluna
(`srcX = FRAME_SIZE * srcColumn`, `:78`), e copia o retangulo de 64x64 para a
posicao da grade nova (`drawFrameToFrame`, `:12-47`). Quando o frame de destino
e maior que o de origem, a origem e **centralizada**, nao escalada
(`draw-frames.ts:33-45`: `offset = (destFrameSize - srcFrameSize) / 2`).

Uma nota sobre a tabela de linhas: `animationRowsLayout`
(`custom-animations.ts:3-28`) mapeia `"walk-n" -> 7`, `"sit-n" -> 29`,
`"slash-n" -> 11`, `"thrust-n" -> 3`, `"backslash-n" -> 45`,
`"halfslash-n" -> 49`. Em **todos** os casos o valor e exatamente **`row - 1`**
em relacao a `ANIMATION_CONFIGS` de `constants.ts:124-154` (walk 8, sit 30,
slash 12, thrust 4, backslash 46, halfslash 50). Nao ha comentario na fonte
explicando a diferenca. Na pratica ela raramente e alcancada: o ramo que usa
essa tabela so roda quando a imagem de origem tem mais de 256 px de altura
(`draw-frames.ts:59` e `:69-76`), e 76.777 dos ~88.000 PNGs de `spritesheets/`
tem exatamente 256 px -- caem no ramo alternativo, que usa `{n:0,w:1,s:2,e:3}`.
Sobram 27 folhas universais de 3.456 px. Registro como observacao; **nao
encontrado na fonte** se e intencional.

`customAnimationBase` (`custom-animations.ts:670-671`) le a primeira celula e
extrai o nome da animacao base -- e assim que o renderer sabe de qual animacao
padrao ele tem que puxar todas as OUTRAS camadas do personagem para dentro da
area nova (`renderer.ts:494-537`).

### Os casos concretos

| animacao derivada | de onde tira | o que faz |
|---|---|---|
| `wheelchair` (`custom-animations.ts:40-48`) | `sit`, quadro 2, 4 direcoes | congela: 2 quadros iguais |
| `slash_128`, `halfslash_128`, `thrust_128`, `walk_128`, `backslash_128` | mesma animacao | so muda o tamanho do frame (64 -> 128) |
| `thrust_oversize`, `slash_oversize` | mesma animacao | frame 192 |
| `slash_reverse_oversize` (`:430-466`) | `slash` | **inverte a ordem**: `5,4,3,2,1,0` |
| `tool_rod` (`:49-113`) | `thrust` | reordena e repete: `0,1,2,3,4,5,4,4,4,5,4,2,3` |
| `tool_whip` / `whip_oversize` (`:467-556`) | `slash` | reembaralha: `0,1,5,4,3,3,2,1` |
| `tool_axe` (`:557-610`) | `slash` | inverte e segura: `5,5,4,4,3,1,0,0,0,0` |
| `tool_hammer` (`:611-660`) | `slash` | idem, 9 quadros |

Contagem no acervo: **32 sheet definitions**, somando **85 camadas** com o campo
`custom_animation` (`thrust_oversize` 20, `slash_oversize` 18, `walk_128` 18,
`slash_128` 8, `slash_reverse_oversize` 5, `tool_axe` 4, e 2 camadas cada para
`wheelchair`, `backslash_128`, `halfslash_128`, `tool_whip`, `tool_hammer`,
`tool_rod`).

### Por que isso importa para o transplante

O precedente que a fonte estabelece e claro, e e mais conservador do que o
nosso: **quando falta animacao, o LPC reusa quadro inteiro, reordenado. Nunca
sintetiza pixel.** Ele copia, inverte a ordem, repete, congela e recentra --
mas cada quadro de saida e um quadro de entrada, byte a byte.

Duas leituras:

- **A favor do transplante**: reuso de pose ja e doutrina oficial. Ninguem vai
  achar estranho que uma peca sem `idle` tire o `idle` de outro lugar.
- **Contra o transplante como esta**: o LPC nunca deforma. `aplicar_campo`
  produz um quadro que nao existe em lugar nenhum. A operacao mais proxima do
  que a fonte considera legitimo e **transladar/recentrar um quadro existente**
  (`draw-frames.ts:34`), nao remapear pixel a pixel. A secao `Medicoes` mostra
  que a operacao conservadora e tambem a que acerta mais.

---

## 5. Materiais

Existem **seis**, e sao exatamente as pastas de `palette_definitions/`:
`body`, `cloth`, `eye`, `hair`, `metal`, `wood` (mais `all`, que e um
agregado). Cada pasta tem um `meta_*.json` que declara o material -- este e o
texto integral do que a fonte diz sobre cada um:

| material | label | descricao (`palette_definitions/{m}/meta_{m}.json`) | variante base |
|---|---|---|---|
| `body` | Skintone | *"Palettes designed for skin tones and flesh colors, but may include fantasy colors."* | `light` |
| `cloth` | General | *"Palettes designed for general colors, but especially cloth or fabric."* | `white` |
| `hair` | Hair | *"Palettes designed to look good for hair colors, but also may include fantasy colors."* | `orange` |
| `metal` | Metal | *"Palettes designed for metallic surfaces such as weapons and armor."* | `steel` |
| `wood` | Wood | *"Palettes designed for wooden surfaces such as bows and staves."* | `maple` |
| `eye` | Eyes | *"Palettes designed for eye colors. These only use 3 palettes and are not interchangeable with other types."* | `blue` |
| `all` | Any | *"Choose from any palette from any material type (except eyes)."* | `white` |

Uso no acervo: **415 dos 656 sheet definitions declaram `recolors`**, somando
**454 declaracoes de material** (uma peca pode ter mais de um canal de cor):
`cloth` 144, `hair` 133, `body` 85, `metal` 62, `eye` 19, `wood` 11. Os outros
241 sheets usam `variants` com um PNG por cor.

Forma da declaracao, em `sheet_definitions/headwear/helmets/helmets/hat_helmet_barbuta.json`:

```json
"recolors": { "material": "metal", "palettes": ["ulpc", "lpcr", "all.lpcr"] }
```

**Nao ha `leather` nem `fur` como material.** `PALETTE_RECOLOR_GUIDE.md:206-212`
lista `cloth-metal` e `fur` como paletas disponiveis, mas **nenhum dos dois
existe em `palette_definitions/`** -- o guia esta desatualizado nesse ponto.
"leather" existe apenas como **nome de variante** dentro da paleta `cloth`
(`cloth_ulpc.json`, chave `leather`), nao como material.

**O que a fonte diz sobre o comportamento otico de cada material: nada.** Nao
ha regra sobre metal ter contraste maior, especular, ou coisa do tipo. So os
textos de uma linha da tabela acima. O unico dado quantitativo e a diferenca
de tamanho de rampa: eye = 3 tons, todo o resto = 6.

---

## 6. zPos

### O que a fonte diz explicitamente

- **E ordem de desenho, e so isso, formalmente.** `renderer.ts:395-397`:
  *"Sort by zPos (lower zPos = drawn first = behind). Shadow (zPos=0) before
  body (zPos=10), etc."*, seguido de `drawCalls.sort((a, b) => a.zPos - b.zPos)`.
- E **por camada**, nao por peca: `CONTRIBUTING.md:46` -- *"A category can
  exist of n-layers. For each layer, define the z-position the sheet needs to
  be drawn at."*
- O JSON manda; o CSV e so uma visao. `CONTRIBUTING.md:367` (grifo do original):
  *"please remember that the JSON files will always contain the source of truth
  with regard to the z-position an asset will be rendered at."*
- A UI documenta quatro ancoras: `0=shadow`, `10=body`, `70=arms`, `110=beard`
  (`sources/components/advanced/AdvancedTools.ts:69-76`).

### O que ele codifica de fato

Levantei todas as 888 camadas dos 656 sheet definitions e agrupei por
`type_name` (script `scratchpad/gramatica-lpc/`, nao salvo -- one-liner
`python3` sobre `sheet_definitions/**/*.json`). **zPos agrupa por regiao do
corpo, sim, e a escala e legivel:**

| faixa | regiao | exemplos (`type_name`, zPos) |
|---|---|---|
| -2 .. 9 | **atras do corpo** | `weapon` -1, `shadow` 0, `shield` 2, `wings` 5, `cape` 5, `tail` 5, `quiver` 8, `hair` 9 |
| 10 | corpo | `body` 10 |
| 14 .. 27 | pes e pernas | `socks` 14, `shoes` 15, `legs` 20, `shoes_toe` 27 |
| 30 .. 59 | torso | `dress` 30, `clothes` 35, `overalls` 38, `vest` 45, `chainmail` 50, `jacket` 55 |
| 60 .. 81 | bracos e cintura | `arms` 60, `armour` 60, `bauldron` 65, `sash` 65, `gloves` 70, `belt` 70, `ring` 75, `necklace` 80 |
| 90 .. 99 | pescoco | `neck` 90, `cape_trim` 90, `accessory` 95 |
| 100 .. 107 | cabeca e rosto | `head` 100, `expression` 101, `wrinkles` 102, `eyes` 105, `nose` 105, `ears` 105, `eyebrows` 106 |
| 110 .. 128 | pelo facial e cobertura | `beard` 110, `mustache` 111, `facial_eyes` 115, `earrings` 115, `bandana` 120, `headcover` 125, `updo` 128 |
| 130 .. 150 | chapeu e o que fica na frente de tudo | `hat` 130, `visor` 132, `hair` 145, `weapon` 150, `ammo` 150 |

Ou seja: **a escala e anatomica, de dentro para fora, de baixo para cima**, com
uma faixa reservada abaixo de 10 para o que fica atras do corpo.

### O detalhe que interessa: o par bg/fg

Varios `type_name` aparecem com **dois valores muito distantes** -- por exemplo
`hair` em 9, 120 **e** 145; `cape` em 5 e 85; `weapon` em -1 e 140/150. Nao e
inconsistencia: sao **camadas diferentes da mesma peca**, uma atras do corpo e
uma na frente. Em `sheet_definitions/torso/cape/cape_tattered.json`:

```json
"layer_1": { "zPos": 85, "male": "cape/tattered/fg/", ... },
"layer_2": { "zPos":  5, "male": "cape/tattered/bg/", ... }
```

`fg`/`bg` no proprio caminho do arquivo. **`zPos < 10` = a camada fica atras do
corpo.** Isso vale como sinal barato para o transplante: uma camada `bg` e
geometricamente diferente da `fg` da mesma peca e nao deve doar movimento para
ela nem herdar dela.

Alem de zPos, o unico campo com semantica de ordenacao e `priority`
(`sheet_definitions/body/body.json:3`) -- **nao encontrado na fonte**
documentacao explicando o que ele faz; nao aparece em `renderer.ts`.

---

## 7. Regras sobre como uma peca deve se comportar em cada animacao

**Nao ha regra de arte escrita.** O que ha e regra de *declaracao*:

- A lista `animations` no sheet definition e **opcional**
  (`CONTRIBUTING.md:49-59`): *"You do not have to feel obligated to fill out
  all animations, and some assets may not work well on all animations anyway."*
- Se a lista for omitida, o gerador assume o conjunto **legado de 7**:
  `spellcast, thrust, walk, slash, shoot, hurt, watering`
  (`constants.ts:94-102` = `ANIMATION_DEFAULTS`; texto identico em
  `CONTRIBUTING.md:61-69`).
- A consequencia declarada e apenas de filtro/UI: *"Users will still be able to
  access your asset, but it won't appear if the animations filter is used"*
  (`CONTRIBUTING.md:71`).

Isso explica exatamente o nosso problema. Contando os **656** sheet definitions
(os outros 112 arquivos JSON de `sheet_definitions/` sao config de pasta --
so `priority`, `label`, `required`): **78 nao tem o campo `animations`** e
portanto ficam presos nas 7 legadas. Suporte por animacao, ja contando o
default implicito nesses 78:

```
walk 645 | hurt 618 | thrust 616 | shoot 614 | spellcast 611 | slash 611
watering 570 | idle 532 | emote 488 | sit 482 | jump 481 | run 479
climb 473 | combat 469 | 1h_slash 468 | 1h_backslash 468 | 1h_halfslash 468
```

O degrau `walk 645 -> idle 532 -> run 479` (113 e 166 pecas de buraco) e o mesmo
buraco de 170 pecas do acervo Waybuilder, visto do lado do upstream.

Terminologia oficial, para nomear as camadas historicas
(`README.md:127-138`): **LPC** = base original (spellcast, slash, thrust, walk,
shoot, hurt; male e female adultos; 64x64); **ULPC** = acrescentou frames
oversize para armas; **LPCR** (ElizaWy) = mudou numero e ordem de frames,
paleta nova, cabecas menores; **LPCE** = acrescentou bow, climb, run, jump e as
bases child/elderly -- e o README admite: *"Many of the assets in this
repository are not yet drawn for these new animations and bases. Help wanted."*

O guia de animacao existe mas **fora deste repositorio**: `README.md:81` aponta
para `github.com/ElizaWy/LPC/.../Animation Guides`. Nao esta no clone.

### O unico "comportamento" codificado

Duas coisas na fonte descrevem comportamento de peca em animacao, e as duas sao
mecanicas, nao artisticas:

1. `match_body_color` (79 sheets, ex. `sheet_definitions/body/body.json:13`):
   quando uma parte colorida como pele muda de variante, todas as outras com a
   flag acompanham (`sources/state/state.ts:202-219`).
2. `custom_animation` no nivel da camada (85 camadas): tira a peca do fluxo
   padrao e joga na tabela de reindexacao da secao 4 (`renderer.ts:283-310`).

---

# Medicoes

Tudo abaixo e **medido por mim**, nao e documentacao. Scripts em
`/tmp/claude-1000/-mnt-c-Users-igor0/a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/gramatica-lpc/`.
Metrica: `pixels_diferentes` de `transplante.py`. Amostra declarada em cada
linha.

## M1. A arte e quantizada e a paleta e fechada

Amostra: 60 pecas com `canais_de_cor`, corpo `male`, camada 1, faixa `base`,
quadro `walk` k=0 (`ramp2.py`).

- Cores distintas visiveis por quadro: **mediana 6**, minimo 1, maximo 12.
- Em 44 das 60, **todas** as cores do quadro caem exatamente numa rampa
  declarada de `palette_definitions/`. As excecoes sao pecas multi-material
  (contorno de metal em peca de pano, etc.), onde 6 casam e o resto vem da
  segunda rampa.

Amostra: 80 pecas (`ramp3.py`).

- **Alfa e binario: 95,23% dos pixels tem alfa 0 e 4,76% tem alfa 255.**
  Zero pixels em valor intermediario. Nao ha antialiasing.

**Consequencia:** qualquer saida do transplante pode ser projetada de volta na
rampa da peca sem custo e sem risco -- um "snap" para o tom mais proximo da
rampa e para alfa 0/255 nao pode piorar nada e corrige pixel de cor invalida.

## M2. Contorno = tom 0 da rampa

Mesma amostra de 80 pecas. Separei pixel de borda (visivel com algum vizinho
4-conectado invisivel) de pixel interno, e classifiquei pelo indice na rampa:

| indice (0 = mais escuro) | 0 | 1 | 2 | 3 | 4 | 5 | fora da rampa |
|---|---:|---:|---:|---:|---:|---:|---:|
| **contorno** | **66,5%** | 15,1% | 8,0% | 5,0% | 1,4% | 0,5% | 3,5% |
| **interior** | 5,2% | 11,1% | 19,2% | 22,9% | 26,5% | 11,6% | 3,5% |

A posicao 0 da rampa e o contorno, com 13x mais densidade na borda que no
interior. A fonte nao diz isso (secao 1), mas a arte diz.

## M3. A luz vem de cima, e so de cima

Amostra: 120 pecas (`luz.py`). Para cada quadro, centroide dos pixels claros
(indices 4-5) menos centroide dos pixels de sombra (indices 1-2):

- **dy = -1,30 px em media** (mediana -1,09). Em **78%** das pecas o claro fica
  acima da sombra.
- **dx = -0,64 px em media, mediana -0,01.** Exatamente **50%** das pecas tem o
  claro a esquerda.

Luz **frontal-superior, sem componente lateral**. Duas implicacoes praticas:

- **Espelhar uma doadora no eixo horizontal e legitimo** -- a iluminacao nao
  quebra. Dobra o pool de doadoras se alguma frente quiser tentar.
- **Deslocar uma peca verticalmente muda o sombreamento correto.** E o unico
  eixo onde translacao pura tem custo artistico.

## M4. `walk` k=0 e o quadro neutro -- e ele ja e o `idle` k=0

Amostra: 493 pecas do acervo Waybuilder com `walk` e `idle` em `male`
(`frame0.py`).

| par comparado | quadros identicos | mediana | media |
|---|---:|---:|---:|
| `walk` k=0 vs `idle` k=0 | **88,4%** | 0 | 11,0 |
| `walk` k=0 vs `idle` k=1 | 13,4% | 98 | 116,2 |
| `idle` k=0 vs `idle` k=1 | 14,0% | 90 | 113,2 |

Confirma pelo lado da arte o que `constants.ts:127` diz pelo lado do codigo: o
quadro 0 de `walk` nao pertence a caminhada, e a pose parada. Em 88% das pecas
ele **e**, byte a byte, o quadro 0 do `idle`.

**Isso reduz o problema.** Nao precisamos gerar `idle` (2 quadros). Precisamos
gerar **um** quadro: `idle` k=1. O k=0 sai de graca, copiando `walk` k=0.

## M5. `idle` k=1 e uma translacao rigida de `walk` k=0

Este e o achado que muda a escolha da doadora.

Amostra: **463 pecas** (`male`, camada 1, faixa `base`, com `walk` e `idle`, com
pelo menos 20 pixels visiveis). Validacao cruzada **por peca**: nas linhas C, a
peca de teste nunca contribui com o proprio deslocamento.

| metodo | n | frames exatos | mediana | media |
|---|---:|---:|---:|---:|
| **A) baseline oficial** -- doadora do mesmo slot por maior IoU + `campo_de_deslocamento`/`aplicar_campo` | 437 | **18,5%** | 27 | 41,0 |
| **B) regra fixa** -- copiar `walk` k=0 deslocado 1 px para cima | 463 | **67,4%** | 0 | 34,4 |
| **C) leave-one-out** -- deslocamento = moda das OUTRAS pecas do mesmo slot | 463 | **71,9%** | 0 | 28,9 |
| D) copiar `walk` k=0 sem deslocar (controle) | 463 | 5,6% | 115 | 135,9 |
| O) oraculo -- melhor deslocamento inteiro por peca (nao usavel, so mede a estrutura) | 463 | 73,4% | 0 | 24,1 |

O baseline recalculado na minha amostra da **18,5% / mediana 27 / media 41,0**,
compativel com o oficial (20,0% / 28 / 42,7) -- a diferenca e a amostra (463
pecas de todos os slots contra 250).

A linha C ganha da linha A por **3,9x em frames exatos**, com validacao
cruzada, sem campo de deslocamento, sem patch matching, sem nada.

E o deslocamento e anatomicamente coerente, por slot:

| slot | n | deslocamento modal | exatos (C) | exatos (baseline A) |
|---|---:|---|---:|---:|
| head | 32 | 1 px para cima | **100%** | 44% |
| charm | 16 | 1 px para cima | **100%** | 19% |
| hat_trim | 13 | 1 px para cima | **100%** | 0% |
| facial_eyes | 13 | 1 px para cima | **100%** | 38% |
| accessory | 9 | 1 px para cima | **100%** | 11% |
| visor | 9 | 1 px para cima | **100%** | 44% |
| ears | 9 | 1 px para cima | **100%** | 22% |
| hat | 50 | 1 px para cima | 92% | 28% |
| shoes | 12 | **parado** | 92% | 42% |
| neck | 8 | 1 px para cima | 88% | 12% |
| hair | 89 | 1 px para cima | 87% | 13% |
| tail | 5 | 1 px para cima | 80% | 60% |
| hairextl | 7 | 1 px para cima | 71% | 0% |
| wings | 5 | 1 px para cima | 60% | 40% |
| hairextr | 7 | 1 px para cima | 57% | 0% |
| legs | 15 | **parado** | 40% | 13% |
| clothes | 22 | 1 px para cima | **0%** | 0% |
| shield_pattern | 46 | parado | **0%** | 0% |

Conferi o sinal medindo a caixa delimitadora: `head` sobe exatamente
`-1` px em topo e base (n=32); `hair` sobe `-0,98`/`-0,94` (n=89); `shoes` fica
em `0,0,0,0` (n=12) (`sinal.py`).

**A gramatica que isso revela**: o `idle` do LPC e um respiro. O corpo sobe
1 pixel; **os pes ficam plantados no chao**. Tudo que esta preso a cabeca ou ao
tronco sobe junto, rigidamente. Tudo que toca o chao nao se mexe. Por isso
`head`, `hat`, `hair`, `ears`, `charm`, `visor` acertam 100% ou perto; e por
isso `shoes` e `legs` tem moda "parado".

Os dois fracassos sao informativos e delimitam o escopo:

- **`clothes` (0%)**: a roupa cobre o tronco **e os bracos**. Os bracos nao
  acompanham o tronco rigidamente no `idle`, entao nao ha translacao unica que
  sirva. E onde o transplante com campo de deslocamento tem razao de existir --
  so que ele tambem da 0% ali.
- **`shield_pattern` (0%)**: o escudo esta na mao. A caixa delimitadora anda
  **+20 px em x** entre `walk` k=0 e `idle` k=1 -- nao e respiro, e a mao mudando
  de posicao. Nao e um problema de translacao pequena.

---

# Sintese: o que a gramatica autoriza

1. **A saida e quantizada e fechada.** 6 tons por rampa (3 no olho), alfa
   binario, sem antialiasing, contorno no tom 0. Um passo de "snap na rampa" no
   fim do pipeline e gratuito e nao pode piorar.
   (`PALETTE_RECOLOR_GUIDE.md:147-172`, `palette-recolor.ts:86`, M1/M2)
2. **O LPC ja resolve "falta animacao" reusando quadro, nunca sintetizando.**
   Copia, inverte, repete, congela, recentra -- sempre quadro inteiro, byte a
   byte. Deformar pixel a pixel nao tem precedente na fonte.
   (`custom-animations.ts:39-661`, `draw-frames.ts:12-93`)
3. **O quadro 0 de `walk` e a pose neutra e nao pertence a caminhada.**
   `cycle: [1..8]` (`constants.ts:127`). Em 88,4% das pecas ele e identico ao
   `idle` k=0 (M4). O problema tem **um** quadro de saida, nao dois.
4. **`idle` k=1 e `walk` k=0 movido 1 px para cima, com os pes parados.**
   Regra por slot, validada por peca: **71,9% de frames exatos contra 18,5% do
   baseline transplante na mesma amostra de 463 pecas** (M5).
5. **`zPos` e uma escala anatomica**, e `zPos < 10` significa "atras do corpo".
   Camada `bg` e camada `fg` da mesma peca sao geometrias diferentes e nao devem
   trocar movimento. (`renderer.ts:395`, `cape_tattered.json`)
6. **Luz frontal-superior sem componente lateral** -- espelhar horizontalmente
   uma doadora nao quebra o sombreamento (M3).
7. **Nao ha guia de estilo dentro do repositorio.** `CONTRIBUTING.md:11`
   recomenda dois guias externos e explicitamente nao os obriga. Nao ha regra
   escrita sobre direcao de luz, comportamento otico de material, ou como uma
   peca deve se mover em cada animacao.
