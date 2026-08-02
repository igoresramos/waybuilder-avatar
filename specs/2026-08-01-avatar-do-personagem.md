---
spec: avatar-do-personagem
project: waybuilder
version: 11
status: aprovada
created: 2026-08-01
revisao: adversarial (fable, 2026-08-01) -- derrubou o dimensionamento do
  renderer e a entrega de assets; a estrutura de dados foi remedida depois
  @3 (2026-08-01) -- o acervo saiu para o repo `waybuilder-avatar`; as
  decisoes 8b e 10 foram reescritas e a ponte de deploy virou divida declarada
  @4 (2026-08-01) -- decisao 6b: o slot vem do `type_name`, nunca do caminho.
  Nasceu de um prototipo que tratou `head` como escolha unica e apagou os 15
  slots que convivem com ela
  @5 (2026-08-01) -- decisoes 5c/5d/5e: a tela vira painel de casas por slot,
  com `combina_com` e `sem_arte`, e o desenho ganha desempate de `zPos`
  @6 (2026-08-01) -- decisao 3c cumprida: atlas consolidado por slot, com teto
  de textura. Licenca: uso pessoal nao-comercial, creditos seguem emitidos
  @7 (2026-08-02) -- decisoes 11 e 12: as 170 pecas legadas deixam de sumir. A
  animacao que falta e gerada por transplante de peca analoga (deterministico,
  defeito medido e assumido pelo dono), e o que o transplante nao cobrir aparece
  parado. Tres caminhos medidos antes, relatorios em `docs/`
  @10 (2026-08-02) -- decisao delegada ao PO (parecer em
  `docs/2026-08-02_PO-direcoes-e-entrega.md`): as 4 direcoes entram com as 5
  animacoes, e o acervo passa a ser servido do GitHub Pages (decisao 2a nova).
  O teto de 100 MB deixa de reger o recorte; o item 2 de "Aberto" fecha como
  consumo em runtime; a decisao 4 e reconciliada com o codigo.
  (O `version` pula de 7 para 10 porque o corpo ja carregava blocos @9 que o
  frontmatter nunca registrou -- a numeracao do corpo e que estava certa.)
  @11 (2026-08-02) -- decisoes 11b e 11c, saidas da pesquisa do transplante com
  passe adversarial: o `idle` sai do transplante e passa a um roteador por
  RIGIDEZ, com limiares medidos (os que a propria pesquisa recomendou eram
  chute e perderam na varredura); `sit` deixa de ser gerado; `idle` k=0 vira
  copia de `walk` k=0. Fecha o item 145. O numero de manchete da pesquisa
  (77,6%) e das pecas que ja tem a arte -- em alvo legado real e ~14%
---

# Spec -- o avatar do personagem

Uma janelinha dentro do Waybuilder onde o jogador monta o boneco do personagem
trocando cabelo, roupa, armadura e arma, estilo Stardew Valley. A fonte de arte
e o acervo do Liberated Pixel Cup.

## O que isto NAO e

- **Nao e derivacao.** O avatar nao e calculado a partir da ficha. O jogador
  escolhe; o app no maximo **sugere** (decisao 9).
- **Nao toca o motor.** Nao entra em `visao()`, nao entra nas fixtures, nao
  afeta a paridade Python/TS, nao vira efeito, nao vira slot. As duas
  implementacoes do motor seguem identicas depois desta spec.
- **Nao toca o pipeline nem a base canonica.** O acervo de sprites e um segundo
  artefato, com build proprio e vocabulario proprio.

> A razao de escrever isto primeiro: e a unica feature grande do projeto que
> nao interage com nenhum dos tres P0 da avaliacao de arquitetura nem com as
> frentes de correcao dos 13 itens. Ela pode andar em paralelo sem risco de
> conflito -- desde que a fronteira acima seja respeitada.

## A fonte, medida

`github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator`
-- GPL-3.0 no codigo, arte com licenca **por peca** (CC0, CC-BY, CC-BY-SA 3.0,
OGA-BY 3.0, GPL 3.0). Repo de 1,57 GB, ativo (push em 2026-07-28).

| medida | valor |
|---|---|
| `sheet_definitions/*.json` | **768** |
| PNGs em `spritesheets/` | **88.235**, somando **129,6 MB** |
| variantes de corpo (diretorios) | 8: child, female, male, muscular, pregnant, skeleton, teen, zombie |
| variantes que uma peca mapeia | 5: male, muscular, female, pregnant, teen |

Definitions por categoria: headwear 149, head 139, hair 137, torso 120,
weapons 110, body 41, legs 27, feet 22, arms 14, tools 9.

> A primeira medicao, pela API do GitHub, deu 56.723 PNGs / 81,2 MB e estava
> **errada por truncamento** da arvore. Os numeros acima vem do clone local, no
> pin. E a razao de o passo de build registrar o peso medido (3h) em vez de
> confiar em estimativa.

### O funil do recorte, medido no acervo real

| etapa | arquivos | MB |
|---|---|---|
| acervo completo | 88.235 | 129,6 |
| so as 5 animacoes | 27.769 | 35,7 |
| menos child/muscular/skeleton/zombie | 22.925 | 31,8 |
| recomprimido (RGBA -> paleta indexada) | 22.925 | 22,7 |
| **so a direcao de frente** | 22.925 | **8,1** |

O maior corte isolado e a direcao (75%). O segundo e a animacao (72,5% do
acervo completo). A recompressao ganha 29% porque ~15% dos arquivos ainda vem
em RGBA de 8 bits em vez de paleta indexada de 4.

### O acervo esta no meio de uma migracao, e isso decide o desenho

Existem **dois formatos coexistindo**. Medido no clone completo: **76.491**
arquivos no formato antigo, **11.744** no novo -- soma 88.235, o total do
acervo.

> Corrigido em @3. Ate entao esta linha dizia "29.741 e ~27 mil", que somam
> 56.741 -- os mesmos ~56,7 mil que a secao acima ja marca como **errados por
> truncamento** da API do GitHub. O total foi corrigido quando o clone local
> chegou; este par ficou para tras. O `build.py` sempre teve os numeros certos.

```
spritesheets/hair/afro/adult/idle.png                  <- NOVO: 1 arquivo por animacao,
                                                          cor aplicada por paleta
spritesheets/backpack/backpack/female/hurt/black.png   <- ANTIGO: animacao e diretorio,
                                                          cor e arquivo
```

No formato novo o definition declara a paleta:

```json
{ "name": "Afro",
  "recolors": { "material": "hair", "palettes": ["ulpc", "lpcr", "all.lpcr"] },
  "layer_1": { "zPos": 120, "male": "hair/afro/adult/", ... } }
```

