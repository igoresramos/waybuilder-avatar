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

Rode: python3 avatar/build.py
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

def ler_definitions() -> list[dict]:
    """Os 768 JSONs, com a categoria vinda do CAMINHO, nao do conteudo."""
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
        item_id = f"{categoria}/{slug(d.get('name', ''))}"
        entrada = {
            "id": item_id,
            "nome": d.get("name") or item_id,
            "categoria": categoria,
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
                rel = os.path.join(
                    "atlas", categoria, slug(d.get("name", "")),
                    f"L{ordem}", f"{corpo}.png",
                )
                bytes_total += salvar_paletizado(atlas, os.path.join(SAIDA, rel))
                arquivos += 1
                variantes[corpo] = {
                    "arq": rel.replace(os.sep, "/"),
                    # `x` desloca a animacao na tira; `y` desloca a cor no atlas
                    "animacoes": [
                        {"nome": a, "frames": n, "x": x} for a, n, x in mapa
                    ],
                    "cores": por_cor,
                }
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

        catalogo.append(entrada)
        contagem[categoria] += 1

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
