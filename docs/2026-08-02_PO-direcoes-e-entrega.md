# Parecer do PO -- direcoes do boneco e entrega do acervo (itens 140, 142, 146)

Papel delegado pelo dono em 2026-08-02. As duas decisoes abaixo sao finais,
salvo os gatilhos de recuo da secao 5.

## 1. A decisao

- **Item 140: as 4 direcoes entram, com as 5 animacoes. Nenhum aperto.**
  Nada sai do build; o jogador nao perde nada na tela e ganha o giro.
- **Item 142: o acervo sai do deploy da Vercel e e servido do GitHub Pages**
  (`igoresramos.github.io/waybuilder-avatar/saida/`), que ja esta publicado e
  provado.
- **Instancia paralela do app: NAO.** E medo caro. A mudanca entra no app
  unico, num commit atomico validado em preview deployment da Vercel.

## 2. Por que

**As duas decisoes sao uma so.** O unico motivo para apertar animacao era o
teto de 100 MB de estaticos do Hobby da Vercel (118 MB projetados > 100 MB).
Tirando o acervo do deploy, o teto vira o do Pages: **1 GB** -- os 118 MB cabem
com folga de **~8,5x**, e o gerador oficial do LPC serve **129,6 MB** de la
hoje, funcionando. Escolher um aperto (sem `run` = 91 MB, sem `run`+`sit` =
78 MB) seria pagar em conteudo um limite que da para simplesmente remover.

**O custo do Pages ja esta medido, e e pequeno.** Dos 5 passos do item 142, os
passos 1, 2 e 4 estao FEITOS e provados (`docs/2026-08-02_acervo-no-github-pages.md`):
CORS `Access-Control-Allow-Origin: *` medido em toda resposta, conteudo byte a
byte contra o local, `.nojekyll` no lugar. O que falta no app sao tres mudancas
pontuais, todas ja escritas no item 146: `im.crossOrigin = "anonymous"` antes
do `src` em `carregarImagem` (`Avatar.tsx:104` -- sem isso o `getImageData` do
recolor em `Avatar.tsx:222` estoura `SecurityError` em toda peca com cor), o
`urlPattern` do service worker virando funcao matcher por origem
(`vite.config.ts:53`) e a entrada morta `/^\/avatar\//` do
`navigateFallbackDenylist` (`vite.config.ts:37`).

**O argumento "offline de verdade" contra o Pages ja caiu -- por decisao do
proprio dono.** `vite.config.ts:44-52` registra: em 2026-08-01 o acervo do
avatar saiu do precache ("pode colocar todas as cores, e so nao dar preload").
A primeira composicao do avatar **ja exige rede hoje**, mesmo same-origin.
Servir de outro dominio nao rebaixa garantia nenhuma -- so muda de quem e a
rede da primeira vez. A decisao 4 da spec e que ficou defasada do codigo; o
adendo abaixo conserta.

**A instancia paralela nao se justifica.** O que ela compraria -- testar sem
arriscar producao -- a Vercel ja da de graca em todo preview deployment. O que
ela custaria e conhecido nesta casa: dois service workers, dois caches, drift
de codigo, e mais uma copia paralela do mesmo trabalho (o item 119 ja pagou o
preco de tres listas descrevendo a mesma coisa). A mudanca e uma constante
(`RAIZ`) mais duas linhas de config: o rollback e `git revert` de um commit. O
risco que a segunda instancia mitigaria nao existe em tamanho que pague dois
apps.

## 3. O que muda na spec (adendo @10, pronto para colar)

**Frontmatter** -- adicionar a lista `revisao` e subir `version` para 8:

```
@10 (2026-08-02) -- decisao delegada ao PO: as 4 direcoes entram com as 5
  animacoes, e o acervo passa a ser servido do GitHub Pages (decisao 2a
  nova). O teto de 100 MB deixa de reger o recorte; o item 2 de "Aberto"
  fecha como consumo em runtime; a decisao 4 e reconciliada com o codigo
```

**Nova decisao 2a**, entre as decisoes 2 e 3:

```
**2a. O acervo e servido do GitHub Pages, fora do deploy da Vercel.**
Adicionada em @10. O app continua um so e continua na Vercel; muda a ORIGEM
dos assets do avatar: `RAIZ` deixa de ser `/avatar/` e passa a ser a URL do
Pages deste repo, e `sincronizar-avatar.sh` sai do build.

- O Pages ja esta publicado e provado byte a byte, com
  `Access-Control-Allow-Origin: *` em toda resposta
  (`docs/2026-08-02_acervo-no-github-pages.md`). O gerador oficial do LPC
  serve 129,6 MB assim.
- O teto passa de 100 MB (Hobby) para 1 GB (Pages) -- e o que permite as 4
  direcoes (3b3 @10) sem cortar animacao.
- Custo no app, medido e pequeno (TODO 146): `im.crossOrigin = "anonymous"`
  antes do `src` em `carregarImagem`, senao o `getImageData` do recolor
  estoura `SecurityError` cross-origin; o `urlPattern` do runtime cache vira
  funcao matcher por origem + prefixo do path; a entrada `/^\/avatar\//` do
  `navigateFallbackDenylist` morre.
