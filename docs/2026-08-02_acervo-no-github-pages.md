# Acervo no GitHub Pages -- passos 1, 2 e 4 do item 142

Escopo: TODO item 142 (`Tartarus/Projetos/pessoal/waybuilder/TODO.md`), passos 1
(regras do Pages), 2 (publicar) e 4 (CORS + cache). Passos 3 (trocar `RAIZ` no
Avatar.tsx e tirar `sincronizar-avatar.sh` do build) e 5 (ligar as 4 direcoes)
ficam com o dono do repo `waybuilder`, fora do escopo deste trabalho -- este
repo (`waybuilder-avatar`) foi o unico tocado.

## 1. Regras reais do GitHub Pages

Fonte oficial: <https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits>.

| limite | valor | observacao |
|---|---|---|
| tamanho do repositorio fonte | 1 GB (recomendado) | nao e hard block, e recomendacao |
| tamanho do site publicado | 1 GB (maximo) | |
| timeout de build | 10 minutos | so relevante pra `build_type: workflow`; nao se aplica ao `legacy` (deploy direto da branch) usado aqui |
| banda mensal | 100 GB/mes | **soft limit** |
| builds por hora | 10/hora | **soft limit**; nao vale se o build for por GitHub Actions custom |

Texto literal sobre enforcement: *"If your site exceeds these usage quotas, we
may not be able to serve your site, or you may receive a polite email from
GitHub Support suggesting strategies for reducing your site's impact on our
servers."* Rate-limit especifico devolve HTTP 429.

CORS: a documentacao de limites nao fala de CORS explicitamente. Confirmado por
medicao (abaixo) que o Pages manda `Access-Control-Allow-Origin: *` em
**qualquer** resposta, inclusive 404 -- e comportamento de infraestrutura do
Pages (Fastly/Varnish na frente), nao configuravel por repo.

### O gerador oficial do LPC, na pratica

Repo: `LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator`.
`gh api repos/.../pages` mostra `build_type: "workflow"`, fonte `master` / `/`.
O workflow (`.github/workflows/deploy.yml`) roda `npm run build` (Vite) e sobe
`./dist` via `actions/upload-pages-artifact`. O `vite.config.js` usa um plugin
(`get-spritesheets-plugin.js`) que faz `rsync -a spritesheets dist/` -- ou seja,
a pasta `spritesheets/` inteira do repo vira `dist/spritesheets` e e servida
como esta.

Medi o tamanho real com `git clone --filter=blob:none` + `du -sb` (byte
aparente, nao bloco de disco -- `du -sh` sem `-b` inflou pra 392 MB neste
ambiente por causa do overhead de bloco em ~88 mil arquivos pequenos, um
artefato do filesystem, nao do conteudo real):

```
du -sb spritesheets  ->  129.580.422 bytes = 129,58 MB
```

Isso bate com o numero ja citado no item 142 do TODO ("129,6 MB"). Confirmado
por medicao direta, nao repetido de cabeca.

CORS medido num asset real publicado:

```
curl -sI https://liberatedpixelcup.github.io/.../spritesheets/body/bodies/teen/combat_idle.png
HTTP/2 200
content-type: image/png
access-control-allow-origin: *
```

## 2. Publicacao do `waybuilder-avatar` no Pages

### Medicao antes de publicar

O que fica versionado no repo (`git ls-files` + `du -sb`, bytes reais, nao
disco): **~30,86 MB** no total (30,57 MB so em `saida/`, o acervo
propriamente dito -- atlas, catalogo, paletas, creditos). Tamanho do repo git
comprimido, via `gh api repos/igoresramos/waybuilder-avatar` (`size` em KB):
**13.014 KB ≈ 12,7 MB**.

Contra o teto de 1 GB (site publicado) e 1 GB (repo fonte, recomendado): folga
de ~30x. Cabe com sobra larga. Nao ha necessidade de workaround.

