#!/usr/bin/env python3
"""Monta a fila de revisao visual das animacoes geradas -- spec, decisao 11.

O `preencher.py` gera arte APROXIMADA para as lacunas do acervo, e a pesquisa
de 2026-08-02 mediu que ela varia de "exata" a "ruido": a translacao rigida
acerta quase sempre onde vale, o transplante quase nunca sai exato, e o
preditor automatico de qualidade FALHOU (50,5% contra o criterio de 70%). Sem
gate automatico, quem separa o que presta e o olho do dono.

Este passo prepara essa revisao: varre o que foi gerado, mede os sinais que o
juizo visual apontou como preditores de "feio" e emite
`preenchimento/revisao.html`, onde cada peca aparece ANIMADA ao lado da arte de
partida, com aceitar/rejeitar.

A ordem da fila e do MELHOR para o pior, de proposito: assim o dono aceita os
bons depressa e, quando comecar a rejeitar em sequencia, sabe que dali para
baixo so piora -- e pode parar. O que ele nao revisar fica de fora do build,
que e o lado seguro.

Uso:
    python3 revisao.py [--saida preenchimento/revisao.html]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ_ACERVO = "/home/igor0/waybuilder/app/public/avatar/"
Q = 64


def componentes(mascara: np.ndarray) -> tuple[int, int]:
    """(quantidade de ilhas, tamanho da maior) -- rotulagem por varredura.

    Fragmentacao foi o defeito MAIS feio segundo o juizo visual: a peca se
    parte em pedacos soltos e o olho rejeita na hora, mesmo com poucos pixels
    errados. numpy puro, sem scipy.
    """
    h, w = mascara.shape
    rot = np.zeros((h, w), dtype=np.int32)
    atual = 0
    tamanhos = []
    for y0 in range(h):
        for x0 in range(w):
            if not mascara[y0, x0] or rot[y0, x0]:
                continue
            atual += 1
            pilha = [(y0, x0)]
            rot[y0, x0] = atual
            n = 0
            while pilha:
                y, x = pilha.pop()
                n += 1
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and mascara[ny, nx] and not rot[ny, nx]:
                        rot[ny, nx] = atual
                        pilha.append((ny, nx))
            tamanhos.append(n)
    return (len(tamanhos), max(tamanhos) if tamanhos else 0)


def caixa(mascara: np.ndarray) -> tuple[int, int]:
    """(altura, largura) da caixa que envolve a peca."""
    ys, xs = np.nonzero(mascara)
    if len(ys) == 0:
        return (0, 0)
    return (int(ys.max() - ys.min() + 1), int(xs.max() - xs.min() + 1))


def sinais(partida: np.ndarray, gerado: np.ndarray) -> dict:
    """Os tres sinais que o juizo visual elegeu, todos sem gabarito.

    Nenhum depende de conhecer a arte "certa" -- que nas lacunas reais nao
    existe. Ver `docs/2026-08-02_pesquisa-juizo-visual.md`.
    """
    mp, mg = partida[..., 3] > 0, gerado[..., 3] > 0
    _, maior_p = componentes(mp)
    n_g, maior_g = componentes(mg)
    hp, wp = caixa(mp)
    hg, wg = caixa(mg)
    return {
        # < 0,75 foi inaceitavel nos tres piores casos julgados
        "razao_componente": round(maior_g / maior_p, 3) if maior_p else 0.0,
        "ilhas": n_g,
        # queda de altura/largura acima de 15-20% = amputacao de ponta
        "queda_bbox": round(1 - min(hg / hp if hp else 1, wg / wp if wp else 1), 3),
        "area_partida": int(mp.sum()),
        "area_gerada": int(mg.sum()),
    }


def nota(s: dict) -> float:
    """Quanto MAIOR, melhor. So ordena a fila -- nao decide nada."""
    return (min(s["razao_componente"], 1.0) * 2
            - max(0.0, s["queda_bbox"]) * 2
            - max(0, s["ilhas"] - 1) * 0.15)


def quadro_de_partida(cat: dict, item_id: str, corpo: str, camada: int):
    """O `walk` k=0 da peca: e dele que a geracao parte, e o ponto de comparacao."""
    it = next((i for i in cat["itens"] if i["id"] == item_id), None)
    if it is None or camada >= len(it["camadas"]):
        return None
    v = it["camadas"][camada]["corpos"].get(corpo)
    if not v:
        return None
    a = next((x for x in v["animacoes"] if x["nome"] == "walk"), None)
    if a is None:
        return None
    y = v["cores"].get("base", next(iter(v["cores"].values())))
    im = np.array(Image.open(RAIZ_ACERVO + v["arq"]).convert("RGBA"))
    return im[y:y + Q, a["x"]:a["x"] + Q]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dir", default="preenchimento")
    p.add_argument("--saida", default=None)
    args = p.parse_args()
    base = os.path.join(AQUI, args.dir)
    saida = args.saida or os.path.join(base, "revisao.html")

    reg = json.load(open(os.path.join(base, "preenchimento.json")))
    cat = json.load(open(RAIZ_ACERVO + "catalogo.json"))
    nome_de = {i["id"]: (i.get("nome_ptbr") or i["nome"]) for i in cat["itens"]}
    slot_de = {i["id"]: i.get("slot", "?") for i in cat["itens"]}

    # Uma decisao por (peca, animacao, camada), nao por celula: o dono nao vai
    # julgar a mesma arte seis vezes, uma por corpo. Escolhemos o corpo `male`
    # quando existe -- e o que ele ve ao abrir o app. A CAMADA entra na chave
    # porque uma peca pode ter tratamento diferente por camada: nas asas, a de
    # tras foi transladada e a da frente nao foi tocada.
    #
    # `nao mexer` fica FORA da fila: nao ha arte nova para julgar. O quadro
    # gerado e o proprio `walk` k=0 repetido, que e exatamente o que a peca ja
    # mostra hoje pela decisao 12 -- pedir uma decisao ali seria pedir para
    # aprovar o que ja esta no ar.
    por_chave: dict[tuple[str, str, int], list[dict]] = defaultdict(list)
    for r in reg["lacunas"]:
        if r["via"] == "nao mexer":
            continue
        por_chave[(r["id"], r["animacao"], r["camada"])].append(r)

    fila = []
    for (item_id, anim, camada), regs in sorted(por_chave.items()):
        r = next((x for x in regs if x["corpo"] == "male"), regs[0])
        tira_rel = os.path.join(
            "frames", item_id.replace("/", "__"), r["corpo"], f"c{r['camada']}",
            f"{anim}.png")
        caminho = os.path.join(base, tira_rel)
        if not os.path.isfile(caminho):
            continue
        tira = np.array(Image.open(caminho).convert("RGBA"))
        partida = quadro_de_partida(cat, item_id, r["corpo"], r["camada"])
        if partida is None:
            continue
        # O quadro de "hoje" tem de vir do ATLAS, nao da tira gerada. Em `idle`
        # os dois coincidem (o k=0 e copia do `walk`), mas em `run` e
        # `combat_idle` o frame 0 ja e gerado -- comparar a arte nova com ela
        # mesma faria a tela mentir justamente onde o risco e maior.
        dir_part = os.path.join(base, "partida")
        os.makedirs(dir_part, exist_ok=True)
        rel_part = f"partida/{item_id.replace('/', '__')}__{r['corpo']}__c{camada}.png"
        cam_part = os.path.join(base, rel_part)
        if not os.path.isfile(cam_part):
            Image.fromarray(partida).save(cam_part)
        s = sinais(partida, tira[:, 0:Q])
        fila.append({
            "id": item_id,
            "nome": nome_de.get(item_id, item_id),
            "slot": slot_de.get(item_id, "?"),
            "animacao": anim,
            "corpo": r["corpo"],
            "camada": r["camada"],
            "via": r["via"],
            "doadora": r.get("doadora"),
            "corpos": sorted({x["corpo"] for x in regs}),
            "celulas": len(regs),
            "tira": tira_rel.replace(os.sep, "/"),
            "partida": rel_part,
            "frames": tira.shape[1] // Q,
            "sinais": s,
            "nota": round(nota(s), 3),
        })

    # translacao primeiro (zero regressao medida), depois transplante do melhor
    # para o pior -- ver o cabecalho
    ordem = {"transladar": 0, "analoga": 1, "corpo": 2}
    fila.sort(key=lambda f: (ordem.get(f["via"], 9), -f["nota"]))

    html = MOLDE.replace("__DADOS__", json.dumps(fila, ensure_ascii=False))
    html = html.replace("__PIN__", cat.get("pin", "?")[:8])
    with open(saida, "w") as f:
        f.write(html)

    vias = defaultdict(int)
    for f in fila:
        vias[f["via"]] += 1
    print(f"fila de revisao: {len(fila)} decisoes (de {len(reg['lacunas'])} celulas)")
    for k, v in sorted(vias.items(), key=lambda kv: -kv[1]):
        print(f"   {k:12s} {v:4d}")
    print(f"-> {saida}")
    return 0


MOLDE = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Revisao das animacoes geradas -- Waybuilder</title>
<style>
  :root {
    --fundo:#16181d; --card:#1e2128; --borda:#2c3039; --texto:#e6e8ec;
    --fraco:#9aa0ab; --ok:#3fb950; --nao:#f85149; --accent:#58a6ff;
  }
  * { box-sizing:border-box }
  body { margin:0; background:var(--fundo); color:var(--texto);
         font:15px/1.5 system-ui, sans-serif; }
  header { position:sticky; top:0; background:var(--fundo); z-index:5;
           border-bottom:1px solid var(--borda); padding:12px 20px;
           display:flex; gap:20px; align-items:center; flex-wrap:wrap }
  h1 { font-size:1.05em; margin:0; font-weight:600 }
  .barra { flex:1; height:6px; background:var(--borda); border-radius:3px;
           overflow:hidden; min-width:120px }
  .barra i { display:block; height:100%; background:var(--ok); width:0 }
  .conta { color:var(--fraco); font-size:.85em; font-variant-numeric:tabular-nums }
  main { max-width:900px; margin:0 auto; padding:24px 20px 120px }
  .palco { display:flex; gap:32px; align-items:center; justify-content:center;
           background:var(--card); border:1px solid var(--borda);
           border-radius:10px; padding:28px; margin-bottom:16px }
  .peca { text-align:center }
  .peca h2 { font-size:.75em; color:var(--fraco); font-weight:500;
             text-transform:uppercase; letter-spacing:.05em; margin:0 0 10px }
  .quadro { width:256px; height:256px; image-rendering:pixelated;
            background:#0e1013 center/cover; border-radius:6px }
  .anima { animation:tocar var(--dur) steps(var(--n)) infinite }
  @keyframes tocar { from{background-position-x:0}
                     to{background-position-x:calc(-256px * var(--n))} }
  @media (prefers-reduced-motion: reduce) { .anima { animation:none } }
  .info { text-align:center; margin-bottom:20px }
  .info b { font-size:1.15em }
  .tags { display:flex; gap:8px; justify-content:center; flex-wrap:wrap;
          margin-top:8px; font-size:.8em; color:var(--fraco) }
  .tag { background:var(--card); border:1px solid var(--borda);
         padding:2px 9px; border-radius:99px }
  .tag.via-transladar { border-color:var(--ok); color:var(--ok) }
  .tag.alerta { border-color:var(--nao); color:var(--nao) }
  .acoes { display:flex; gap:12px; justify-content:center; margin:24px 0 }
  button { font:inherit; cursor:pointer; border-radius:8px; padding:11px 26px;
           border:1px solid var(--borda); background:var(--card); color:var(--texto) }
  button:hover { border-color:var(--accent) }
  .sim { border-color:var(--ok); color:var(--ok); font-weight:600 }
  .nao { border-color:var(--nao); color:var(--nao); font-weight:600 }
  .dica { text-align:center; color:var(--fraco); font-size:.8em }
  .fim { background:var(--card); border:1px solid var(--borda); border-radius:10px;
         padding:24px; margin-top:24px }
  textarea { width:100%; height:150px; background:#0e1013; color:var(--texto);
             border:1px solid var(--borda); border-radius:6px; padding:12px;
             font-family:ui-monospace, monospace; font-size:12px }
  .oculto { display:none }
</style></head><body>
<header>
  <h1>Revisao das animacoes geradas</h1>
  <div class="barra"><i id="prog"></i></div>
  <span class="conta" id="conta"></span>
  <button id="btFim" style="padding:6px 14px;font-size:.85em">Ver resultado</button>
</header>
<main>
  <div id="tela">
    <div class="info">
      <b id="nome"></b>
      <div class="tags" id="tags"></div>
    </div>
    <div class="palco">
      <div class="peca"><h2>hoje (parada)</h2>
        <div class="quadro" id="antes"></div></div>
      <div class="peca"><h2>gerada <span id="anim"></span></h2>
        <div class="quadro anima" id="depois"></div></div>
    </div>
    <div class="acoes">
      <button class="nao" id="btNao">Rejeitar (N)</button>
      <button id="btPular">Pular (espaco)</button>
      <button class="sim" id="btSim">Aceitar (S)</button>
    </div>
    <p class="dica">A da esquerda e o que o jogador ve HOJE: a peca travada no
      primeiro quadro. A da direita e a gerada, rodando a 8 quadros por segundo.<br>
      Setas para voltar. O que voce nao revisar fica FORA do build.</p>
  </div>

  <div class="fim oculto" id="fim">
    <h2 style="margin-top:0">Resultado</h2>
    <p id="resumo" class="conta"></p>
    <p class="dica" style="text-align:left">Copie o bloco abaixo e cole na
      conversa com o Claude. Ele contem so os IDs e as decisoes.</p>
    <textarea id="saida" readonly></textarea>
    <div class="acoes">
      <button id="btCopiar" class="sim">Copiar</button>
      <button id="btVoltar">Voltar a revisar</button>
    </div>
  </div>
</main>
<script>
const FILA = __DADOS__;
const PIN = "__PIN__";
const CHAVE = "waybuilder-revisao-" + PIN;
let i = 0;
const dec = JSON.parse(localStorage.getItem(CHAVE) || "{}");
const chaveDe = (f) => f.id + "|" + f.animacao;

const $ = (id) => document.getElementById(id);

function primeiraPendente() {
  const k = FILA.findIndex((f) => !(chaveDe(f) in dec));
  return k < 0 ? FILA.length - 1 : k;
}

function pintar() {
  const f = FILA[i];
  if (!f) return;
  $("nome").textContent = f.nome;
  $("anim").textContent = "(" + f.animacao + ")";
  const s = f.sinais;
  const alertas = [];
  if (s.razao_componente < 0.75) alertas.push("fragmentou");
  if (s.queda_bbox > 0.18) alertas.push("encolheu " + Math.round(s.queda_bbox * 100) + "%");
  $("tags").innerHTML =
    `<span class="tag via-${f.via.replace(" ", "-")}">${f.via}</span>`
    + `<span class="tag">${f.slot}</span>`
    + `<span class="tag">${f.celulas} corpo(s)</span>`
    + (f.doadora ? `<span class="tag">doadora: ${f.doadora}</span>` : "")
    + alertas.map((a) => `<span class="tag alerta">${a}</span>`).join("");
  const url = f.tira;
  $("depois").style.background = `url("${url}") 0 0/${256 * f.frames}px 256px`;
  $("depois").style.setProperty("--n", f.frames);
  $("depois").style.setProperty("--dur", (f.frames / 8) + "s");
  $("antes").style.background = `url("${f.partida}") 0 0/256px 256px`;
  const feita = dec[chaveDe(f)];
  $("btSim").style.opacity = feita === "sim" ? 1 : .75;
  $("btNao").style.opacity = feita === "nao" ? 1 : .75;
  const n = Object.keys(dec).length;
  $("conta").textContent = `${i + 1} de ${FILA.length} — ${n} decidida(s)`;
  $("prog").style.width = (n / FILA.length * 100) + "%";
}

function decidir(v) {
  const f = FILA[i];
  if (!f) return;
  if (v) dec[chaveDe(f)] = v; else delete dec[chaveDe(f)];
  localStorage.setItem(CHAVE, JSON.stringify(dec));
  if (i < FILA.length - 1) { i++; pintar(); } else { mostrarFim(); }
}

function mostrarFim() {
  const sim = [], nao = [];
  for (const f of FILA) {
    const d = dec[chaveDe(f)];
    if (d === "sim") sim.push(chaveDe(f));
    else if (d === "nao") nao.push(chaveDe(f));
  }
  $("resumo").textContent =
    `${sim.length} aceitas, ${nao.length} rejeitadas, `
    + `${FILA.length - sim.length - nao.length} nao revisadas (ficam de fora).`;
  $("saida").value = JSON.stringify(
    { revisao: "animacoes-geradas", pin: PIN, aceitas: sim, rejeitadas: nao }, null, 1);
  $("tela").classList.add("oculto");
  $("fim").classList.remove("oculto");
}

$("btSim").onclick = () => decidir("sim");
$("btNao").onclick = () => decidir("nao");
$("btPular").onclick = () => { if (i < FILA.length - 1) { i++; pintar(); } else mostrarFim(); };
$("btFim").onclick = mostrarFim;
$("btVoltar").onclick = () => {
  $("fim").classList.add("oculto"); $("tela").classList.remove("oculto"); pintar();
};
$("btCopiar").onclick = async () => {
  await navigator.clipboard.writeText($("saida").value);
  $("btCopiar").textContent = "Copiado";
  setTimeout(() => ($("btCopiar").textContent = "Copiar"), 1500);
};
addEventListener("keydown", (e) => {
  if (e.key === "s" || e.key === "S") decidir("sim");
  else if (e.key === "n" || e.key === "N") decidir("nao");
  else if (e.key === " ") { e.preventDefault(); $("btPular").click(); }
  else if (e.key === "ArrowLeft" && i > 0) { i--; pintar(); }
  else if (e.key === "ArrowRight" && i < FILA.length - 1) { i++; pintar(); }
});
i = primeiraPendente();
pintar();
</script></body></html>
"""


if __name__ == "__main__":
    sys.exit(main())