> **`body` e `hair` ja migraram.** Sao o nucleo de qualquer avatar. Sem
> implementar o recolor por paleta, o app fica **sem cor de pele e sem cor de
> cabelo** -- nao e um refinamento, e a feature.

## Decisoes

**1. Nao copiar codigo do gerador -- mas CONSULTAR e obrigatorio.** Sao duas
coisas, e a v1 desta spec as deixou coladas. Reescrita em @7, depois de o erro
se repetir tres vezes.

- **Copiar codigo: nao.** GPL-3.0 contaminaria o Waybuilder, e o app deles e
  Mithril contra o React daqui. A composicao e escrita do zero.
- **Ler o gerador para descobrir o formato do acervo: SIM, e antes de deduzir.**
  Ele e a fonte da verdade sobre como o acervo funciona. Reimplementar a partir
  do que se leu la e legitimo -- e o mesmo criterio que ja valia para o
  `PALETTE_RECOLOR_GUIDE.md`.

> Por que isto virou decisao: a redacao antiga foi lida como "nao olhe o
> gerador", e o resultado foi **inventar tres vezes onde havia resposta pronta**:
>
> | inventado | ja existia no gerador |
> |---|---|
> | categoria pelo caminho | `type_name` no proprio definition |
> | selecao inicial do avatar | `selectDefaults()`, `sources/state/state.ts:159` |
> | caminho de arte literal | interpolacao de `${head}` |
>
> Cada um custou uma volta inteira de build. **Antes de deduzir comportamento do
> acervo, procurar no gerador.**

**2. Sem backend.** Mantem-se a decisao do projeto. O que muda em relacao ao
esboco inicial e que **os assets nao sao servidos como estao**: sao reempacotados
em build (decisao 3).

> Por que o esboco inicial nao servia: a Vercel aceita no maximo **15.000
> arquivos-fonte** por deploy via CLI e **100 MB** de estaticos no plano Hobby.
> 88.235 PNGs e 129,6 MB estouram os dois com folga. "Servir o repo inteiro" e
> "ter backend" nunca foram as duas unicas opcoes -- a terceira e curadoria em
> build.
>
> (Ate @3 esta linha citava 56.723 / 81,2 MB, a medicao truncada. O argumento so
> ficou mais forte com o numero certo.)

**2a. O acervo e servido do GitHub Pages, fora do deploy da Vercel.**
Adicionada em @10. O app continua um so e continua na Vercel; muda a ORIGEM
dos assets do avatar: `RAIZ` deixa de ser `/avatar/` e passa a ser a URL do
Pages deste repo, e `sincronizar-avatar.sh` sai do fluxo.

- O Pages ja esta publicado e provado byte a byte, com
  `Access-Control-Allow-Origin: *` em toda resposta
  (`docs/2026-08-02_acervo-no-github-pages.md`). O gerador oficial do LPC
  serve 129,6 MB assim.
- O teto passa de 100 MB (Hobby) para 1 GB (Pages) -- e o que permite as 4
  direcoes (3b3 @10) sem cortar animacao.
- Custo no app, medido e pequeno (TODO 146): `im.crossOrigin = "anonymous"`
  antes do `src` em `carregarImagem`, senao o `getImageData` do recolor
  estoura `SecurityError` cross-origin **e** a resposta chega opaca, que o
  `CacheFirst` se recusa a guardar -- o avatar nunca ficaria offline; o
  `urlPattern` do runtime cache vira funcao matcher por origem; a entrada
  `/^\/avatar\//` do `navigateFallbackDenylist` morre.
- A `RAIZ` carrega sufixo de versao (`?v=<versao do acervo>`): com
  `CacheFirst` de 90 dias, trocar o acervo sob a MESMA URL misturaria
  catalogo novo com atlas velho em cache parcial -- render errado em
  silencio, que e o que o principio zero proibe. Versao nova = chave de cache
  nova, invalidacao em bloco.
- **Nao existe instancia paralela do app.** A decisao 10 segue de pe: a
  validacao sem risco e o preview deployment da Vercel, e o rollback e o
  revert de um commit.

> **Medido ao aplicar (2026-08-02), e corrige a premissa do item 142:** o
> acervo NUNCA chegou ao deploy da Vercel. `app/public/avatar/` e gitignored e
> `sincronizar-avatar.sh` nunca esteve no `buildCommand` do `vercel.json` --
> so `sincronizar-base.sh` esta. Prova: `/avatar/catalogo.json` responde **404**
> em `waybuilder.vercel.app` e **200** no Pages. O teto de 100 MB, portanto,
> nunca chegou a apertar de fato: ele apertaria no dia em que o avatar fosse
> promovido a producao. A decisao acima nao muda -- ela deixa de ser migracao e
> passa a ser a escolha da origem antes da estreia, que e mais barato ainda.