Observacao importante para o proximo passo (item 140/142, girar as 4
direcoes): mesmo o projetado de 118 MB das 4 direcoes cabe com folga dentro do
1 GB do Pages -- o teto que apertava era o de 100 MB de estaticos do Hobby da
Vercel (item 140), nao o do Pages.

### Configuracao escolhida

- **Fonte:** branch `main`, pasta raiz (`/`) -- **sem reorganizar o repo**.
  `saida/` continua onde esta; nao criei `docs/` como pasta especial do Pages
  (a pasta `docs/` deste relatorio e so a convencao deste repo pra documentos
  de sessao, nao tem relacao com a fonte do Pages).
- **`build_type`:** `legacy` (deploy direto da branch, sem Actions) -- e o que
  `POST /repos/{owner}/{repo}/pages` aceita com `source.branch`/`source.path`;
  confirmado em <https://docs.github.com/en/rest/pages/pages> antes de usar.
  Sem workflow de build porque nao ha nada pra compilar: `saida/` ja e o
  produto final versionado.
- **`.nojekyll`:** criado na raiz do repo. Necessario porque
  `specs/2026-08-01-avatar-do-personagem.md` tem front matter YAML
  (`---\nspec: ...`) que o Jekyll (motor default do Pages) interpretaria e
  processaria, alterando o arquivo servido. Confirmado o problema antes de
  agir: sem `.nojekyll` o Jekyll trata esse `.md` como pagina. Com
  `.nojekyll`, o Pages serve a arvore do git como esta, byte a byte.
- Comando usado (endpoint e campos verificados na doc oficial antes de
  chamar, nenhum inventado):
  ```
  gh api repos/igoresramos/waybuilder-avatar/pages -X POST \
    -f build_type=legacy -f source[branch]=main -f source[path]=/
  ```

URL publicada: **<https://igoresramos.github.io/waybuilder-avatar/>**

### Prova

```
$ curl -sI https://igoresramos.github.io/waybuilder-avatar/saida/atlas/accessory/L1/female.png
HTTP/2 200
content-type: image/png
access-control-allow-origin: *
content-length: 5781        # == wc -c local (5781) -- byte a byte, sem Jekyll

$ curl -sI https://igoresramos.github.io/waybuilder-avatar/saida/catalogo.json
HTTP/2 200
content-type: application/json; charset=utf-8
access-control-allow-origin: *
content-length: 1282941     # == wc -c local (1282941)

$ curl -sI https://igoresramos.github.io/waybuilder-avatar/specs/2026-08-01-avatar-do-personagem.md
HTTP/2 200
content-type: text/markdown; charset=utf-8
access-control-allow-origin: *
content-length: 30274       # == wc -c local (30274) -- confirma que o .nojekyll segurou
```

Build do Pages: commit `c2ed425` (o do `.nojekyll`), status `built`.

## 4. CORS e cache -- o app da Vercel consegue consumir isso?

### `fetch()` de JSON

**Sim, sem mudanca nenhuma no codigo do app.** `fetch()` usa modo `cors` por
padrao; o Pages responde `Access-Control-Allow-Origin: *` em toda resposta
(medido acima, e tambem no LPC). `Avatar.tsx:101` (`fetch(RAIZ + rel)`) e
`Avatar.tsx:560` (`` fetch(`${RAIZ}catalogo.json`) ``) funcionam cross-origin
assim que `RAIZ` apontar pro Pages.

### `<img>` / canvas -- veredito sobre taint

**Quebra, e quebra silenciosamente sem a mudanca certa.** O renderer LE PIXEL:
`Avatar.tsx:205` (`ctx.getImageData(...)`, dentro de `bitmapDa`) roda pra
**toda camada com `recolor`** -- ou seja, a maioria das pecas customizaveis do
avatar, nao um caso raro.

O carregamento da imagem, hoje, nao seta `crossOrigin`:

```
# Avatar.tsx:83-94
function carregarImagem(arq: string): Promise<HTMLImageElement> {
  ...
  const im = new Image();
  im.onload = () => ok(im);
  im.onerror = () => falha(new Error(arq));
  im.src = RAIZ + arq;                 // <- falta im.crossOrigin ANTES desta linha
  ...
}
```