- A `RAIZ` carrega sufixo de versao (`?v=<pin>`): com `CacheFirst` de 90
  dias, trocar o acervo sob a MESMA URL poderia misturar catalogo velho com
  atlas novo em cache parcial -- render errado em silencio, que e o que o
  principio zero proibe. Versao nova = chave de cache nova, invalidacao em
  bloco.
- **Nao existe instancia paralela do app.** A decisao 10 segue de pe: a
  validacao sem risco e o preview deployment da Vercel, e o rollback e o
  revert de um commit.
```

**Na decisao 3b3**, apos o bloco @9:

```
> **@10 -- decidido: as 4 direcoes entram, com as 5 animacoes.** Nenhum
> aperto. O que tornava o aperto necessario era o teto de 100 MB da Vercel,
> e a decisao 2a o removeu: os 118 MB projetados cabem no 1 GB do Pages com
> folga de ~8,5x. O build passa a emitir as 4 linhas. Pre-requisito: 2a
> aplicada no app primeiro (crossOrigin + matcher), senao o recolor quebra.
```

**Na decisao 4**, apos o bloco de citacao existente:

```
> **@10 -- reconciliacao com o codigo.** A decisao do dono de 2026-08-01
> (registrada em `app/vite.config.ts:44-52`) ja tinha tirado o acervo do
> precache: ele e runtime cache `CacheFirst`, e a primeira composicao ja
> exigia rede. O "offline de verdade" vale para o nucleo do app; para o
> avatar a garantia e "depois da primeira visita, offline" -- e servir do
> Pages (2a) nao muda essa garantia, so o dominio da primeira visita.
```

**No item 2 de "Aberto"**: marcar fechado --

```
2. FECHADO em @10: a ponte nao e nenhuma das tres opcoes da tabela. O
   acervo nao entra no build do app; o app o consome em RUNTIME do GitHub
   Pages (decisao 2a). `saida/` segue versionada (8b intacta); o pin segue
   no catalogo (6 intacta).
```

## 4. Ordem de execucao

**146 -> 142(passo 3) -> 140.** O 146 e pre-requisito declarado do 142; o 142
e pre-requisito do 140 (ligar 4 direcoes antes de remover o teto estoura o
deploy).

1. **Item 146a -- `crossOrigin` em `carregarImagem`.** Pode entrar ja, isolado:
   e no-op same-origin, risco zero.
2. **Item 146b + 142 passo 3, num commit UNICO no app:** trocar `RAIZ` pra URL
   do Pages com `?v=<pin>`, trocar o `urlPattern` por funcao matcher, remover a
   denylist morta, tirar `sincronizar-avatar.sh` do build. Nao separar: o
   matcher por origem do Pages, sozinho, deixaria o `/avatar/` atual sem cache.
   Validar no preview deployment ANTES de promover: recolor funciona (sem
   `SecurityError`), cache `avatar` popula, avatar abre offline na segunda
   visita. Prova, nao suposicao.
3. **Item 140 -- o build emite as 4 linhas** (29,2 -> ~118 MB), `saida/`
   versionada, push, bump do `?v=`. Ligar o giro na UI.

## 5. O risco que aceitei e o gatilho de recuo

- **Dependencia de runtime do github.io** na primeira visita e apos expiracao
  (90 dias). Aceito porque a dependencia de rede ja existia e os limites do
  Pages sao soft (100 GB/mes) contra uso de app pessoal. **Gatilho:** 429 ou
  indisponibilidade observada de verdade -> recuo barato: 1 direcao volta a
  caber na Vercel (29,2 MB) com um revert.
- **~118 MB versionados no repo, crescendo a cada rebuild** (blobs novos no
  historico). **Gatilho:** repo se aproximando do 1 GB recomendado pelo GitHub
  -> mover atlas pra release assets ou limpar historico.
- **118 MB e projecao de amostra (44 pecas), nao medicao do build.** Aceito
  porque ate um erro de 2x cabe no Pages. **Gatilho:** nenhum realista.
- **As metricas do transplante (143/144/145) foram medidas so de frente.** Com
  4 direcoes a superficie de arte gerada quadruplica e o erro de perfil/costas
  nao foi medido. **Gatilho:** o veredito do item 145 passa a valer POR
  DIRECAO, nao por animacao agregada.

Conferido de passagem: `maxEntries: 600` do cache aguenta -- 4 direcoes deixam
os atlas mais altos, nao mais numerosos (~480 arquivos, inalterado).

## 6. O que NAO decidi, e por que

- **Item 145** (se `sit`/`run` entram no TRANSPLANTE -- `sit` deu 0,0% de
  frames exatos): aguarda o ataque das hipoteses do item 143/144. Decidir
  agora seria decidir sem o passe adversarial que o proprio item exige. Se o
  145 cortar as geradas, o acervo so encolhe -- nao conflita com este parecer.
- **Item 141** (fallback `walk` para as 102 pecas sem `idle`): prioridade
  baixa, ortogonal a estas duas.
- **`skeleton`/`zombie`** (Aberto 1): segue aberto; o custo de incluir depois
  continua sendo so refazer o build.
- **Formato exato do sufixo de versao** (`?v=` vs segmento de path): decisao
  de implementacao do passo 2; o requisito de produto e so um -- acervo novo
  nunca mistura com cache velho em silencio.