**3. Um passo de build produz o acervo do app.** E o coracao desta spec. Ele:

  a. **normaliza os dois formatos** num so (o app nao conhece a migracao do
     upstream);
  b. **recorta as animacoes** para cinco: `idle`, `combat_idle`, `walk`, `sit`,
     `run`. As outras ~12 nao entram;
  b2. **recorta as variantes de corpo**: `skeleton` e `zombie` ficam **fora**.
     Entram os **seis** do gerador (`sources/state/constants.ts:9`): `male`,
     `female`, `teen`, `child`, `muscular`, `pregnant`.

     > **@9 -- `child` e `muscular` voltaram.** O corte original derrubava 18
     > definitions que so tinham arte de crianca: elas caiam em "sem arte" e
     > sumiam da tela. Medido no build: catalogo de **609 -> 627 itens**,
     > "sem arte no recorte" de **47 -> 29**, acervo de **23,8 -> 30,6 MB**
     > (+28%).
     >
     > Nem toda peca existe em todo corpo, e a diferenca e enorme: `male` tem
     > 582 das 627, `female` 588, `teen` 541, `muscular` 503, `pregnant` 517 e
     > **`child` so 98**. Por isso o picker passou a **nao oferecer** peca sem
     > arte no corpo atual -- e o que o gerador faz
     > (`components/tree/TreeNode.ts:163`, filtrando por `required`, que ele
     > deriva dos corpos declarados no `layer_1`). A peca **equipada** continua
     > listada e marcada: escondida, ela sumiria sem explicacao ao trocar de
     > corpo. Medido no gerador: `required_tags` e `excluded_tags` **nao**
     > participam da compatibilidade de corpo -- nao ha uma so referencia a
     > eles em `sources/`;
  b3. **recorta a direcao**: so a de **frente**. O LPC empilha 4 direcoes por
     folha, em linhas de 64px, na ordem `[costas, perfil-esq, FRENTE,
     perfil-dir]` -- **verificado visualmente** compondo `body` + `head` e
     olhando o resultado, nao suposto pela convencao. Sozinho, este corte tira
     75% do que sobrou. Consequencia aceita: **nao da para girar o boneco**.

     > **@9 -- girar o boneco foi pedido e esbarra no limite do deploy.**
     > Projecao medida numa amostra de 44 pecas de 8 slots, refazendo a tira
     > com as 4 linhas e recomprimindo do mesmo jeito que o build:
     >
     > | cenario | razao | atlas projetado |
     > |---|---|---|
     > | 1 direcao, 5 animacoes (hoje, 6 corpos) | 1,00x | **29,2 MB** |
     > | 4 direcoes, 5 animacoes | 4,04x | **118,0 MB** |
     > | 4 direcoes, sem `run` | 3,11x | 91,0 MB |
     > | 4 direcoes, sem `run` e sem `sit` | 2,68x | 78,4 MB |
     > | 4 direcoes, so `idle` + `walk` | 2,41x | 70,4 MB |
     >
     > O teto de **100 MB de estaticos no plano Hobby** foi reconferido na
     > fonte (https://vercel.com/docs/limits, "Static File uploads", pagina
     > atualizada em 2026-07-01): o numero da decisao 2 esta **correto**. Vale
     > para o upload de fontes via CLI -- deploy por Git nao sobe
     > `public/avatar/`, que e derivado do pacote.
     >
     > Como 118 MB passa do teto, **a escolha do aperto e do dono**, nao do
     > build (decisao 3 manda apertar o recorte e registrar o que saiu).
     > Enquanto nao houver decisao, o recorte segue em 1 direcao;
     >
     > **@10 -- decidido: as 4 direcoes entram, com as 5 animacoes.** Nenhum
     > aperto. O que tornava o aperto necessario era o teto de 100 MB da
     > Vercel, e a decisao 2a o removeu: os 118 MB projetados cabem no 1 GB do
     > Pages com folga de ~8,5x. O build passa a emitir as 4 linhas.
     > Pre-requisito: 2a aplicada no app primeiro (crossOrigin + matcher),
     > senao o recolor quebra. E os 118 MB sao **projecao de amostra de 44
     > pecas** -- o peso real sai do relatorio de (3h) quando o build rodar,
     > e e ele que entra no repo;
  c. **empacota em atlas por SLOT** -- um PNG por (slot, camada, corpo), em vez
     de milhares de arquivos soltos. Resolve o limite de arquivos da Vercel e o
     request storm da grade; com a UI de casas (5c), abrir um picker vira **um
     request**. Ate @5 a spec dizia "por categoria" e o build emitia **um PNG
     por peca** -- 2.800 arquivos. Cumprido em @6, com dois numeros medidos:
     custa **~28% de area** em padding (a peca mais larga do slot manda, e o
     padding transparente o PNG comprime a quase nada), e exige um **teto de
     16.384 px**, porque sem ele 12 grupos passariam de 19.072 px -- acima do
     limite de textura que os navegadores garantem, onde o canvas falha e as
     vezes sem erro;
  d. **emite o atlas de preview**: UM frame por peca (parado, de frente), por
     variante de corpo. Nao sao miniaturas prontas -- ver decisao 5b;
  e. **emite catalogo proprio** com IDs estaveis (decisao 6);
  f. **filtra pecas cuja unica licenca e GPL** (decisao 8);
  g. **emite os creditos** a partir do `CREDITS.csv` da raiz do repo, nao
     agregando os 768 blocos a mao;
  h. **registra o peso e a contagem medidos** num relatorio, como os portoes do
     pipeline ja fazem;
  i. **resolve `${head}` nas expressoes** (@7). 12 definitions tem caminho como
     `head/faces/${head}/neutral/`: a expressao **depende da cabeca equipada**,
     e a arte real vive em 3 pastas (`male`, `female`, `elderly`). O valor vem
     de `meta.replace_in_path.head`, tabela dentro do JSON da propria expressao,
     que mapeia **so 9 cabecas humanas**. Cabeca de lagarto, alien ou animal
     **nao tem expressao** -- no gerador o caminho fica literal e a camada
     simplesmente nao desenha (`state/path.ts:178-181`). **Nao ha fallback para
     `global`**: essa pasta serve so as 4 expressoes que a declaram direto, e
     essas o build ja emitia;
  j. **propaga `match_body_color`** (@7). 79 definitions tem a flag. Cabeca,
     nariz, orelha, rugas e expressao sao slots SEPARADOS com material `body`:
     sem ela, trocar o tom de pele deixa a cabeca de outra cor. O gerador forca
     a cor do corpo nesses itens em render (`state/palettes.ts:119-123`);
  k. **grava a paleta com as cores EXATAS** (@7). `convert("P", ADAPTIVE)` e
     median cut e e lossy mesmo abaixo de 256 cores: medido, o contorno do corpo
     virou `(39,24,32)` onde a fonte tem `#271920` -- justamente a primeira cor
     da rampa `light`. Com matching exato, o recolor de pele nunca repintaria o
     contorno.

**4. O NUCLEO cabe no precache; o acervo e runtime cache** (titulo reescrito em
@10 -- ate ali dizia "o acervo cabe no precache", que o codigo ja nao cumpria). Com o recorte de (3b), a estimativa e de
~4/17 do volume, antes do corte de cor. O numero real sai do build.

> Por que precache e nao carga sob demanda: `app/vite.config.ts` abre declarando
> *"Offline de verdade -- nao 'funciona com cache do navegador se der sorte'. O
> uso e mesa de jogo: pode nao ter rede, e o app tem de abrir."* Carga sob
> demanda daria grade vazia na primeira abertura sem rede, e silhueta quebrada
> numa ficha aberta em maquina que nunca compos aquele avatar.

~~Se o acervo recortado nao couber, a saida **nao** e runtime cache: e apertar o
recorte (menos variantes de corpo, menos animacoes) ate caber, e registrar o que
saiu.~~ **SUPERADO em @10** -- vale para o nucleo; para o acervo do avatar a
saida FOI runtime cache, por decisao do dono em 2026-08-01, e a 2a construiu em
cima disso. Fica como registro do que se decidiu antes.