Hoje `RAIZ` e same-origin (`/avatar/`), entao nao importa. No momento em que
`RAIZ` virar a URL do Pages (passo 3, fora deste escopo), qualquer `<img>`
carregada sem `crossOrigin="anonymous"` fica **tainted** pro canvas, mesmo com
o servidor mandando `Access-Control-Allow-Origin: *` -- o header so vale se o
browser pedir em modo CORS, e isso e decidido pelo atributo `crossOrigin` do
`<img>`, setado ANTES do `src`, nao pelo servidor sozinho. Sem isso,
`ctx.getImageData()` em `bitmapDa` (linha 205) estoura
`SecurityError: Failed to execute 'getImageData' ... tainted by cross-origin data`
pra toda peca com recolor -- o boneco carrega (drawImage funciona sem CORS),
mas customizar cor quebra na hora.

Fix preciso (nao aplicado -- e mudanca no `waybuilder`, fora deste repo):
adicionar `im.crossOrigin = "anonymous";` em `Avatar.tsx`, antes da linha 90
(`im.src = RAIZ + arq;`), dentro de `carregarImagem`.

### Service worker -- o que precisa mudar

Arquivo: `/home/igor0/waybuilder/app/vite.config.ts` (so leitura, nada
alterado).

**Linha 53** -- a regra de runtime cache do acervo:

```ts
urlPattern: /\/avatar\/.*\.(png|json)$/,
handler: "CacheFirst",
options: { cacheName: "avatar", ... },
```

Dois problemas quando `RAIZ` virar cross-origin:

1. **O caminho muda.** A URL passa a ser algo como
   `https://igoresramos.github.io/waybuilder-avatar/saida/atlas/.../arquivo.png`
   -- o segmento literal `/avatar/` deixa de existir na URL (a menos que o
   passo 3 escolha manter esse nome de segmento no path do Pages, decisao do
   Igor). A regex tem de ser reescrita pro caminho real que sair do passo 3.
2. **RegExp do Workbox nao casa cross-origin por padrao.** `workbox-routing`
   so aceita uma `RegExp` bruta (`RegExpRoute`) para requests cross-origin
   quando o match comeca no indice 0 da URL inteira (`url.href`) -- ou seja, a
   regex precisaria ancorar a origem tambem, o que uma regex de path solto
   como a atual nunca faz. Na pratica, sem trocar a forma do matcher, essa
   regra fica muda: nao da erro, so nunca casa, e o acervo passa a nunca ser
   cacheado (toda visita busca de novo, contrariando o "offline de verdade"
   da spec).

   Troca necessaria: substituir o `urlPattern` (RegExp) por uma **funcao
   matcher** (`({url}) => ...`), que nao tem essa restricao de indice 0:

   ```ts
   urlPattern: ({ url }) =>
     url.origin === "https://igoresramos.github.io" &&
     /\.(png|json)$/.test(url.pathname),
   ```

   (o prefixo exato do `pathname` -- `/waybuilder-avatar/saida/...` ou o que
   o passo 3 decidir pra `RAIZ` -- deveria entrar na condicao tambem, pra nao
   cachear qualquer coisa daquele dominio.)

**Linha 37** -- `navigateFallbackDenylist: [/^\/base\//, /^\/avatar\//],`. A
entrada `/^\/avatar\//` fica morta: e um filtro pra navegacao same-origin, e
nenhuma URL do app vai mais bater em `/avatar/...` depois da troca. Nao quebra
nada (so deixa de ter efeito), mas vale remover por precisao -- descreve um
caminho que nao existe mais.

Nao precisa de `cacheableResponse` plugin adicional: a resposta do Pages e
`200` com CORS (nao opaca), entao o `CacheFirst` padrao ja cacheia sem
configuracao extra -- **desde que** o fetch/img seja feito em modo `cors`
(que exige o `crossOrigin` do paragrafo anterior pro `<img>`; `fetch()` ja usa
`cors` por padrao).
