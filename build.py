#!/usr/bin/env python3
"""
O passo de build do avatar -- spec `specs/2026-08-01-avatar-do-personagem.md`.

Le o clone do LPC em `fontes/lpc` (reconstruivel por `buscar_fonte.sh`) e emite
em `saida/` o acervo que o app consome. O app NUNCA le a fonte: ele le o
catalogo e os atlas produzidos aqui.

O que este passo faz, e por que (decisao 3 da spec):

  a. normaliza os DOIS formatos do upstream -- o acervo esta migrando de
     "cor e arquivo" para "cor e paleta", e os dois coexistem (medido: 76.491
     arquivos no formato antigo, 11.744 no novo). O app so ve um.
  b. recorta as animacoes para cinco: idle, combat_idle, walk, sit, run.
  b2. recorta as variantes de corpo: skeleton e zombie ficam fora. Entram os
     seis do gerador -- male, female, teen, child, muscular, pregnant.
  b3. recorta a DIRECAO: so a de frente. O LPC empilha 4 direcoes por folha, em
     linhas de 64px, na ordem [costas, perfil-esq, FRENTE, perfil-dir] --
     verificado visualmente, nao suposto. Sozinho, este corte tira 75%.
  c. concatena as 5 animacoes numa TIRA de 64px por (peca, variante, cor):
     22.925 arquivos viram ~4.600. Horizontal, nao vertical -- empilhar em
     coluna obriga a folha a ter a largura da animacao mais larga, e medido
     isso quase dobrava o acervo.
  e. emite catalogo com IDs PROPRIOS -- o documento de personagem nunca
     referencia caminho do upstream, que esta em reorganizacao ativa.
  f. filtra pecas cuja UNICA licenca e GPL.
  g. emite os creditos a partir do CREDITS.csv da raiz do repo.
  h. registra peso e contagem medidos em `saida/relatorio.md`.

Rode: python3 build.py
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
FONTE = os.path.join(AQUI, "fontes", "lpc")
SAIDA = os.path.join(AQUI, "saida")

# -- o recorte ---------------------------------------------------------------

ANIMACOES = ["idle", "combat_idle", "walk", "sit", "run"]

# Ordem do gerador (`sources/state/constants.ts:9`). `child` e `muscular`
# voltaram em @9: o corte da 3b2 escondia 19 definitions que so tinham arte de
# crianca -- elas caiam em "sem arte" e sumiam da tela.
CORPOS = ["male", "female", "teen", "child", "muscular", "pregnant"]

# O gerador nao toca os frames em ordem crua: anima por CICLO, a 8 FPS
# (`sources/canvas/preview-animation.ts:74,180`; ciclos em
# `state/constants.ts:124-154`). `walk` pula o frame 0, que e pose parada --
# sem o ciclo a caminhada soluca uma pose parada a cada volta. `combat_idle`
# usa o ciclo de `combat`, que e como o gerador chama a mesma linha.
CICLOS: dict[str, list[int]] = {
    # DECISAO DO DONO, contra o gerador: ele usa [0, 0, 1], que a 8 FPS deixa a
    # primeira pose o dobro do tempo da segunda -- na tela a respiracao fica
    # torta, meio truncada. Com [0, 0, 1, 1] os dois lados duram igual e o
    # balanco fecha. "tem que ser 0-0-1-1, repetindo frames mesmo".
    "idle": [0, 0, 1, 1],
    "combat_idle": [0, 0, 1],
    "walk": [1, 2, 3, 4, 5, 6, 7, 8],
    "sit": [0] * 5 + [1] * 5 + [2] * 5,
    "run": [0, 1, 2, 3, 4, 5, 6, 7],
}
FPS = 8

# a folha empilha 4 direcoes em linhas de 64px; a de frente e a TERCEIRA.
# Verificado compondo body+head e olhando: linha 0 nao tem olhos (costas),
# 1 e 3 sao perfis, 2 encara. Errar aqui poe o acervo inteiro de costas.
ALTURA = 64
LINHA_DA_FRENTE = 2

# As direcoes gravadas, com a linha de origem de cada uma na folha do LPC --
# spec, decisao 3b3 @12. DUAS: frente e perfil direito, por decisao do dono.
#
# A ORDEM AQUI NAO E A DO LPC, e a diferenca e proposital. Gravando a frente
# PRIMEIRO, o endereco antigo (`x + k*64`, que o app usava quando so havia uma
# direcao) continua caindo na frente. Se a ordem do LPC fosse preservada, o
# mesmo endereco passaria a apontar para as COSTAS -- o acervo inteiro viraria
# de costas sem um erro sequer, que e o modo de falha que o principio zero
# proibe.
#
# ESPELHAR o perfil direito para ter o esquerdo de graca foi medido e NAO
# funciona: em 353 folhas de `walk`, o perfil esquerdo e o espelho do direito em
# **0,3%** dos casos, e realmente diferente em 99,2%. O LPC alterna as pernas na
# caminhada, entao o frame k de um lado nao corresponde ao espelho do frame k do
# outro. A terceira direcao custaria acervo como qualquer outra.
DIRECOES = [("frente", 2), ("perfil_dir", 3)]

# As direcoes vao no eixo X, ao lado dos frames -- nao empilhadas no Y junto
# das cores. Medido no catalogo de 643 atlas: no eixo Y, empilhar 4 direcoes
# fazia 105 deles passarem do teto de textura de 16.384 px (o pior, `wings`,
# chegava a 65.280); no eixo X nenhum estoura. Mesma area, so muda a forma.
#
# Endereco de um frame: x_da_animacao + (indice_da_direcao * frames + k) * 64.

# nomes que aparecem como ARQUIVO no formato novo (arquivo = animacao) e como
# DIRETORIO no formato antigo (diretorio = animacao, arquivo = cor)
TODAS_ANIMACOES = {
    "idle", "combat_idle", "walk", "sit", "run", "hurt", "climb", "jump",
    "emote", "shoot", "slash", "thrust", "spellcast", "backslash", "halfslash",
    "combat", "1h_slash", "1h_backslash", "1h_halfslash", "watering",
}


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower())
    return s.strip("-") or "sem-nome"


# -- leitura dos sheet_definitions -------------------------------------------

def identidade_da_peca(rel: str, d: dict) -> dict:
    """Slot e caminho de navegacao de uma peca (spec, decisao 6b).

    O slot decide EXCLUSIVIDADE e vem do `type_name`. Nao do caminho: 25 dos
    104 slots aparecem em mais de um diretorio -- `weapon` chega a morar dentro
    de `tools/` --, entao nao existe funcao do caminho que devolva o slot.
    """
    return {
        "slot": d.get("type_name"),
        "caminho": os.path.dirname(rel).split(os.sep),
    }


# -- agrupamento dos quadradinhos ---------------------------------------------
#
# A UI e um painel de casas, uma por slot: a casa mostra o que esta equipado e
# clicar nela abre o picker daquele slot. Isso torna a exclusividade visivel --
# uma casa, uma peca -- e e o motivo de o grupo NUNCA decidir exclusividade.
#
# Curado a mao porque o caminho do upstream agrupa mal (25 slots aparecem em
# mais de um diretorio). Tabela versionada e auditavel; slot novo cai em
# "Outros" com aviso, nunca some da tela.
GRUPO_DE_SLOT: dict[str, tuple[str, ...]] = {
    "Corpo": ("body", "shadow", "tail", "wings", "wings_dots", "wings_edge",
              "fins", "horns", "prosthesis_hand", "prosthesis_leg",
              "wheelchair"),
    "Marcas": ("wound_arm", "wound_brain", "wound_eye_left", "wound_eye_right",
               "wound_mouth", "wound_ribs", "wrinkles", "bandages"),
    "Cabeça": ("head", "ears", "ears_inner", "furry_ears", "furry_ears_skin",
               "nose"),
    "Rosto": ("eyes", "facial_eyes", "expression", "expression_crying",
              "eyebrows", "beard", "mustache", "facial_mask", "facial_left",
              "facial_left_trim", "facial_right", "facial_right_trim"),
    "Cabelo": ("hair", "hairextl", "hairextr", "ponytail", "updo", "hairtie",
               "hairtie_rune"),
    "Chapéu": ("hat", "hat_trim", "hat_overlay", "hat_accessory", "hat_buckle",
               "headcover", "headcover_rune", "bandana", "bandana_overlay",
               "visor"),
    "Torso": ("clothes", "jacket", "jacket_trim", "jacket_collar",
              "jacket_pockets", "vest", "dress", "dress_trim", "dress_sleeves",
              "dress_sleeves_trim", "sleeves", "apron", "overalls", "sash",
              "sash_tie", "cargo", "chainmail"),
    "Pernas e Pés": ("legs", "shoes", "shoes_toe", "socks"),
    "Armadura": ("armour", "bauldron", "bracers", "gloves", "wrists",
                 "shoulders", "arms", "belt", "buckles"),
    "Acessórios": ("neck", "necklace", "charm", "earrings", "earring_left",
                   "earring_right", "ring", "accessory", "cape", "cape_trim",
                   "backpack", "backpack_straps", "quiver"),
    "Armas": ("weapon", "weapon_magic_crystal", "ammo", "shield",
              "shield_pattern", "shield_trim", "shield_paint"),
}

_DE_SLOT = {s: g for g, ss in GRUPO_DE_SLOT.items() for s in ss}


def grupo_do_slot(slot: str) -> str:
    return _DE_SLOT.get(slot, "Outros")


def segue_cor_do_corpo(d: dict) -> bool:
    """A peca herda o tom de pele do corpo (`match_body_color`, 79 no acervo).

    Cabeca, nariz, orelha, rugas e expressao sao slots SEPARADOS com material
    `body`. Sem esta regra, trocar o tom de pele deixa a cabeca de outra cor --
    o gerador forca a cor do corpo nesses itens em tempo de render
    (`sources/state/palettes.ts:119-123`).
    """
    return bool(d.get("match_body_color"))


def ler_metas_de_material(raiz: str | None = None) -> dict[str, dict]:
    """`meta_<material>.json` de cada material de paleta: `default` e `base`.

    Sao eles que dizem em que rampa a arte foi pintada -- o cabelo nasce em
    `ulpc.orange`, a pele em `ulpc.light`. Sem isso o recolor nao tem de onde
    sair.
    """
    raiz = raiz or os.path.join(FONTE, "palette_definitions")
    fora: dict[str, dict] = {}
    if not os.path.isdir(raiz):
        return fora
    for mat in sorted(os.listdir(raiz)):
        caminho = os.path.join(raiz, mat, f"meta_{mat}.json")
        if not os.path.isfile(caminho):
            continue
        try:
            with open(caminho, encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("type") == "material":
            fora[mat] = d
    return fora


def base_do_canal(material: str, base: str | None,
                  metas: dict[str, dict]) -> str | None:
    """A rampa de ORIGEM do canal, sempre no formato `<versao>.<rampa>`.

    Regra do gerador (`scripts/generateSources/item-helper.js:55-66`):
    sem `base`, vale `<default>.<base>` do material; com `base` sem ponto, a
    versao e a padrao do material; com ponto, manda inteiro.

    41 canais do acervo declaram base proprio (`cloth.brown`,
    `body.lpcr.ivory`). O app usava sempre o base do material e o recolor nao
    casava pixel nenhum: a cor aparecia na lista e nao pintava.
    """
    md = metas.get(material)
    if md is None:
        return None
    if not base:
        return f"{md['default']}.{md['base']}"
    return base if "." in base else f"{md['default']}.{base}"


def normalizar_recolors(r: dict | None,
                        metas: dict[str, dict] | None = None) -> list[dict]:
    """Um formato so de cor, como manda a decisao 3a.

    O upstream declara de dois jeitos: `{material, palettes}` direto (359
    itens) ou um bloco por cor (27 itens). Um elmo com metal e tiras de tecido
    tem **duas cores independentes**, nao uma -- por isso o app recebe sempre
    uma lista de canais, e nunca precisa saber qual formato o item usava.

    Cada canal sai com a rampa de ORIGEM ja resolvida (`base`, e `fonte` quando
    o proprio canal traz as cores). O app nao reimplementa a regra -- e quando
    reimplementou, reimplementou errado.
    """
    if not isinstance(r, dict) or not r:
        return []
    metas = metas if metas is not None else {}

    def canal(nome: str, d: dict) -> dict:
        fora = {"nome": nome, "material": d["material"],
                "paletas": d.get("palettes", [])}
        if d.get("label"):
            fora["rotulo"] = d["label"]
        base = base_do_canal(d["material"], d.get("base"), metas)
        if base:
            fora["base"] = base
        # `source` vence a busca por paleta: sao as cores da arte, escritas na
        # propria definition (`sources/state/palettes.ts:179-182`)
        if isinstance(d.get("source"), list) and d["source"]:
            fora["fonte"] = d["source"]
        return fora

    if "material" in r:
        return [canal("cor", r)]
    return [
        canal(v.get("type_name") or k, v)
        for k, v in sorted(r.items())
        if isinstance(v, dict) and "material" in v
    ]


def faixas_declaradas(achadas: list, variants: list[str] | None) -> list:
    """So e cor da peca a faixa que a peca DECLARA em `variants`.

    O diretorio da animacao tem arquivos que nao sao variante -- `_leather`,
    `_brown`, `crown_red`, `spear`. Medido: 55 faixas assim entravam no
    catalogo e viravam botao de cor que o gerador oficial nunca ofereceu.

    A declaracao usa espaco onde o arquivo usa underscore
    (`variantToFilename`: `"kite blue blue"` -> `kite_blue_blue.png`).

    Peca sem `variants` mantem o que achou: 4 do acervo estao nessa situacao e
    filtrar por lista vazia as apagaria. Se nada casar, tambem mantem -- perder
    a arte e pior que oferecer uma cor a mais.
    """
    if not variants:
        return achadas
    permitidas = {v.replace(" ", "_") for v in variants}
    filtradas = [c for c in achadas if c is None or c in permitidas]
    return filtradas or achadas


NOMES = os.path.join(AQUI, "nomes")


def ler_nomes_ptbr(raiz: str | None = None) -> dict[str, str]:
    """`id do item -> nome em pt-BR`, unido dos mapas de `nomes/`.

    Traduzido a mao em tres blocos, um por frente de trabalho. A uniao tem de
    ser disjunta: id em dois arquivos e conflito de traducao, e o build avisa
    em vez de escolher em silencio.
    """
    raiz = raiz or NOMES
    fora: dict[str, str] = {}
    if not os.path.isdir(raiz):
        return fora
    for a in sorted(os.listdir(raiz)):
        if not a.endswith(".json") or a == "slots.json":
            continue
        try:
            with open(os.path.join(raiz, a), encoding="utf-8") as f:
                d = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ! mapa de nomes ilegivel, pulado: {a} ({e})")
            continue
        for k, v in d.items():
            if k in fora and fora[k] != v:
                print(f"  ! id traduzido duas vezes: {k} "
                      f"({fora[k]!r} / {v!r}) -- vale o primeiro")
                continue
            fora[k] = v
    return fora


def _ler_mapa(nome: str, raiz: str | None = None) -> dict[str, str]:
    caminho = os.path.join(raiz or NOMES, nome)
    if not os.path.isfile(caminho):
        return {}
    try:
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"  ! {nome} ilegivel ({e})")
        return {}


def ler_rotulos_de_slot(raiz: str | None = None) -> dict[str, str]:
    """`slot -> rotulo em pt-BR`. A casa mostrava `facial_eyes` cru."""
    return _ler_mapa("slots.json", raiz)


def ler_rotulos_de_cor(raiz: str | None = None) -> dict[str, str]:
    """`nome cru da cor -> rotulo em pt-BR`.

    Cobre os dois mundos: rampa de paleta (`emerald`) e faixa de atlas
    (`kite_blue_blue`). A chave e o nome CRU, com prefixo de peca -- a
    traducao ja descarta o prefixo no valor ("Azul e Azul"), menos nos
    amuletos, onde o metal e informacao de cor ("Aco e Amarelo").
    """
    return _ler_mapa("cores.json", raiz)


def ler_paletas(raiz: str | None = None) -> dict[tuple[str, str], dict]:
    """`(material, versao) -> {rampa: [hex]}` de `palette_definitions`."""
    raiz = raiz or os.path.join(FONTE, "palette_definitions")
    fora: dict[tuple[str, str], dict] = {}
    if not os.path.isdir(raiz):
        return fora
    for mat in sorted(os.listdir(raiz)):
        d = os.path.join(raiz, mat)
        if not os.path.isdir(d):
            continue
        for a in sorted(os.listdir(d)):
            if a.startswith("meta_") or not a.endswith(".json"):
                continue
            try:
                with open(os.path.join(d, a), encoding="utf-8") as f:
                    fora[(mat, a[len(mat) + 1:-5])] = json.load(f)
            except (OSError, json.JSONDecodeError, IndexError):
                continue
    return fora


def _rgb(hexa: str) -> tuple[int, int, int]:
    n = int(hexa.lstrip("#"), 16)
    return ((n >> 16) & 255, (n >> 8) & 255, n & 255)


def rampa_de_origem(canal: dict, paletas: dict[tuple[str, str], dict]
                    ) -> list[str] | None:
    """As cores em que a arte do canal foi pintada.

    `fonte` vence a busca por paleta -- e o que o gerador faz quando a
    definition traz `source` (`sources/state/palettes.ts:179-182`).
    """
    if canal.get("fonte"):
        return canal["fonte"]
    base = canal.get("base")
    if not base or "." not in base:
        return None
    versao, rampa = base.split(".", 1)
    return paletas.get((canal["material"], versao), {}).get(rampa)


def canal_pinta(canal: dict, cores_da_arte: set,
                paletas: dict[tuple[str, str], dict]) -> bool:
    """O recolor deste canal muda algum pixel desta peca?

    Medido: 9 dos 413 canais do acervo declaram uma rampa de origem que NAO
    aparece em nenhum pixel da arte -- os olhos das cabecas idosas, o laco dos
    cabelos amarrados, as expressoes `-alt`. Eles ofereciam ate 121 cores e
    nenhuma pintava. O pedido do dono e literal: a cor listada tem de ser real
    e pareavel com o asset.
    """
    rampa = rampa_de_origem(canal, paletas)
    if not rampa:
        return False
    return bool(cores_da_arte & {_rgb(c) for c in rampa})


def parear_por_prefixo(
    acessorios: list[dict], principais: list[dict]
) -> dict[str, list[str]]:
    """`combina_com`: liga trim/overlay/fivela ao chapeu de mesmo prefixo.

    Os slots continuam separados (decisao do dono): isto so deixa a UI filtrar
    a grade pelo chapeu equipado e avisar quando o acessorio fica orfao. Casa
    17 dos 21 acessorios do pin; o resto e curadoria.
    """
    fora: dict[str, list[str]] = {}
    for a in acessorios:
        cands = [p for p in principais if a["nome"].startswith(p["nome"])]
        if not cands:
            continue
        # o par certo e o mais especifico: "Tricorne Captain" e nao "Tricorne"
        melhor = max(cands, key=lambda p: len(p["nome"]))
        fora[a["id"]] = [melhor["id"]]
    return fora


def sem_arte_em(item: dict, corpos: list[str]) -> list[str]:
    """Variantes de corpo em que a peca nao aparece.

    Sem isto a celula da grade mostra o personagem inalterado e o preview
    mente por omissao -- 92 pecas nao tem arte para `pregnant`.
    """
    tem = {c for cam in item["camadas"] for c in cam["corpos"]}
    return [c for c in corpos if c not in tem]


def ler_grupos(raiz: str) -> dict[str, dict]:
    """Os `meta_*.json`: prioridade e rotulo de cada diretorio de navegacao.

    Ate @3 o build pulava todo arquivo `meta_*` junto com as pecas, e com ele ia
    embora a ordem de exibicao e o nome legivel do grupo ("Human Heads").
    """
    fora: dict[str, dict] = {}
    for base, _, arqs in os.walk(raiz):
        for a in sorted(arqs):
            if not (a.startswith("meta_") and a.endswith(".json")):
                continue
            try:
                with open(os.path.join(base, a), encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"  ! meta ilegivel, pulado: {a} ({e})")
                continue
            rel = os.path.relpath(base, raiz).replace(os.sep, "/")
            entrada: dict = {"prioridade": d.get("priority", 0)}
            if d.get("label"):
                entrada["rotulo"] = d["label"]
            fora[rel] = entrada
    return fora


def ler_definitions() -> list[dict]:
    """Os 768 JSONs, anotados com categoria, slot e caminho.

    A categoria e o primeiro segmento do caminho e serve so para estatistica. O
    que decide exclusividade e o `_slot`, que vem do `type_name` do conteudo --
    ver `identidade_da_peca`.
    """
    raiz = os.path.join(FONTE, "sheet_definitions")
    saida = []
    for base, _, arqs in os.walk(raiz):
        for a in sorted(arqs):
            if not a.endswith(".json") or a.startswith("meta_"):
                continue
            caminho = os.path.join(base, a)
            rel = os.path.relpath(caminho, raiz)
            try:
                with open(caminho, encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"  ! definition ilegivel, pulada: {rel} ({e})")
                continue
            d["_arquivo"] = rel
            d["_categoria"] = rel.split(os.sep)[0]
            ident = identidade_da_peca(rel, d)
            d["_slot"] = ident["slot"]
            d["_caminho"] = ident["caminho"]
            saida.append(d)
    return saida


def licencas(d: dict) -> set[str]:
    return {l for c in d.get("credits", []) or [] for l in c.get("licenses", []) or []}


def camadas(d: dict) -> list[tuple[int, dict]]:
    """`layer_1..layer_N` na ordem, cada uma com seu zPos e paths por variante."""
    fora = []
    for chave, val in d.items():
        m = re.fullmatch(r"layer_(\d+)", chave)
        if m and isinstance(val, dict):
            fora.append((int(m.group(1)), val))
    return sorted(fora, key=lambda x: x[0])


# -- resolucao de arquivo: os dois formatos ----------------------------------

def arquivos_da_animacao(dirbase: str, anim: str) -> list[tuple[str | None, str]]:
    """
    Devolve [(cor, caminho)]. `cor is None` = formato novo (cor vem da paleta).

    NOVO:   <dirbase>/<anim>.png
    ANTIGO: <dirbase>/<anim>/<cor>.png
    """
    d = os.path.join(FONTE, "spritesheets", dirbase.strip("/"))

    # O ANTIGO vem primeiro de proposito: os dois formatos COEXISTEM no mesmo
    # diretorio em varias pecas (o Tricorne tem `idle.png` solto E uma pasta
    # `idle/` com 24 cores). Achar o arquivo solto antes fazia a peca nascer
    # com uma cor so -- as cores de um asset sao dele, nao da categoria, e sao
    # justamente estas. Vale para as 241 pecas que declaram `variants`.
    subdir = os.path.join(d, anim)
    if os.path.isdir(subdir):
        achados = [
            (a[:-4], os.path.join(subdir, a))
            for a in sorted(os.listdir(subdir))
            if a.endswith(".png")
        ]
        if achados:
            return achados

    novo = os.path.join(d, f"{anim}.png")
    if os.path.isfile(novo):
        return [(None, novo)]
    return []


# -- composicao --------------------------------------------------------------

def recortar_frente(im, largura_alvo: int, linha: int = LINHA_DA_FRENTE):
    """Uma linha da folha, em largura fixa (sobra vira transparente)."""
    from PIL import Image

    y = linha * ALTURA
    if im.size[1] < y + ALTURA:
        return None  # folha sem essa linha (fora do layout universal)
    faixa = im.crop((0, y, im.size[0], y + ALTURA))
    if faixa.size[0] == largura_alvo:
        return faixa
    tela = Image.new("RGBA", (largura_alvo, ALTURA), (0, 0, 0, 0))
    tela.alpha_composite(faixa.crop((0, 0, min(faixa.size[0], largura_alvo), ALTURA)))
    return tela


def quantizar_exato(im):
    """Indexa mantendo cada cor RGB intacta.

    `convert("P", palette=ADAPTIVE)` reescreve as cores por median cut, e e
    lossy mesmo abaixo de 256 cores: mediu-se o contorno do corpo virando
    (39,24,32) onde a fonte tem #271920 -- a primeira cor da rampa `light`.

    Aqui a paleta E a lista de cores da imagem, e o mapeamento roda em C
    (`quantize` com `dither=NONE`): a cor mais proxima de uma cor que esta na
    paleta e ela mesma, com distancia zero. Em Python puro isto levava horas.
    """
    from PIL import Image

    rgba = im.convert("RGBA")
    # Contar CORES, nao combinacoes RGBA: com `maxcolors=256` um atlas de 200
    # cores em dois niveis de alpha da 400 combinacoes e caia fora, mesmo
    # cabendo folgado em 256 indices. Foi o que jogou 127 atlas para RGBA e
    # quase dobrou o peso do acervo.
    cores = rgba.getcolors(maxcolors=1 << 20)
    if cores is None:
        return im

    opacas = sorted({c[:3] for _, c in cores if c[3] != 0})
    if not opacas or len(opacas) > 255:
        return im  # sem indice sobrando para a transparencia: fica RGBA

    transp = len(opacas)
    plana: list[int] = []
    for c in opacas:
        plana += list(c)
    # Os slots sobrando repetem a ULTIMA cor valida, nunca preto: (0,0,0) vira
    # um atrator e o `quantize` colapsa tons escuros nele, perdendo cor.
    resto = list(opacas[-1]) if opacas else [0, 0, 0]
    plana += resto * (256 - transp)

    molde = Image.new("P", (1, 1))
    molde.putpalette(plana)
    saida = rgba.convert("RGB").quantize(palette=molde, dither=Image.NONE)

    alfa = rgba.getchannel("A")
    saida.paste(transp, mask=alfa.point(lambda a: 255 if a == 0 else 0))
    saida.info["transparency"] = transp
    return saida


def cores_de(im) -> set:
    """As cores RGB visiveis de uma imagem -- para o portao de fidelidade."""
    rgba = im.convert("RGBA")
    achadas = rgba.getcolors(maxcolors=1 << 20) or []
    return {c[:3] for _, c in achadas if c[3] != 0}


# atlas que ficaram RGBA porque indexar perderia cor -- contados no relatorio
RGBA_POR_FIDELIDADE: list[str] = []


def salvar_paletizado(im, destino: str) -> int:
    """PNG indexado quando cabe em 256 cores -- ~15% do acervo vem em RGBA."""
    from PIL import Image

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    saida = im
    if len(cores_de(im)) <= 255:
        # Paleta EXATA, nunca ADAPTIVE: median cut e lossy mesmo abaixo de 256
        # cores e ja corrompeu o contorno do corpo em 1 bit (#271920 virou
        # 39,24,32). Como a primeira cor da rampa `light` e justamente essa, o
        # recolor de pele passava a depender da tolerancia para nao falhar.
        indexada = quantizar_exato(im)
        # Portao: indexar NAO pode mexer em cor nenhuma -- uma diferenca de 1
        # bit ja aproxima o recolor do limite de tolerancia e falharia calado.
        # Quando nao da para indexar sem perder cor, fica RGBA: pesa mais e e
        # exato por definicao. Melhor alguns KB do que um tom de pele que nao
        # repinta.
        if cores_de(im) == cores_de(indexada):
            saida = indexada
        else:
            RGBA_POR_FIDELIDADE.append(destino)
    buf = io.BytesIO()
    saida.save(buf, "PNG", optimize=True, compress_level=9)
    with open(destino, "wb") as f:
        f.write(buf.getvalue())
    return buf.tell()


# Limite de textura que os navegadores garantem. Medido: consolidando por slot
# sem teto, 12 grupos passariam de 19.072 px -- `wings` sao 11 pecas com muitas
# cores. Acima disso o canvas falha, as vezes sem erro.
TETO_DE_TEXTURA = 16384


def empacotar_por_teto(alturas: list[int], teto: int = TETO_DE_TEXTURA
                       ) -> list[list[int]]:
    """Divide as pecas de um slot em atlas que respeitem o teto de altura.

    Devolve grupos de indices, na ordem. Peca sozinha maior que o teto vai
    assim mesmo: perde-la seria pior que um atlas grande.
    """
    grupos: list[list[int]] = []
    atual: list[int] = []
    soma = 0
    for i, h in enumerate(alturas):
        if atual and soma + h > teto:
            grupos.append(atual)
            atual, soma = [], 0
        atual.append(i)
        soma += h
    if atual:
        grupos.append(atual)
    return grupos


def montar_atlas(dirbase: str, cores: list[str | None]):
    """
    Um atlas por (peca, camada, corpo): cada COR e uma faixa de 64px.

    Medido: 25 cores como arquivos separados custam 15.212 B; empilhadas num
    atlas, 12.151 B (80%). Sao ~128 B de cabecalho por PNG, e com 10 mil
    arquivos isso e 1,4 MB -- alem de 10 mil entradas no git e 25 requests para
    ciclar as cores de uma peca em vez de um.

    Devolve (imagem, [(animacao, frames, x)], {cor: y}) ou (None, [], {}).
    """
    from PIL import Image

    faixas = []
    mapa_anim: list[tuple[str, int, int]] = []
    for cor in cores:
        tira, mapa = montar_folha(dirbase, cor)
        if tira is None:
            continue
        if not mapa_anim:
            mapa_anim = mapa
        faixas.append((cor or "base", tira))
    if not faixas:
        return None, [], {}

    largura = max(t.size[0] for _, t in faixas)
    atlas = Image.new("RGBA", (largura, ALTURA * len(faixas)), (0, 0, 0, 0))
    por_cor: dict[str, int] = {}
    for i, (nome, tira) in enumerate(faixas):
        atlas.alpha_composite(tira, (0, i * ALTURA))
        por_cor[nome] = i * ALTURA
    return atlas, mapa_anim, por_cor


def montar_folha(dirbase: str, cor_alvo: str | None):
    """
    Concatena as 5 animacoes (so a frente) numa TIRA de 64px de altura.

    Horizontal, nao vertical. Empilhar verticalmente obriga a folha a ter a
    largura da animacao mais larga, e `walk` tem 9 frames contra 2 de `idle`:
    medido, o padding quase dobrava o acervo (34 MB contra os 8 previstos).
    Concatenar lado a lado da area exatamente igual a soma dos recortes.

    Devolve (imagem, [(animacao, frames, x)]) ou (None, []).
    """
    from PIL import Image

    faixas = []
    for anim in ANIMACOES:
        achados = arquivos_da_animacao(dirbase, anim)
        if not achados:
            continue
        escolhido = None
        for cor, caminho in achados:
            if cor == cor_alvo:
                escolhido = caminho
                break
        if escolhido is None:
            continue
        try:
            im = Image.open(escolhido).convert("RGBA")
        except OSError:
            continue
        if im.size[1] < (LINHA_DA_FRENTE + 1) * ALTURA:
            continue  # folha fora do layout universal de 4 direcoes
        faixas.append((anim, im))
    if not faixas:
        return None, []

    # cada animacao ocupa as 4 direcoes lado a lado: 4x a largura de antes
    largura = sum(im.size[0] for _, im in faixas) * len(DIRECOES)
    tira = Image.new("RGBA", (largura, ALTURA), (0, 0, 0, 0))
    mapa = []
    x = 0
    for anim, im in faixas:
        larg_anim = im.size[0]
        posto = False
        for i, (_nome, linha) in enumerate(DIRECOES):
            faixa = recortar_frente(im, larg_anim, linha)
            if faixa is None:
                continue  # folha sem essa linha: fica transparente, e o
                # renderer cai no fallback da decisao 12
            tira.alpha_composite(faixa, (x + i * larg_anim, 0))
            posto = True
        if not posto:
            continue
        mapa.append((anim, larg_anim // ALTURA, x))
        x += larg_anim * len(DIRECOES)
    if not mapa:
        return None, []
    return tira, mapa


# -- creditos ----------------------------------------------------------------

def ler_creditos() -> dict[str, dict]:
    """CREDITS.csv da raiz do repo -- o proprio upstream ja o gera."""
    caminho = os.path.join(FONTE, "CREDITS.csv")
    if not os.path.isfile(caminho):
        print("  ! CREDITS.csv ausente -- creditos sairao so dos definitions")
        return {}
    por_arquivo = {}
    with open(caminho, encoding="utf-8") as f:
        for linha in csv.DictReader(f):
            chave = (linha.get("filename") or linha.get("file") or "").strip()
            if chave:
                por_arquivo[chave] = linha
    return por_arquivo


# -- build -------------------------------------------------------------------

def main() -> int:
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        print("erro: este passo precisa do Pillow (pip install Pillow)")
        return 1

    if not os.path.isdir(FONTE):
        print(f"erro: fonte ausente em {FONTE} -- rode avatar/buscar_fonte.sh")
        return 1

    pin = "desconhecido"
    try:
        with open(os.path.join(AQUI, "PIN"), encoding="utf-8") as f:
            pin = f.read().strip()
    except OSError:
        pass

    # A contagem do build ANTERIOR, lida antes de apagar a saida: perda de cor
    # e invisivel (609 itens continuam 609 enquanto as cores caem), e ja
    # aconteceu. O portao avisa quando um slot perde faixa.
    anterior: dict = {}
    marco = os.path.join(SAIDA, "contagem_de_cores.json")
    if os.path.isfile(marco):
        try:
            with open(marco, encoding="utf-8") as f:
                anterior = json.load(f)
        except (OSError, json.JSONDecodeError):
            anterior = {}

    if os.path.isdir(SAIDA):
        shutil.rmtree(SAIDA)
    os.makedirs(SAIDA, exist_ok=True)

    defs = ler_definitions()
    print(f"definitions lidas: {len(defs)}")

    creditos_csv = ler_creditos()
    metas_material = ler_metas_de_material()
    paletas_material = ler_paletas()
    canais_mudos: list[str] = []
    nomes_ptbr = ler_nomes_ptbr()
    rotulos_de_slot = ler_rotulos_de_slot()
    rotulos_de_cor = ler_rotulos_de_cor()
    sem_traducao: list[str] = []

    catalogo: list[dict] = []
    bytes_total = 0
    arquivos = 0
    contagem = Counter()
    # (slot, camada, corpo) -> [(variante, dirbase, cores)], preenchido na 1a
    # fase e resolvido na 2a, quando as pecas do slot viram um atlas so
    pendentes: dict[tuple[str, int, str], list[tuple]] = defaultdict(list)
    fora_gpl: list[str] = []
    sem_arte: list[str] = []
    autores: set[str] = set()
    licencas_vistas: Counter = Counter()

    for d in defs:
        licenca = licencas(d)
        # (f) peca cuja UNICA licenca e GPL fica fora: distribuir arte GPL exige
        # conformidade GPL para aquela arte, e a perda de acervo e minima.
        if licenca and licenca <= {"GPL 3.0", "GPL3.0", "GPL-3.0"}:
            fora_gpl.append(d.get("name") or d["_arquivo"])
            continue

        categoria = d["_categoria"]
        # (6b) o id vem do SLOT, nao da categoria: "Long Topknot" existe como
        # `hair` e como `ponytail`, e sob a categoria as duas colidiam -- no
        # catalogo e no atlas, onde uma sobrescrevia os PNGs da outra.
        item_id = f"{d['_slot']}/{slug(d.get('name', ''))}"
        entrada = {
            "id": item_id,
            "nome": d.get("name") or item_id,
            "categoria": categoria,
            # (6b) o slot decide exclusividade; o caminho so agrupa na UI
            "slot": d["_slot"],
            "caminho": d["_caminho"],
            "grupo": grupo_do_slot(d["_slot"]),
            "camadas": [],
        }
        # o nome em pt-BR e campo PROPRIO: o original continua disponivel como
        # fallback e para depurar id que dessincronizou depois de um rebuild
        if nomes_ptbr.get(item_id):
            entrada["nome_ptbr"] = nomes_ptbr[item_id]
        # (3a) um formato so de cor: o app nunca ve os dois do upstream
        canais = normalizar_recolors(d.get("recolors"), metas_material)
        if segue_cor_do_corpo(d):
            entrada["segue_cor_do_corpo"] = True

        alguma = False
        cores_da_arte: set = set()
        for ordem, camada in camadas(d):
            zpos = camada.get("zPos", 0)
            variantes: dict[str, dict] = {}
            for corpo in CORPOS:
                dirbase = camada.get(corpo)
                if not isinstance(dirbase, str) or not dirbase:
                    continue
                # que cores existem para esta camada/variante?
                cores: list[str | None] = []
                for anim in ANIMACOES:
                    achados = arquivos_da_animacao(dirbase, anim)
                    if achados:
                        cores = [c for c, _ in achados]
                        break
                # so e cor da peca a faixa que a peca declara -- o diretorio da
                # animacao guarda arquivo solto que nao e variante
                cores = faixas_declaradas(cores, d.get("variants"))
                if not cores:
                    continue

                atlas, mapa, por_cor = montar_atlas(dirbase, cores)
                if atlas is None:
                    continue
                cores_da_arte |= cores_de(atlas)
                # `arq` e o deslocamento final saem na 2a fase, quando as pecas
                # do mesmo slot viram um atlas so
                variante = {
                    "arq": None,
                    # `x` desloca a animacao na tira; `y` desloca a cor no atlas
                    "animacoes": [
                        {"nome": a, "frames": n, "x": x} for a, n, x in mapa
                    ],
                    "cores": por_cor,
                }
                variantes[corpo] = variante
                pendentes[(d["_slot"], ordem, corpo)].append(
                    (variante, dirbase, cores)
                )
                alguma = True

            if variantes:
                entrada["camadas"].append({
                    "ordem": ordem, "zPos": zpos, "corpos": variantes,
                })

        if not alguma:
            sem_arte.append(d["_arquivo"])
            continue

        # (bug 2) a cor listada tem de pintar. Canal cuja rampa de origem nao
        # aparece em pixel nenhum da arte oferece cor que nao muda nada.
        pintam = [c for c in canais if canal_pinta(c, cores_da_arte,
                                                   paletas_material)]
        for c in canais:
            if c not in pintam:
                canais_mudos.append(f"{item_id} [{c['nome']}] "
                                    f"{c['material']}.{c.get('base')}")
        if pintam:
            entrada["canais_de_cor"] = pintam

        for c in d.get("credits", []) or []:
            for a in c.get("authors", []) or []:
                autores.add(a)
            for l in c.get("licenses", []) or []:
                licencas_vistas[l] += 1

        # a celula da grade mostra a peca NO personagem; sem isto ela exibe o
        # boneco inalterado quando a peca nao cobre o corpo atual, e o preview
        # mente por omissao
        faltantes = sem_arte_em(entrada, CORPOS)
        if faltantes:
            entrada["sem_arte"] = faltantes

        # so conta como nao-traduzida a peca que ENTRA no catalogo: as 47
        # descartadas por falta de arte no recorte nunca chegam a tela
        if not entrada.get("nome_ptbr"):
            sem_traducao.append(item_id)

        catalogo.append(entrada)
        contagem[categoria] += 1

    # `combina_com`: trim/overlay/fivela pareados ao chapeu. Depois do laco
    # porque precisa do catalogo inteiro montado.
    ACESSORIOS_DE = {"hat": ("hat_trim", "hat_overlay", "hat_accessory",
                             "hat_buckle")}
    for principal, acessorios in ACESSORIOS_DE.items():
        pares = parear_por_prefixo(
            [i for i in catalogo if i["slot"] in acessorios],
            [i for i in catalogo if i["slot"] == principal],
        )
        for i in catalogo:
            if i["id"] in pares:
                i["combina_com"] = pares[i["id"]]

    # -- 2a fase: um atlas por (slot, camada, corpo) ---------------------------
    #
    # Um PNG por peca dava 2.800 arquivos -- e o precache do service worker so
    # ativa quando TODOS baixam, que e o cenario que a decisao 4 quer proteger.
    # Consolidar por slot custa ~28% de area em padding (a peca mais larga do
    # slot manda), mas o padding e transparente e o PNG o comprime a quase
    # nada. Com a UI de casas (5c), abrir um picker passa a ser 1 request.
    from PIL import Image

    for (slot, ordem, corpo), lista in sorted(pendentes.items()):
        tiras = [montar_atlas(db, cs)[0] for _, db, cs in lista]
        alturas = [t.size[1] for t in tiras]
        for n, grupo in enumerate(empacotar_por_teto(alturas)):
            largura = max(tiras[i].size[0] for i in grupo)
            atlas = Image.new(
                "RGBA", (largura, sum(alturas[i] for i in grupo)), (0, 0, 0, 0)
            )
            sufixo = "" if n == 0 else f"-{n}"
            rel = f"atlas/{slot}/L{ordem}/{corpo}{sufixo}.png"
            y = 0
            for i in grupo:
                atlas.alpha_composite(tiras[i], (0, y))
                variante = lista[i][0]
                variante["arq"] = rel
                # o offset da cor passa a ser absoluto dentro do atlas do slot
                variante["cores"] = {
                    c: base + y for c, base in variante["cores"].items()
                }
                y += alturas[i]
            bytes_total += salvar_paletizado(atlas, os.path.join(SAIDA, rel))
            arquivos += 1

    # paletas: o recolor do formato novo acontece no APP, nao aqui -- copiar
    # multiplica arquivo por cor e e exatamente o que o recorte evita.
    destino_paletas = os.path.join(SAIDA, "paletas")
    origem_paletas = os.path.join(FONTE, "palette_definitions")
    bytes_paletas = 0
    if os.path.isdir(origem_paletas):
        shutil.copytree(origem_paletas, destino_paletas, dirs_exist_ok=True)
        for base, _, arqs in os.walk(destino_paletas):
            for a in arqs:
                bytes_paletas += os.path.getsize(os.path.join(base, a))

    with open(os.path.join(SAIDA, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump({
            "pin": pin,
            "recorte": {
                "animacoes": ANIMACOES,
                "corpos": CORPOS,
                # `direcao` (singular) fica por compatibilidade: diz qual e a
                # direcao no endereco base, e continua sendo a frente.
                "direcao": "frente",
                "direcoes": [nome for nome, _linha in DIRECOES],
                "altura_do_frame": ALTURA,
                # o app anima por ciclo, nao em ordem crua
                "ciclos": CICLOS,
                "fps": FPS,
            },
            # (6b) mapa de navegacao: prioridade e rotulo por diretorio
            "grupos": ler_grupos(os.path.join(FONTE, "sheet_definitions")),
            # a casa mostrava o slot cru (`facial_eyes`); o rotulo e o que o
            # jogador le
            "slots": rotulos_de_slot,
            # nome cru da cor -> rotulo em pt-BR, para os dois mundos (rampa de
            # paleta e faixa de atlas). Chave sobrando nao custa nada; chave
            # faltando deixa rotulo cru na tela.
            "cores": rotulos_de_cor,
            "itens": catalogo,
        }, f, ensure_ascii=False, separators=(",", ":"))

    with open(os.path.join(SAIDA, "creditos.json"), "w", encoding="utf-8") as f:
        json.dump({
            "fonte": "Liberated Pixel Cup -- Universal LPC Spritesheet",
            "pin": pin,
            "url": "https://github.com/LiberatedPixelCup/"
                   "Universal-LPC-Spritesheet-Character-Generator",
            "autores": sorted(autores),
            "licencas": dict(licencas_vistas.most_common()),
            "linhas_do_credits_csv": len(creditos_csv),
        }, f, ensure_ascii=False, indent=1)

    # -- portao das cores ------------------------------------------------------
    #
    # Contagem de faixas de atlas por slot, comparada com o build anterior.
    agora: dict[str, int] = {}
    for i in catalogo:
        faixas = {
            c
            for cam in i["camadas"]
            for v in cam["corpos"].values()
            for c in v["cores"]
            if c != "base"
        }
        agora[i["slot"]] = agora.get(i["slot"], 0) + len(faixas)
    quedas = [
        (k, anterior[k], agora.get(k, 0))
        for k in sorted(anterior)
        if agora.get(k, 0) < anterior[k]
    ]
    with open(marco, "w", encoding="utf-8") as f:
        json.dump(agora, f, ensure_ascii=False, indent=1, sort_keys=True)
    if quedas:
        print("\n  ! CORES A MENOS que no build anterior:")
        for k, a, d in quedas:
            print(f"    {k}: {a} -> {d}")

    tam_cat = os.path.getsize(os.path.join(SAIDA, "catalogo.json"))
    total = bytes_total + bytes_paletas + tam_cat

    linhas = [
        "# Acervo do avatar -- relatorio de build", "",
        f"Pin da fonte: `{pin}`", "",
        "## Recorte", "",
        f"- animacoes: {', '.join(ANIMACOES)}",
        f"- variantes de corpo: {', '.join(CORPOS)}",
        "- direcao: frente (linha 2 de 4 da folha do LPC)", "",
        "## Peso", "",
        "| artefato | arquivos | MB |",
        "|---|---|---|",
        f"| atlas | {arquivos} | {bytes_total / 1e6:.2f} |",
        f"| paletas | - | {bytes_paletas / 1e6:.2f} |",
        f"| catalogo.json | 1 | {tam_cat / 1e6:.2f} |",
        f"| **total** | **{arquivos + 1}** | **{total / 1e6:.2f}** |", "",
        "## Itens por categoria", "",
        "| categoria | itens |", "|---|---|",
    ]
    for k, v in contagem.most_common():
        linhas.append(f"| {k} | {v} |")
    linhas += [
        "", f"Total de itens no catalogo: **{len(catalogo)}**", "",
        "## Excluidos", "",
        f"- por licenca GPL-only: **{len(fora_gpl)}**",
        f"- sem arte no recorte: **{len(sem_arte)}**",
        # canal cuja rampa de origem nao aparece em pixel nenhum da arte: ele
        # oferecia cor que nao pintava
        f"- canais de cor mudos (nao pintam nada): **{len(canais_mudos)}**", "",
        "## Cores por slot (faixas do atlas)", "",
        "| slot | faixas | antes |", "|---|---|---|",
    ]
    for k in sorted(agora):
        linhas.append(f"| {k} | {agora[k]} | {anterior.get(k, '-')} |")
    linhas += [
        "", f"Total de faixas: **{sum(agora.values())}**"
        + (f" (antes: {sum(anterior.values())})" if anterior else ""), "",
        "## Traducao", "",
        f"- itens com nome em pt-BR: **{len(catalogo) - len(sem_traducao)}**",
        f"- itens SEM traducao (ficam com o nome original): "
        f"**{len(sem_traducao)}**",
        f"- slots com rotulo em pt-BR: **{len(rotulos_de_slot)}**", "",
    ]
    if sem_traducao:
        linhas += ["<details><summary>sem traducao</summary>", ""]
        linhas += [f"- `{n}`" for n in sorted(sem_traducao)]
        linhas += ["", "</details>", ""]
    if canais_mudos:
        linhas += ["<details><summary>canais mudos</summary>", ""]
        linhas += [f"- `{n}`" for n in sorted(canais_mudos)]
        linhas += ["", "</details>", ""]
    if fora_gpl:
        linhas += ["<details><summary>GPL-only</summary>", ""]
        linhas += [f"- {n}" for n in sorted(fora_gpl)]
        linhas += ["", "</details>", ""]
    with open(os.path.join(SAIDA, "relatorio.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))

    print(f"\nitens no catalogo: {len(catalogo)}")
    print(f"atlas: {arquivos} arquivos, {bytes_total / 1e6:.2f} MB")
    print(f"paletas: {bytes_paletas / 1e6:.2f} MB | catalogo: {tam_cat / 1e6:.2f} MB")
    print(f"TOTAL: {total / 1e6:.2f} MB")
    print(f"excluidos: {len(fora_gpl)} GPL-only, {len(sem_arte)} sem arte")
    print(f"canais de cor mudos: {len(canais_mudos)}")
    print(f"itens sem nome pt-BR: {len(sem_traducao)} de {len(catalogo)}")
    print(f"relatorio: {os.path.relpath(os.path.join(SAIDA, 'relatorio.md'), AQUI)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
