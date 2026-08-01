---
spec: avatar-do-personagem
project: waybuilder
version: 6
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

**1. Nao copiar codigo do gerador.** GPL-3.0 contaminaria o Waybuilder, e o app
deles e Mithril contra o React daqui. A composicao e escrita do zero. Reimplementar
o recolor a partir do `PALETTE_RECOLOR_GUIDE.md` e legitimo: e documentacao, nao
codigo.

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

**3. Um passo de build produz o acervo do app.** E o coracao desta spec. Ele:

  a. **normaliza os dois formatos** num so (o app nao conhece a migracao do
     upstream);
  b. **recorta as animacoes** para cinco: `idle`, `combat_idle`, `walk`, `sit`,
     `run`. As outras ~12 nao entram;
  b2. **recorta as variantes de corpo**: `child` e `muscular` ficam **fora**.
     Entram `male`, `female`, `pregnant` e `teen`;
  b3. **recorta a direcao**: so a de **frente**. O LPC empilha 4 direcoes por
     folha, em linhas de 64px, na ordem `[costas, perfil-esq, FRENTE,
     perfil-dir]` -- **verificado visualmente** compondo `body` + `head` e
     olhando o resultado, nao suposto pela convencao. Sozinho, este corte tira
     75% do que sobrou. Consequencia aceita: **nao da para girar o boneco**;
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
     pipeline ja fazem.

**4. O acervo cabe no precache.** Com o recorte de (3b), a estimativa e de
~4/17 do volume, antes do corte de cor. O numero real sai do build.

> Por que precache e nao carga sob demanda: `app/vite.config.ts` abre declarando
> *"Offline de verdade -- nao 'funciona com cache do navegador se der sorte'. O
> uso e mesa de jogo: pode nao ter rede, e o app tem de abrir."* Carga sob
> demanda daria grade vazia na primeira abertura sem rede, e silhueta quebrada
> numa ficha aberta em maquina que nunca compos aquele avatar.

Se o acervo recortado nao couber, a saida **nao** e runtime cache: e apertar o
recorte (menos variantes de corpo, menos animacoes) ate caber, e registrar o que
saiu.

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

Cobertura atual: **609 de 637 pecas elegiveis (95,6%)**. Recuperar as 28 exige
tratar o caso "o `dirbase` ja termina numa animacao" e os layouts `fg`/`bg`
avulsos. Fica registrado como divida, nao como bug -- e o proximo item da lista
se a mesa sentir falta de alguma arma.

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

2. **A ponte entre os dois repos, em aberto por decisao (@3).** Com o acervo
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
