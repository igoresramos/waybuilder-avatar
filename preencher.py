"""Preenche as animacoes que faltam no acervo -- spec, decisao 11.

Varre o catalogo, acha cada par (peca, animacao que falta, corpo) e gera os
frames por transplante de peca analoga. Nada aqui e IA: o campo de
deslocamento sai de duas poses da doadora e move os pixels que a ALVO ja tem.

Uso:
    python3 preencher.py [--limite N] [--saida DIR]

Emite `DIR/frames/<id>/<corpo>/<animacao>.png` (uma tira horizontal por
animacao) e `DIR/preenchimento.json` com a procedencia de cada lacuna, que e o
que permite a tela dizer o que e sintetico e o dia de amanha trocar por arte de
verdade com um diff.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

from transplante import (
    aplicar_campo,
    campo_de_deslocamento,
    pixels_diferentes,
    sobreposicao,
)

RAIZ = "/home/igor0/waybuilder/app/public/avatar/"
Q = 64

# Quantos frames DISTINTOS cada animacao tem. O ciclo repete alguns (`idle` toca
# 0-0-1-1), mas a arte e so a lista abaixo.
DISTINTOS = {"idle": 2, "combat_idle": 2, "walk": 8, "sit": 3, "run": 8}


def carregar(caminho: str, _cache: dict = {}) -> np.ndarray:
    if caminho not in _cache:
        _cache[caminho] = np.array(Image.open(RAIZ + caminho).convert("RGBA"))
    return _cache[caminho]


def variante(item: dict, corpo: str, camada: int = 0):
    camadas = item["camadas"]
    if camada >= len(camadas):
        return None
    return camadas[camada]["corpos"].get(corpo)


def animacoes(v: dict) -> set[str]:
    return {a["nome"] for a in v["animacoes"]}


def quadro(v: dict, anim: str, k: int = 0):
    """Um frame de 64x64, ou `None` se a peca nao tem aquela animacao."""
    a = next((x for x in v["animacoes"] if x["nome"] == anim), None)
    if a is None:
        return None
    # a faixa `base` e a arte crua; pecas com cores embutidas usam a primeira
    y = v["cores"].get("base", next(iter(v["cores"].values())))
    x = a["x"] + min(k, a["frames"] - 1) * Q
    return carregar(v["arq"])[y:y + Q, x:x + Q, :]


def achar_doadora(alvo_v, tem, falta, candidatos, corpo, camada):
    """A peca mais parecida que sabe fazer a animacao que falta.

    Precisa de DUAS coisas: a animacao que falta -- senao nao tem o que ensinar
    -- e alguma animacao em comum com a alvo, que e onde as duas poses sao
    comparadas. A escolha e por sobreposicao de silhueta, e o empate cai no id
    para o build nao depender da ordem do diretorio.
    """
    comum = sorted(tem)[0]
    base = quadro(alvo_v, comum)
    melhor, melhor_s = None, 0.0
    for outro in candidatos:
        vo = variante(outro, corpo, camada)
        if vo is None:
            continue
        an = animacoes(vo)
        if falta not in an or comum not in an:
            continue
        s = sobreposicao(base, quadro(vo, comum))
        if s > melhor_s or (s == melhor_s and s > 0 and melhor is not None
                            and outro["id"] < melhor["id"]):
            melhor, melhor_s = outro, s
    return melhor, melhor_s, comum


def gerar(alvo_v, doadora_v, falta, comum):
    """Os frames da animacao que falta, na ordem, para a peca alvo."""
    partida = quadro(alvo_v, comum)
    saida = []
    for k in range(DISTINTOS[falta]):
        destino = quadro(doadora_v, falta, k)
        origem = quadro(doadora_v, comum)
        campo, silhueta = campo_de_deslocamento(origem, destino)
        saida.append(aplicar_campo(campo, partida, silhueta))
    return saida


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--limite", type=int, default=0, help="para depurar")
    p.add_argument("--saida", default="preenchimento")
    args = p.parse_args()

    cat = json.load(open(RAIZ + "catalogo.json"))
    anims_do_recorte = cat["recorte"]["animacoes"]
    corpos = cat["recorte"]["corpos"]
    os.makedirs(os.path.join(args.saida, "frames"), exist_ok=True)

    registro: list[dict] = []
    conta = Counter()
    n = 0

    for corpo in corpos:
        presentes = [i for i in cat["itens"] if variante(i, corpo)]
        corpo_base = next((i for i in presentes if i["id"] == "body/body-color"), None)
        for alvo in presentes:
            for c in range(len(alvo["camadas"])):
                av = variante(alvo, corpo, c)
                if av is None:
                    continue
                tem = animacoes(av)
                if not tem:
                    continue
                for falta in sorted(set(anims_do_recorte) - tem):
                    doadora, iou, comum = achar_doadora(
                        av, tem, falta, presentes, corpo, c)
                    via = "analoga"
                    if doadora is None and corpo_base is not None:
                        cv = variante(corpo_base, corpo, 0)
                        if cv and {falta, comum} <= animacoes(cv):
                            doadora, iou, via = corpo_base, 0.0, "corpo"
                    if doadora is None:
                        conta["sem saida"] += 1
                        continue
                    dv = variante(doadora, corpo, 0 if via == "corpo" else c)
                    if dv is None or not {falta, comum} <= animacoes(dv):
                        conta["sem saida"] += 1
                        continue

                    frames = gerar(av, dv, falta, comum)
                    tira = np.concatenate(frames, axis=1)
                    destino = os.path.join(
                        args.saida, "frames", alvo["id"].replace("/", "__"),
                        corpo, f"c{c}")
                    os.makedirs(destino, exist_ok=True)
                    Image.fromarray(tira).save(os.path.join(destino, f"{falta}.png"))

                    registro.append({
                        "id": alvo["id"], "corpo": corpo, "camada": c,
                        "animacao": falta, "doadora": doadora["id"],
                        "via": via, "iou": round(iou, 3),
                        "partiu_de": comum, "frames": len(frames),
                    })
                    conta[via] += 1
                    n += 1
                    if args.limite and n >= args.limite:
                        break
                if args.limite and n >= args.limite:
                    break
            if args.limite and n >= args.limite:
                break
        if args.limite and n >= args.limite:
            break

    json.dump({"lacunas": registro, "resumo": dict(conta)},
              open(os.path.join(args.saida, "preenchimento.json"), "w"),
              ensure_ascii=False, indent=1)
    print(f"lacunas preenchidas: {n}")
    for k, v in conta.most_common():
        print(f"   {k:12s} {v:5d}")
    pecas = len({r['id'] for r in registro})
    print(f"pecas atingidas: {pecas}")
    print(f"frames gerados: {sum(r['frames'] for r in registro)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
