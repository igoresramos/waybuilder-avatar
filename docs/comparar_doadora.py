"""Mostra, em imagem, o que os numeros da doadora analoga querem dizer.

O relatorio `2026-08-02_doadora-analoga.md` diz que o transplante corta o erro
em 62% e mesmo assim quase nao produz frame perfeito. Numero nao comunica isso.
Esta figura poe lado a lado, ampliado, o que entra, o que devia sair, o que sai,
e onde erra -- com os pixels errados em vermelho.

Uso:
    python3 docs/comparar_doadora.py
"""
import json
import os
import sys

import numpy as np
from PIL import Image

TRABALHO = sys.argv[1] if len(sys.argv) > 1 else (
    "/tmp/claude-1000/-mnt-c-Users-igor0/"
    "a5bbdb2b-727f-450d-884b-be2bcd2c2f13/scratchpad/work"
)
SAIDA = os.path.join(os.path.dirname(__file__), "2026-08-02_doadora-analoga.png")

ZOOM = 5
FUNDO = (24, 26, 30)
GRADE = (60, 66, 78)
ERRO = (255, 60, 60)

# um caso de cada tipo, escolhido pelos registros do experimento
CASOS = [
    ("armour/legion", "Armadura Legionaria -- o exemplo pedido"),
    ("clothes/longsleeve-polo", "Manga Longa Polo -- doadora de silhueta identica"),
    ("bandana/bandana", "Bandana -- uma das 5 que ficaram perfeitas"),
]

sys.path.insert(0, TRABALHO)
from field_lib import apply_field, build_field  # noqa: E402

itens = {i["id"]: i for i in json.load(open(f"{TRABALHO}/items.json"))}
registros = {r["id"]: r for r in json.load(open(f"{TRABALHO}/exp234_records.json"))}
RAIZ = "/home/igor0/waybuilder/app/public/avatar/"


def quadro(item, anim, k):
    # `items.json` ja guarda o caminho absoluto; RAIZ so completa se for relativo
    arq = item["arq"]
    im = np.array(Image.open(arq if os.path.isabs(arq) else RAIZ + arq).convert("RGBA"))
    x = item["x"][anim] + k * 64
    return im[item["y"]:item["y"] + 64, x:x + 64, :]


def ampliar(arr):
    return np.kron(arr, np.ones((ZOOM, ZOOM, 1), dtype=arr.dtype))


def sobre_fundo(arr):
    """Achata RGBA sobre o fundo do app -- alpha nao aparece em PNG opaco."""
    a = arr[..., 3:4] / 255.0
    return (arr[..., :3] * a + np.array(FUNDO) * (1 - a)).astype(np.uint8)


painel = []
for alvo, titulo in CASOS:
    it, reg = itens[alvo], registros[alvo]
    doadora = itens[reg["donor"]]
    # o par com movimento real: walk k=0 -> idle k=1. Em k=0 as duas poses sao
    # identicas em varias pecas, e o transplante pareceria perfeito por acidente
    campo, _, _ = build_field(quadro(doadora, "walk", 0), quadro(doadora, "idle", 1))
    entrada = quadro(it, "walk", 0)
    real = quadro(it, "idle", 1)
    saiu = apply_field(campo, entrada)

    errados = np.any(saiu != real, axis=-1)
    mapa = sobre_fundo(real).copy()
    mapa[errados] = ERRO
    print(f"{alvo:32s} doadora={reg['donor']:32s} "
          f"erro {reg['baseline_k1']:4d} -> {int(errados.sum()):4d} px "
          f"(de {reg['n_opaque']} opacos)")
    painel.append((titulo, reg, int(errados.sum()),
                   [ampliar(sobre_fundo(x)) for x in (entrada, real, saiu)]
                   + [ampliar(mapa)]))

L = 64 * ZOOM
MARGEM, TOPO, ENTRE = 14, 46, 30
larg = MARGEM * 2 + L * 4 + ENTRE * 3
alt = TOPO + (L + TOPO) * len(painel) + MARGEM
tela = np.full((alt, larg, 3), FUNDO, dtype=np.uint8)

for lin, (_titulo, _reg, _err, imgs) in enumerate(painel):
    y = TOPO + lin * (L + TOPO)
    for col, img in enumerate(imgs):
        x = MARGEM + col * (L + ENTRE)
        tela[y:y + L, x:x + L] = img
        tela[y - 1, x - 1:x + L + 1] = GRADE
        tela[y + L, x - 1:x + L + 1] = GRADE
        tela[y - 1:y + L + 1, x - 1] = GRADE
        tela[y - 1:y + L + 1, x + L] = GRADE

Image.fromarray(tela).save(SAIDA)
print("\nfigura:", SAIDA)
print("colunas: 1 entrada (walk) | 2 alvo real (idle) | 3 gerado | 4 erro em vermelho")
for titulo, reg, err, _ in painel:
    print(f"  {titulo}: {reg['baseline_k1']} -> {err} px errados "
          f"de {reg['n_opaque']} da peca")