> **@10 -- reconciliacao com o codigo.** A decisao do dono de 2026-08-01
> (registrada em `app/vite.config.ts`) ja tinha tirado o acervo do precache:
> ele e runtime cache `CacheFirst`, e a primeira composicao ja exigia rede.
> O "offline de verdade" vale para o NUCLEO do app; para o avatar a garantia e
> "depois da primeira visita, offline" -- e servir do Pages (2a) nao muda essa
> garantia, so o dominio da primeira visita. O paragrafo acima segue valendo
> para o nucleo, nao para o acervo.

**5. O renderer.** Para cada camada selecionada, ordenada por `zPos`, desenhar
no canvas. Ele precisa de tres coisas que o esboco inicial nao previa:

  - **recolor por paleta** (formato novo) alem de selecao de arquivo por cor
    (formato antigo) -- mas se (3a) normalizar bem, o app so ve um dos dois;
  - **camadas atras do corpo**: arma tem `behind/`, cabelo tem camada traseira;
  - **`layer_1..layer_N`**, cada uma com seu proprio `zPos`.

Nao e um loop de `drawImage` -- e um renderer pequeno. Orcar como tal.

**5c. A tela e um painel de casas, uma por slot.** Adicionada em @5.

Cada slot vira um **quadradinho** que mostra o que esta equipado ali; clicar
abre o picker daquele slot. A exclusividade fica visivel -- uma casa, uma peca
-- e os 41 slots de peca unica viram liga/desliga em vez de grade.

As casas se agrupam em **11 secoes** (`Corpo`, `Marcas`, `Cabeca`, `Rosto`,
`Cabelo`, `Chapeu`, `Torso`, `Pernas e pes`, `Armadura`, `Acessorios`,
`Armas`), por tabela curada no build (`GRUPO_DE_SLOT`). O grupo decide **so**
em que secao a casa aparece; **nunca** exclusividade, que e do slot.

> Por que curada e nao derivada do caminho: o caminho agrupa mal. `hair` vive
> em 10 diretorios -- o jogador equipa em `hair/short`, navega para
> `hair/braids` e a peca equipada nao aparece marcada em lugar nenhum, porque o
> estado e por slot e a navegacao seria por pasta. Slot novo no upstream cai em
> `Outros` com aviso; nunca some da tela.

O padrao ja existe no app: `app/src/componentes/Slot.tsx` faz casa -> modal com
busca, filtros e lista virtual, com botao de limpar. Muda a apresentacao do
gatilho (quadrado em vez de linha), nao a mecanica.

**5d. `combina_com` e `sem_arte`.** Dois metadados que a tela de casas exige:

- **`combina_com`** -- `hat_trim`, `hat_overlay`, `hat_accessory` e
  `hat_buckle` continuam **slots separados** (decisao do dono), mas o build
  pareia cada um ao chapeu de mesmo prefixo de nome: medido, **17 dos 21**
  casam ("Tricorne Captain Trim" -> "Tricorne Captain"), preferindo sempre o
  nome mais longo. O picker filtra pelo chapeu equipado, e trocar de chapeu
  avisa quando o acessorio fica orfao -- nunca troca em silencio.
- **`sem_arte`** -- as variantes de corpo em que a peca nao aparece. Medido:
  **92 pecas nao tem arte para `pregnant`**, 68 para `teen`, 27 para `male`, 21
  para `female`. Sem marcar, a celula da 5b mostra o personagem inalterado e o
  preview que "nunca mente" mente por omissao.

**5e. A ordem de desenho precisa de desempate.** Medido: **30 dos 64 valores de
`zPos` sao compartilhados por mais de um slot** (o `zPos` 115 tem 13). Ordenar
so por `zPos` deixa o resto por conta da ordem de insercao -- e no
`visualizador.html:132` isso significa que **a ordem em que o jogador clicou
decide o render**. Duas fichas com a mesma selecao desenham diferente.

O renderer ordena por `(zPos, slot, ordem_da_camada)`, e a fixture byte a byte
das Travas **tem de variar a ordem de insercao**, senao nunca pega a regressao.

> **Isto e escolha nossa, nao fidelidade ao gerador.** Ele ordena so por `zPos`,
> com sort estavel (`canvas/renderer.ts:397`) -- ou seja, empate resolve pela
> ordem em que o jogador equipou. Determinismo vale mais aqui do que espelhar o
> upstream, mas se algum dia a fixture comparar com o gerador, vai divergir nos
> empates. Registrado para nao virar susto.

**5b. A grade mostra a peca NO personagem, nao isolada.** Igual ao Stardew: o
jogador ve o proprio boneco mudando enquanto navega, nao um catalogo de pecas
soltas. Cada celula da grade e o **personagem atual inteiro**, com a peca
candidata no lugar da que ele usa hoje naquela categoria.

Consequencias, e todas sao a favor:

- **Nao existe miniatura pre-gerada.** Ela nao poderia existir: depende do corpo,
  da cor e das outras pecas equipadas naquele momento. O build emite o atlas de
  preview (3d); a composicao e em runtime.
- **A grade usa o MESMO renderer da decisao 5**, com um unico frame. Nao ha
  caminho de codigo separado para preview -- entao o preview nunca mente sobre o
  resultado, e `zPos` (cabelo atras da cabeca, arma atras do corpo) sai de graca.
- **O custo de abrir uma aba e um request**, nao 137: o atlas da categoria chega
  inteiro e a grade desenha recortes dele sobre o corpo atual.
- Trocar a variante de corpo ou a cor de pele **redesenha a grade**, e isso e o
  comportamento certo.

Virtualizacao da grade (desenhar so as celulas visiveis) e otimizacao, nao
requisito: 149 celulas e o maior caso.

**6. IDs proprios e estaveis.** O catalogo gerado em (3e) tem vocabulario
proprio; o documento de personagem **nunca** referencia caminho do upstream.

> O upstream acabou de reorganizar `sheet_definitions` em subdiretorios e esta
> migrando cores para paletas. Referenciar o caminho deles faria ficha salva
> quebrar em silencio na proxima atualizacao do snapshot.

O acervo e **pinado por commit**, e o pin vai no catalogo. ID orfao (peca que
sumiu entre snapshots) produz **avatar parcial mais aviso** -- nunca crash,
nunca silencio. E o mesmo padrao de `pin`/`nascida_em_pin` que `app/src/doc.ts`
ja aplica a base canonica.

**6b. O SLOT vem do `type_name`, nunca do caminho.** Adicionada em @4, depois de
um prototipo errado.

Duas coisas que o acervo trata como distintas, e que o build ate @3 confundia
numa so:

- **slot** -- o lugar do boneco que a peca ocupa. Peca com o mesmo `type_name`
  e **mutuamente exclusiva**: entra uma, sai a outra.
