# waybuilder-avatar

O acervo de sprites do avatar do [Waybuilder](https://github.com/igoresramos/waybuilder)
-- um recorte curado do [Liberated Pixel Cup](https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator),
empacotado no formato que o app consome.

A spec da feature esta em [`specs/2026-08-01-avatar-do-personagem.md`](specs/2026-08-01-avatar-do-personagem.md).

## O que tem aqui

| caminho | o que e |
|---|---|
| `build.py` | o passo de build: le a fonte, recorta, empacota, emite o catalogo |
| `buscar_fonte.sh` | reconstroi o clone do LPC no pin (sparse, sem o `sources/`) |
| `PIN` | commit do LPC de onde o acervo saiu |
| `saida/` | **o produto**: atlas, catalogo, paletas, creditos, relatorio |
| `validacao/` | PNGs da conferencia visual da composicao |
| `visualizador.html` | pagina solta para olhar o acervo sem subir o app |

`fontes/` fica **fora do git** -- sao 100+ MB reconstruiveis. `saida/` e
**versionado**, porque e o que o consumidor le e regera-lo exige o clone da
fonte (spec, decisao 8b).

## Rodar o build

```bash
./buscar_fonte.sh     # so na primeira vez, ou ao mudar o PIN
python3 build.py
```

O build reescreve `saida/` e grava `saida/relatorio.md` com peso e contagem
medidos. Esse relatorio entra no repo e e comparado build a build.

## O recorte

| medida | valor |
|---|---|
| itens no catalogo | 609 |
| cobertura das pecas elegiveis | 95,6% (609 de 637) |
| arquivos em `saida/` | 2.813 |
| peso | 6,71 MB |
| animacoes | `idle`, `combat_idle`, `walk`, `sit`, `run` |
| variantes de corpo | `male`, `female`, `pregnant`, `teen` |
| direcao | so a de frente |

O corte da direcao sozinho tira 75% do que sobra depois do corte de animacao --
e a razao de nao dar para girar o boneco. Divida conhecida: 28 pecas de layout
nao-universal (13 delas armas) ficaram de fora; ver a spec.

## Creditos e licenca

A arte e do Liberated Pixel Cup, com **licenca por peca** (CC0, CC-BY,
CC-BY-SA 3.0, OGA-BY 3.0). A atribuicao completa -- fonte, pin e a lista de
autores -- e gerada em [`saida/creditos.json`](saida/creditos.json) a partir do
`CREDITS.csv` do upstream, e e obrigatoria em qualquer uso.

Pecas cuja unica licenca e GPL sao **excluidas no build**, para nao contaminar o
app consumidor. No pin atual o filtro nao cortou nenhuma.

Nada do codigo do gerador do LPC foi copiado: a composicao e o recolor foram
escritos do zero a partir do `PALETTE_RECOLOR_GUIDE.md` deles.

## Quem consome

Hoje, ninguem -- o renderer do Waybuilder e o passo 2 da spec e ainda nao
existe. Como o acervo chega ao build do app (submodule, pacote npm ou fetch) e
decisao em aberto, registrada no item 2 de "Aberto" na spec.
