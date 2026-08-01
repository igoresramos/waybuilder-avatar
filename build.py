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
  b2. recorta as variantes de corpo: child, muscular, skeleton e zombie ficam
     fora. Entram male, female, pregnant, teen.
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
CORPOS = ["male", "female", "pregnant", "teen"]

# a folha empilha 4 direcoes em linhas de 64px; a de frente e a TERCEIRA.
# Verificado compondo body+head e olhando: linha 0 nao tem olhos (costas),
# 1 e 3 sao perfis, 2 encara. Errar aqui poe o acervo inteiro de costas.
ALTURA = 64
LINHA_DA_FRENTE = 2

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
    "Cabeca": ("head", "ears", "ears_inner", "furry_ears", "furry_ears_skin",
               "nose"),
    "Rosto": ("eyes", "facial_eyes", "expression", "expression_crying",
              "eyebrows", "beard", "mustache", "facial_mask", "facial_left",
              "facial_left_trim", "facial_right", "facial_right_trim"),
    "Cabelo": ("hair", "hairextl", "hairextr", "ponytail", "updo", "hairtie",
               "hairtie_rune"),
    "Chapeu": ("hat", "hat_trim", "hat_overlay", "hat_accessory", "hat_buckle",
               "headcover", "headcover_rune", "bandana", "bandana_overlay",
               "visor"),
    "Torso": ("clothes", "jacket", "jacket_trim", "jacket_collar",
              "jacket_pockets", "vest", "dress", "dress_trim", "dress_sleeves",
              "dress_sleeves_trim", "sleeves", "apron", "overalls", "sash",
              "sash_tie", "cargo", "chainmail"),
    "Pernas e pes": ("legs", "shoes", "shoes_toe", "socks"),
    "Armadura": ("armour", "bauldron", "bracers", "gloves", "wrists",
                 "shoulders", "arms", "belt", "buckles"),
    "Acessorios": ("neck", "necklace", "charm", "earrings", "earring_left",
                   "earring_right", "ring", "accessory", "cape", "cape_trim",
                   "backpack", "backpack_straps", "quiver"),
    "Armas": ("weapon", "weapon_magic_crystal", "ammo", "shield",
              "shield_pattern", "shield_trim", "shield_paint"),
}

_DE_SLOT = {s: g for g, ss in GRUPO_DE_SLOT.items() for s in ss}


def grupo_do_slot(slot: str) -> str:
    return _DE_SLOT.get(slot, "Outros")


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
    novo = os.path.join(d, f"{anim}.png")
    if os.path.isfile(novo):
        return [(None, novo)]
    subdir = os.path.join(d, anim)
    if os.path.isdir(subdir):
        return [
            (a[:-4], os.path.join(subdir, a))
            for a in sorted(os.listdir(subdir))
            if a.endswith(".png")
        ]
    return []


# -- composicao --------------------------------------------------------------

def recortar_frente(im, largura_alvo: int):
    """A linha da frente da folha, em largura fixa (sobra vira transparente)."""
    from PIL import Image

    y = LINHA_DA_FRENTE * ALTURA
    if im.size[1] < y + ALTURA:
        return None  # folha sem a linha da frente (fora do layout universal)
    faixa = im.crop((0, y, im.size[0], y + ALTURA))
    if faixa.size[0] == largura_alvo:
        return faixa
    tela = Image.new("RGBA", (largura_alvo, ALTURA), (0, 0, 0, 0))
    tela.alpha_composite(faixa.crop((0, 0, min(faixa.size[0], largura_alvo), ALTURA)))
    return tela


def salvar_paletizado(im, destino: str) -> int:
    """PNG indexado quando cabe em 256 cores -- ~15% do acervo vem em RGBA."""
    from PIL import Image

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    cores = im.getcolors(maxcolors=256)
    saida = im
    if cores is not None:
        saida = im.convert("P", palette=Image.ADAPTIVE, colors=max(2, len(cores)))
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

    largura = sum(im.size[0] for _, im in faixas)
    tira = Image.new("RGBA", (largura, ALTURA), (0, 0, 0, 0))
    mapa = []
    x = 0
    for anim, im in faixas:
        faixa = recortar_frente(im, im.size[0])
        if faixa is None:
            continue
        tira.alpha_composite(faixa, (x, 0))
        mapa.append((anim, im.size[0] // ALTURA, x))
        x += im.size[0]
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

    if os.path.isdir(SAIDA):
        shutil.rmtree(SAIDA)
    os.makedirs(SAIDA, exist_ok=True)

    defs = ler_definitions()
    print(f"definitions lidas: {len(defs)}")

    creditos_csv = ler_creditos()

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
        if isinstance(d.get("recolors"), dict):
            entrada["recolors"] = d["recolors"]

        alguma = False
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
                if not cores:
                    continue

                atlas, mapa, por_cor = montar_atlas(dirbase, cores)
                if atlas is None:
                    continue
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
                "direcao": "frente",
                "altura_do_frame": ALTURA,
            },
            # (6b) mapa de navegacao: prioridade e rotulo por diretorio
            "grupos": ler_grupos(os.path.join(FONTE, "sheet_definitions")),
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
        f"- sem arte no recorte: **{len(sem_arte)}**", "",
    ]
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
    print(f"relatorio: {os.path.relpath(os.path.join(SAIDA, 'relatorio.md'), AQUI)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