- **caminho** -- a hierarquia de navegacao (`head/heads/human`). Serve para a
  UI agrupar, e **nada mais**.

Medido no pin `0f898bb6`: **104 slots** distintos, e nenhuma peca sem
`type_name`. O build ate @3 usava `rel.split(os.sep)[0]` -- o primeiro segmento
do caminho -- e achatava os 104 em **10 categorias**, jogando o `type_name`
fora.

> Nao e imprecisao que da para remendar: **25 dos 104 slots aparecem em mais de
> um diretorio.** `hair` em 10, `hat` em 9, `weapon` em 7 -- e `weapon` aparece
> dentro de `tools/`. **Nao existe funcao do caminho que devolva o slot.**

O caso que o prototipo errou: `head` como slot sao **45 pecas em 6
diretorios** (`human`, `beast`, `fantasy`, `farm`, `reptile`, `undead`), todas
disputando um lugar so. Mas dentro do *caminho* `head/` moram **16 slots
independentes** -- `eyes`, `eyebrows`, `expression`, `nose`, `ears`, `neck`,
`necklace`, `charm`, `horns`, `fins`, `wrinkles` -- que coexistem sem conflito.
Tratar `head/` como escolha unica apaga quinze deles.

Entao o catalogo carrega, por peca: `slot` (do `type_name`), `caminho` (a
hierarquia inteira) e `prioridade` (o `priority` do `meta_*.json` do diretorio,
que o build ate @3 nem lia, porque pulava todo arquivo `meta_*`).

A regra de composicao que sai disso: **uma peca por slot, quantos slots
quiser.** Um chapeu completo, por exemplo, sao varias entradas coexistindo --
`hat` + `hat_trim` + `hat_overlay` + `hat_buckle` sao quatro slots, nao quatro
alternativas.

**7. O documento guarda a selecao, nunca a imagem.** Meia duzia de strings,
como o hash de URL do gerador (`body=...&hair=...`). O canvas recompoe.

- Vai no bloco **`manual`** (`specs/2026-07-26-schema-personagem.md:107`: *"o
  motor **nunca** escreve dentro de `manual`"*), **fora de `escolhas[]`**, que o
  motor varre.
- Migracao de esquema **@2 -> @3** pelo caminho existente (`versaoDeEsquema` /
  `migrar`, idempotente, ja usado no @1 -> @2).
- Ficha com avatar aberta em app antigo nao quebra nem perde o campo: o spread
  da gravacao preserva chave desconhecida por contrato (`doc.ts:660`).

> Guardar o PNG composto estouraria a cota do `localStorage` -- que ja aperta, a
> julgar pelo tratamento de `QuotaExceededError` em `doc.ts`. E violaria o
> principio 3 (guardar decisao, nao resultado).

**8. Licenca.** Atribuicao e obrigatoria e e **entrega**, nao observacao: uma
tela de creditos alimentada por (3g), no mesmo espirito do `Licenca.tsx` que ja
existe para OGL/ORC. Pecas cuja unica licenca e GPL sao **excluidas em build** --
a perda de acervo e minima e elimina a unica obrigacao incomoda. Exportar o
avatar como PNG embute os creditos.

**8b. O acervo recortado e VERSIONADO; a fonte nao.** Assimetria em relacao ao
pipeline da base, e o motivo e o deploy.

O `vercel.json` regenera o payload da base no build
(`python3 pipeline/emitir_app.py && ./sincronizar-base.sh && npm run build`), e
por isso `pipeline/base/app/*` pode ser gitignored. O avatar **nao pode seguir
esse padrao**: reconstruir o acervo exigiria clonar o LPC dentro do build da
Vercel, e o repo tem 1,57 GB.

Entao, na raiz deste repo:

- `fontes/` -- clone do LPC no pin. **Fora do git**, reconstruivel por
  `buscar_fonte.sh` (mesmo criterio de `pipeline/dados_brutos/` do waybuilder).
- `saida/` -- atlas, catalogo e creditos. **Versionado**, porque e o produto
  deste repo e nao ha como regera-lo em 45 segundos de build.

> E o mesmo raciocinio de `pipeline/dados_derivados/`, com outro motivo: la o
> que decide e "exigiu arbitragem humana"; aqui e "o custo de reconstruir nao
> cabe no build". A pergunta continua sendo a da wiki -- *existe comando que
> refaz isso sozinho?* --, e a resposta aqui e "existe, mas nao em 45 segundos
> de build".

Consequencia direta: **o peso do recorte e um numero que entra no repositorio
para sempre.** E a razao de o passo de build vir primeiro na ordem, e de (3h)
existir. Se o recorte ficar grande demais para versionar, a decisao a revisitar
e o recorte -- nao o versionamento.

**9. Sugestao, nao deducao.** Depois de tudo acima funcionando, o app pode
**sugerir** a selecao inicial: ancestralidade indica orelhas e tom de pele,
armadura equipada indica a camada de torso, arma indica a da mao. O jogador
sobrescreve sempre.

> Mapeia-se so o que da ganho -- as ~30 ancestralidades, as categorias de
> armadura, os grupos de arma --, nunca os 20 mil registros da base. Falha de
> mapeamento produz avatar generico, nao erro.
>
> **Limite conhecido:** o acervo LPC e humanoide-cetrico. Humano, elfo e anao
> tem correspondente; goblin, leshy, automaton e fetchling nao. A sugestao vai
> falhar para boa parte das ancestralidades do PF2e, e isso e aceitavel porque e
> sobrescrivel -- mas precisa estar dito antes, nao depois.

**10. Nao existe app separado -- mas o ACERVO e separado.** Sao duas coisas, e
so a segunda mudou em @3.

- **O acervo** (build, fontes, atlas, catalogo, creditos) vive neste repo,
  `waybuilder-avatar`. Ele ja era "um segundo artefato, com build proprio e
  vocabulario proprio" desde a v1; @3 so deu a ele o repo que isso implica.
- **O renderer e a UI** continuam dentro do waybuilder: rota de dev no proprio
  repo do app, mesmo build, mesmo versionamento. A promocao a modal e mover um
  componente.

> Prototipo de INTERFACE em projeto separado e modo de perda conhecido nesta
> casa -- foi assim que o HTML da home do nimbulus-web morreu num `/tmp`. Um
> acervo versionado com build proprio e pin nao corre esse risco: ele tem dono,
> historico e relatorio de peso. A fronteira que importa e "a tela mora junto do
> app", e ela segue de pe.

### 11. Animacao que falta e GERADA por transplante de peca analoga (@7)

**Decisao do dono, tomada olhando a arte, nao a metrica.**

170 dos 627 itens nao tem as animacoes novas -- 77% da armadura, 75% dos
acessorios. Sao pecas do formato legado do LPC. Tres caminhos foram medidos
antes desta decisao, e os relatorios estao em `docs/`:

| caminho | resultado |
|---|---|
| remapear frames identicos entre animacoes | **0** dos 170 recuperados |
| aprender a transformacao a partir do corpo | 67,9% por pixel, contra 99,57% que um frame exige |
| **transplante de peca analoga** | erro medio **-62%**; 9,1% dos frames exatos |

O transplante ganha de longe e ainda assim quase nao produz frame exato. O que
decidiu foi ver a figura (`docs/2026-08-02_doadora-analoga.png`): a peca gerada
sai **estruturalmente certa** -- volume, sombreamento e forma no lugar --, com o
defeito concentrado numa regiao (o saiote da armadura, os ombros da manga), nao
espalhado. Na Armadura Legionaria sao 29 px de 246. *"o erro n ta tipo escroto
inutilizavel, acho q da pra seguir assim mesmo"*.

**Como funciona.** Para a peca ALVO que nao tem a animacao X:

1. escolhe a DOADORA: a peca do mesmo slot com maior IoU de silhueta na
   animacao que as duas tem em comum;
2. mede na doadora, que tem as duas, para onde cada pixel foi ao mudar de pose
   -- busca do patch 5x5 mais parecido numa janela de mais ou menos 6 px;
3. aplica esse mesmo deslocamento a peca alvo.

Deterministico: mesma entrada, mesma saida. Nao ha modelo, nao ha peso, nao ha
aleatoriedade -- o build continua reproduzivel byte a byte, que e a trava 3.

**O que fica registrado.** A peca marca no catalogo qual animacao e gerada e de
qual doadora veio. Duas razoes: a tela poder dizer, e o dia em que o LPC
publicar a arte de verdade a substituicao ser um diff, nao uma arqueologia.

**Licenca: fora de escopo por decisao do dono** -- *"ignora o licenciamento
cara, n vou vender"*. O uso e pessoal e nao-comercial, como a nota da v6 ja
registra, e os creditos seguem emitidos com todos os autores e licencas do
acervo. Fica anotado que a peca gerada deriva de DUAS pecas, e que restringir a
doadora a licenca compativel seria barato (`build.py:475` ja extrai o conjunto)
caso o uso mude.

**O que isto NAO e.** Nao e "as animacoes que faltavam agora existem". E arte
aproximada, com defeito medido e assumido, ocupando o lugar de arte que nao
existe. O fallback estatico da decisao 12 continua valendo para o que o
transplante nao cobrir.

### 11b. O transplante sai da frente do `idle`: roteador por RIGIDEZ (@11)

A decisao 11 mandava gerar toda animacao que falta por transplante de peca
analoga. Uma pesquisa de dez frentes com passe adversarial
(`docs/2026-08-02_PESQUISA-transplante.md`) mediu que existe caminho melhor
para o `idle` -- e, mais importante, mediu **onde ele nao vale**.

**O achado.** `idle` k=1 e quase sempre `walk` k=0 deslocado alguns pixels.
Onde existe um (dy, dx) exato -- 78,7% do acervo -- a translacao acerta
**98,5%** dos frames e a doadora nem e consultada. Nos outros 21,3% ela acerta
**0,0%**, e ali e PIOR que o transplante: mediana de 88 pixels errados contra
51, com 80,2% dos fracassos acima de um quarto da area da peca.

Por isso a escolha nao e por slot, e por **rigidez**, e a terceira saida --
**nao mexer** -- e resposta legitima: em 61 das 76 pecas legadas medidas foi a
decisao certa.

| regra | valor | origem |
|---|---|---|
| pecas de referencia minimas no slot | **2** | desempate dentro de empate medido |
| concordancia minima no (dy, dx) | **0,70** | desempate dentro de empate medido |

**Referencia e peca COMPLETA** -- a que tem todas as animacoes do recorte. Ter
`walk` e `idle` nao basta, e a definicao nao e detalhe: e ela que sustenta os
numeros desta tabela. A calibracao mediu zero regressao justamente porque
restringiu o treino assim, e atribuiu as 13 regressoes da medicao anterior ao
treino contaminado por pecas legadas -- inclusive o caso `hat/tiara`, arte que
estava EXATA e foi destruida pela moda do slot. `roteador.eh_referencia` guarda
a regra, e `testes/test_roteador.py` trava.

> **Os limiares que a propria pesquisa recomendou eram chute, e perderam.** Ela
> propos (3 pecas, 80%) declarando que nao os havia medido. A varredura por
> leave-one-out das 48 combinacoes
> (`docs/2026-08-02_calibracao-do-roteador.md`) mostrou o chute
> **estritamente dominado**: 10,5% de frames exatos contra 14,5%, com as mesmas
> zero regressoes. Nao havia trade-off -- era so mais conservador sem comprar
> nada.
>
> **O que a varredura mediu foi o que PERDE, nao um vencedor unico.** O par
> adotado esta num empate de **6 combinacoes** com resultado identico, de
> (1; 0,50) a (2; 0,70). Escolher `n_min = 2` dentro do empate e preferencia de
> robustez -- nao deixar uma unica peca decidir o slot inteiro --, e a propria
> calibracao a rotula como opiniao. Registrado para que uma recalibracao futura
> que devolva (1; 0,50) nao pareca contradizer esta spec. `test_roteador.py`
> trava os dois numeros contra volta ao chute, nao contra o empate.

**O tamanho honesto da entrega.** Nas 76 pecas legadas medidas o roteador
aplica translacao em 15: **9 melhoram, 6 ficam iguais, 0 pioram**. As outras 61
nao sao tocadas. O numero de manchete da pesquisa -- 77,6% de frames exatos --
e das pecas que **ja tem** a arte; em alvo legado real cai para ~14%, e a tabela
por slot so cobre 28,2% das lacunas. `shield_pattern`, `weapon` e `charm` nao
tem peca de referencia nenhuma.

**O que o roteador NAO cobre**, e cada excecao continua na decisao 11:

- `combat_idle` e `run`: os 68,0% e 59,3% que a pesquisa mostra para eles
  vieram de reaplicacao aproximada da tabela de `idle`, **sem leave-one-out
  proprio**. Migra-los agora seria repetir o erro do parametro chutado.
- **Peca sem `walk`** (135 celulas na contagem canonica): `walk` k=0 e a base
  da copia e da translacao. Sem ela nao ha do que partir, e o transplante
  segue sendo a unica saida.

**Arte duplicada sai do treino.** 13 grupos de pecas byte a byte identicas sob
ids diferentes (`hat/bascinet` = `hat/round-bascinet`, `head/wolf-female` =
`head/wolf-male`) inflavam qualquer medicao em ate 5 pontos percentuais sem
ensinar nada. A deduplicacao e por conteudo, em tempo de build, para sobreviver
a troca de pin.

### 11c. `sit` nao e gerado, e `idle` k=0 e copia (@11)

Fecha o item 145 -- o veredito por animacao, com numero.

| animacao | veredito | medido |
|---|---|---|
| `idle` k=0 | **copia de `walk` k=0** | identicos byte a byte em 88,4% de 493 pecas |
| `idle` k=1 | **roteador por rigidez** (11b) | 9 melhoram, 6 iguais, 0 pioram em 15 aplicadas |
| `combat_idle` | transplante, como esta | falta LOO proprio |
| `run` | transplante, como esta | falta LOO proprio; e o IoU e cego ali (correlacao -0,001) |
| `sit` | **nunca gerar** | 0,0% de exatos em duas amostras (n=349 e n=366) |

`sit` produz ruido, nao arte aproximada: mediana de 118-123 pixels errados e
96,2% das pecas com mais de um quarto da area errada. Os **3,6%** de "exatos"
que a H2 mediu eram **artefato**: 13 dos 13 frames exatos eram quadros VAZIOS
contando como acerto, em pecas cuja `camadas[0]` e vazia (chifres, asas,
caudas, escudo). Corrigido, cai a 0,0%. A peca cai no fallback parado da
decisao 12, que e honesto.

> Os **0,5%** que aparecem na tabela de hipoteses para `sit` sao outro numero
> -- o baseline de transplante da amostra da H1 (n=374), que nunca foi
> decomposto. Os dois nao devem ser confundidos: a prova dos quadros vazios foi
> feita sobre o 3,6%.

**Os vereditos acima valem para a direcao de FRENTE.** Tudo em 11b e 11c foi
medido no recorte frontal, que era o unico que existia quando a pesquisa rodou.
A decisao 3b3 @10 acabou de ligar as **4 direcoes**: a superficie de arte
gerada quadruplica e o erro em perfil e de costas nao foi medido. Antes de
estender o roteador ou o transplante as linhas novas, revalidar **por
direcao** -- gatilho fixado pelo proprio parecer que ligou as 4 direcoes.

**Corte por regiao em `combat_idle` e `run`: medido, NAO adotado.** A H2 mediu
0,0% de exatos nas 4 celulas em que a peca tem pixel em pernas ou pes nessas
animacoes (mediana 10-38 px, fracao de area errada de 37,5% a 90,2%), e o passe
adversarial preservou a conclusao. Nao esta implementado: exige o mapa de
regiao por peca, que hoje so existe como artefato de pesquisa
(`docs/2026-08-02_mapa-de-movimento.json`). Fica registrado como divida com
numero, nao como esquecimento.

**Nao existe nota de confianca automatica, e nao vai existir tao cedo.** A
pesquisa tentou construir um preditor de qualidade sem gabarito -- o que
permitiria reprovar automaticamente a peca mal gerada, ja que nas lacunas reais
nao ha original para comparar. Ele **falhou**, e o motivo importa mais que o
resultado: precisao de 50,5% no quartil pior, contra o criterio de 70% fixado
antes. E o criterio era inalcançavel por construcao -- com so 17,6% das pecas
errando sob translacao, o desenho do teste (sinalizar 25%) capa qualquer
classificador em **69,7%**, abaixo do proprio criterio. O relatorio esta em
`docs/2026-08-02_pesquisa-h5-preditor-de-qualidade.md`.

> Isso nao deixa o acervo desprotegido, porque **o roteador ja e o gate**: ele
> so translada onde o treino do slot concorda, e nas 76 pecas medidas isso deu
> zero regressoes. A protecao vem de nao gerar, nao de gerar e filtrar. O preco
> esta declarado: ~77% das lacunas ficam sem arte gerada, esperando arte de
> verdade ou revisao humana.

> **Ressalva que vale para as duas decisoes acima:** os 88,4% e a regra de
> rigidez foram medidos em pecas COMPLETAS. O passe adversarial mostrou que as
> legadas sao outra populacao -- 55,3% rigidas contra 83,5%, area mediana de
> 101 px contra 209,5, e 25,8% delas com mais de 6 tons contra 18,3%. Os
> numeros **nao transferem**; o que sustenta a decisao e que nenhuma das 76
> legadas medidas piorou.

### 12. Peca sem a animacao aparece PARADA, nao some (@7)

O gerador omite a camada naquela linha (`canvas/renderer.ts:343`) e nos
copiavamos: a peca desaparecia ao ser equipada, sem dizer nada. Agora ela cai no
primeiro frame de uma animacao que tenha e trava ali, com aviso
`animacao-substituida` para a tela explicar.

Nunca roda a tira alheia em movimento -- o risco que o gerador evitava segue
evitado. A substituta vem da ordem do RECORTE, nao da ordem em que o build
gravou: duas fichas iguais tem de desenhar igual.

## Resultado do passo 1, medido (2026-08-01)

`avatar/build.py` rodou contra o pin `0f898bb6`:

| artefato | arquivos | MB |
|---|---|---|
| atlas | 469 | 8,29 |
| catalogo.json | 1 | 0,88 |
| paletas | 10 | 0,03 |
| **total** | **494** | **9,16** |

> Numeros de @6, com o atlas consolidado por slot: **2.800 arquivos viraram
> 469** ao custo de **+1,95 MB** (27%) em padding. Para um PWA que so ativa o
> service worker quando TODO o precache baixa, trocar 2.331 requests por 2 MB e
> o lado certo. O maior atlas ficou em 16.256 px -- o teto de 16.384 pegou por
> pouco em `charm`.
>
> Numeros de @4, depois da correcao de slot. Ate @3 a tabela dizia 2.811
> arquivos e 7,05 MB -- e o atlas tinha **2.788 PNGs em disco contra 2.800
> gravados**. Os 12 que faltavam eram pecas homonimas de slots diferentes
> escrevendo no mesmo caminho, uma por cima da outra. Com o id vindo do slot,
> disco e relatorio batem.

O atlas guarda **uma cor por faixa de 64px**: um arquivo por (peca, camada,
corpo), com `x` deslocando a animacao e `y` deslocando a cor. Antes de
consolidar eram 10.142 arquivos e 8,88 MB.

> Medido: 25 cores como arquivos separados custam 15.212 B; num atlas unico,
> 12.151 B. Sao ~128 B de cabecalho por PNG, e com 10 mil arquivos isso vira
> 1,4 MB -- alem de 10 mil entradas no git e 25 requests para ciclar as cores de
> uma peca em vez de um. O catalogo encolheu junto (1,87 -> 0,85 MB) porque as
> animacoes subiram de nivel: deixaram de repetir por cor.
>
> **Enxugar o catalogo por si so foi avaliado e descartado:** ele comprime de
> 1,87 MB para **62 KB** em gzip, que e o que de fato trafega. O ganho aparente
> era ilusao de comparar bytes crus com bytes ja comprimidos.

**609 itens** no catalogo, de 656 definitions de peca (os outros 112 dos 768 sao
`meta_*.json` -- metadados de categoria, nao peca).

Validado visualmente: um personagem composto do catalogo sai de frente, com as
tiras alinhadas e `zPos` na ordem certa -- inclusive arma com camada atras
(`z=9`) e na frente (`z=140`) do corpo.

**Nenhuma peca foi excluida por licenca GPL-only.** O filtro da decisao 8 existe
e nao cortou nada neste pin.

### Divida declarada: 28 pecas de layout nao-universal

47 definitions ficaram sem arte no recorte. **19 sao `child`/`muscular`**,
cortadas de proposito. As outras **28 declaram variantes que mantemos** e mesmo
assim nao entraram -- entre elas **13 armas** (`Whip`, `Club`, `Dragon spear`) e
25 pecas de `head`.

Causa medida: elas nao seguem o layout universal.

```
weapon/polearm/dragonspear/foreground/walk/brass.png   <- animacao no MEIO do path
weapon/blunt/club/background/club.png                  <- outro arranjo ainda
tools/whip/bg                                          <- diretorio nem existe
```

E os JSONs declaram animacoes proprias (`walk_128`, `thrust_oversize`,
`slash_reverse_oversize`, `tool_whip`) em vez do conjunto universal.

Cobertura atual: **609 de 637 pecas elegiveis (95,6%)**.

> **A divida real e de 10 pecas, nao 28** -- corrigido em @7, lendo o gerador.
> As 47 sem arte se repartem assim: **19** sao `child`-only (cortadas de
> proposito), **12** sao as expressoes com `${head}` (decisao 3i), **14** usam
> `custom_animation` e **2** estao corretas fora.
>
> Das 14 custom, **so 10 seriam visiveis no nosso recorte**: as 9 de `walk_128`
> (dragonspear, longspear, trident, katana, scimitar, longsword alt e 3 arcos) e
> o `wheelchair`, de base `sit`. As outras 4 -- club, whip, boomerang, tool rod
> -- tem base `slash`/`thrust`, animacoes que a decisao 3b ja cortou:
> **recupera-las adiciona zero pixel visivel**, porque o proprio gerador so as
> desenha naquelas linhas.
>
> Recuperar as 10 exige recortar a linha `s` (indice 2) de celulas de **128 px**
> e desenhar com offset `-32,-32` sobre o frame de 64 -- o inverso do
> centramento que o gerador faz em `canvas/draw-frames.ts:32-46`. Precisa de
> canvas com sangria, senao a lamina corta.

## Ordem

1. Passo de build (decisao 3) com o relatorio de (3h). **Sem ele nao ha numero
   para decidir o resto.**
2. Renderer (decisao 5) como modulo puro, testavel sem UI.
3. Rota de dev com a grade e as setinhas, todas as opcoes do catalogo.
4. Campo no documento e migracao @2 -> @3 (decisao 7).
5. Promocao a modal.
6. Creditos (decisao 8).
7. Sugestao por ancestralidade e equipamento (decisao 9) -- opcional, depois.

## Travas

- Teste do renderer contra um conjunto de selecoes fixas, comparando o canvas
  resultante byte a byte (o mesmo padrao das 33 fixtures do motor).
- Teste de que ID orfao produz avatar parcial e aviso, nunca excecao.
- Teste de que `manual` sobrevive a um ciclo salvar/abrir/exportar/importar com
  o campo de avatar preenchido -- a garantia de que `manual` nunca e sobrescrito
  **nao tem teste hoje**, e esta spec e a primeira a depender dela.
- O relatorio de (3h) entra no repo e o peso e comparado build a build.

## Decidido em 2026-08-01

As tres perguntas que este rascunho abriu foram respondidas pelo Igor e viraram
as decisoes 3b, 3b2 e 5b:

- **`idle` entra** -- cinco animacoes no recorte.
- **`pregnant` e `teen` entram**; `child` e `muscular` ficam fora.
- **A grade mostra a peca no corpo atual**, no esquema do Stardew: monta-se no
  proprio personagem. Isso eliminou o passo de miniaturas pre-geradas.

## Aberto

1. `skeleton` e `zombie` sao diretorios de CORPO sem peca de roupa mapeada. Nao
   entram no recorte. Vale saber se interessam algum dia -- o PF2e tem
   ancestralidade morta-viva, e o custo de inclui-los depois e refazer o build,
   nao remodelar nada.

2. **FECHADO em @10: a ponte nao e nenhuma das tres opcoes da tabela.** O
   acervo nao entra no build do app; o app o consome em RUNTIME do GitHub
   Pages (decisao 2a). `saida/` segue versionada (8b intacta) e o pin segue no
   catalogo (6 intacta). O texto original fica abaixo, como registro do que se
   considerou.

   **A ponte entre os dois repos, em aberto por decisao (@3).** Com o acervo
   fora do waybuilder, o build da Vercel de la nao enxerga mais `saida/`. Isso
   **nao bloqueia nada hoje** -- o app nao consome o acervo, nao ha import nem
   linha no `vercel.json`. A ponte se decide no passo 2 da ordem, quando o
   renderer existir e houver o que servir. As opcoes levantadas na separacao:

   | opcao | custo | observacao |
   |---|---|---|
   | git submodule no pin | atrito em todo clone (`--recurse-submodules`) | Vercel faz checkout em repo publico; ambos sao publicos |
   | pacote npm do GitHub | `npm install` ja roda no build | versiona o acervo por tag, o mais limpo a longo prazo |
   | fetch do raw/release no build | zero atrito de clone | rede no build, e o que a decisao 4 mais quer evitar |

   O que **nao** e opcao: voltar a reconstruir o acervo dentro do build da
   Vercel. A decisao 8b nasceu justamente disso -- clonar 1,57 GB nao cabe.
