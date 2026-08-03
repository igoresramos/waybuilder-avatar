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
# ver o comentario equivalente em `preencher.py`: a copia dentro do app
# esta congelada desde que o acervo passou a ser servido do Pages
RAIZ_ACERVO = os.path.join(AQUI, "saida") + os.sep
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


_ATLAS: dict[str, np.ndarray] = {}


def atlas(arq: str) -> np.ndarray:
    if arq not in _ATLAS:
        _ATLAS[arq] = np.array(Image.open(RAIZ_ACERVO + arq).convert("RGBA"))
    return _ATLAS[arq]


def quadro_do_acervo(cat, item_id, corpo, camada, anim, k=0, direcao=0):
    """Um frame 64x64 do acervo, ja no endereco com direcao."""
    it = next((i for i in cat["itens"] if i["id"] == item_id), None)
    if it is None or camada >= len(it["camadas"]):
        return None
    v = it["camadas"][camada]["corpos"].get(corpo)
    if not v:
        return None
    a = next((x for x in v["animacoes"] if x["nome"] == anim), None)
    if a is None:
        return None
    y = v["cores"].get("base", next(iter(v["cores"].values())))
    x = a["x"] + (direcao * a["frames"] + min(k, a["frames"] - 1)) * Q
    return atlas(v["arq"])[y:y + Q, x:x + Q]


def sobrepor(fundo: np.ndarray, frente: np.ndarray) -> np.ndarray:
    """Alfa binario -- o LPC nao usa meio-tom (medido: 95,2% em 0, 4,8% em 255)."""
    m = frente[..., 3] > 0
    saida = fundo.copy()
    saida[m] = frente[m]
    return saida


def tiras_do_corpo(cat, base: str, corpo: str = "male") -> dict:
    """Uma tira do corpo nu por (animacao, direcao), para servir de palco.

    Sao poucos arquivos e todos os itens da fila os reaproveitam: a composicao
    peca-sobre-corpo acontece no CSS, sobrepondo duas camadas animadas em
    sincronia. Compor no Python geraria quatro tiras por item -- milhares de
    PNGs para a mesma dezena de fundos.
    """
    dirs = cat["recorte"].get("direcoes") or ["frente"]
    dest = os.path.join(base, "corpo")
    os.makedirs(dest, exist_ok=True)
    mapa = {}
    for anim in cat["recorte"]["animacoes"]:
        for d, nome_dir in enumerate(dirs):
            frames = []
            k = 0
            while True:
                f = quadro_do_acervo(cat, "body/body-color", corpo, 0, anim, k, d)
                if f is None:
                    break
                it = next(i for i in cat["itens"] if i["id"] == "body/body-color")
                a = next(x for x in it["camadas"][0]["corpos"][corpo]["animacoes"]
                         if x["nome"] == anim)
                if k >= a["frames"]:
                    break
                frames.append(f)
                k += 1
            if not frames:
                continue
            rel = f"corpo/{anim}__{nome_dir}.png"
            Image.fromarray(np.concatenate(frames, axis=1)).save(
                os.path.join(base, rel))
            mapa[f"{anim}|{d}"] = {"arq": rel, "frames": len(frames)}
    return mapa


def cena(cat, item_id, corpo, camada, anim, k, direcao, zpos_peca, peca=None):
    """A peca NO CORPO, na ordem de desenho -- e assim que o jogador ve.

    Julgar a peca solta engana: uma manga que se deforma some sob o braco, e um
    chapeu que encolhe 20% quase nao se nota flutuando no vazio, mas salta aos
    olhos preso a cabeca. O corpo base tem as cinco animacoes em toda direcao,
    entao serve de palco para qualquer lacuna.

    `peca` vem de fora quando o frame e GERADO (nao esta no acervo). Sem ela,
    desenha o que o acervo tem.
    """
    corpo_f = quadro_do_acervo(cat, "body/body-color", corpo, 0, anim, k, direcao)
    if corpo_f is None:
        return None
    if peca is None:
        peca = quadro_do_acervo(cat, item_id, corpo, camada, anim, k, direcao)
    if peca is None:
        return corpo_f
    # zPos < 10 desenha ATRAS do corpo (capa, camada traseira de asa)
    return sobrepor(corpo_f, peca) if zpos_peca >= 10 else sobrepor(peca, corpo_f)


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

    dirs = cat["recorte"].get("direcoes") or ["frente"]
    corpo_tiras = tiras_do_corpo(cat, base)

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
        n_dir = r.get("direcoes", 1)
        por_dir = (tira.shape[1] // Q) // max(1, n_dir)
        # a arte de partida vem do ATLAS, nao da tira gerada: em `run` e
        # `combat_idle` o frame 0 da tira JA e gerado, e comparar a arte nova
        # com ela mesma esconderia o defeito justamente onde o risco e maior
        partida = quadro_do_acervo(cat, item_id, r["corpo"], camada, "walk", 0, 0)
        if partida is None:
            continue
        dir_part = os.path.join(base, "partida")
        os.makedirs(dir_part, exist_ok=True)
        base_nome = f"{item_id.replace('/', '__')}__{r['corpo']}__c{camada}"
        partidas = []
        for d in range(min(n_dir, len(dirs))):
            q = quadro_do_acervo(cat, item_id, r["corpo"], camada, "walk", 0, d)
            if q is None:
                continue
            rel = f"partida/{base_nome}__{dirs[d]}.png"
            if not os.path.isfile(os.path.join(base, rel)):
                Image.fromarray(q).save(os.path.join(base, rel))
            partidas.append(rel)
        if not partidas:
            continue
        s_ = sinais(partida, tira[:, 0:Q])
        it = next((i for i in cat["itens"] if i["id"] == item_id), None)
        zpos = (it["camadas"][camada].get("zPos", 100) if it else 100)
        fila.append({
            "id": item_id,
            "nome": nome_de.get(item_id, item_id),
            "slot": slot_de.get(item_id, "?"),
            "animacao": anim,
            "corpo": r["corpo"],
            "camada": camada,
            "zpos": zpos,
            "via": r["via"],
            "doadora": r.get("doadora"),
            "celulas": len(regs),
            "tira": tira_rel.replace(os.sep, "/"),
            "partidas": partidas,
            "quadros_por_direcao": por_dir,
            "direcoes": [dirs[d] for d in range(min(n_dir, len(dirs)))],
            "sinais": s_,
            "nota": round(nota(s_), 3),
        })

    # translacao primeiro (zero regressao medida), depois transplante do melhor
    # para o pior -- ver o cabecalho
    ordem = {"transladar": 0, "analoga": 1, "corpo": 2}
    fila.sort(key=lambda f: (ordem.get(f["via"], 9), -f["nota"]))

    html = MOLDE.replace("__DADOS__", json.dumps(fila, ensure_ascii=False))
    html = html.replace("__CORPO__", json.dumps(corpo_tiras, ensure_ascii=False))
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
  :root { --fundo:#16181d; --card:#1e2128; --borda:#2c3039; --texto:#e6e8ec;
          --fraco:#9aa0ab; --ok:#3fb950; --nao:#f85149; --accent:#58a6ff; }
  * { box-sizing:border-box }
  body { margin:0; background:var(--fundo); color:var(--texto);
         font:15px/1.5 system-ui, sans-serif }
  header { position:sticky; top:0; background:var(--fundo); z-index:5;
           border-bottom:1px solid var(--borda); padding:12px 20px;
           display:flex; gap:20px; align-items:center; flex-wrap:wrap }
  h1 { font-size:1.05em; margin:0; font-weight:600 }
  .barra { flex:1; height:6px; background:var(--borda); border-radius:3px;
           overflow:hidden; min-width:120px }
  .barra i { display:block; height:100%; background:var(--ok); width:0 }
  .conta { color:var(--fraco); font-size:.85em; font-variant-numeric:tabular-nums }
  main { max-width:980px; margin:0 auto; padding:20px 20px 100px }
  .info { text-align:center; margin-bottom:14px }
  .info b { font-size:1.15em }
  .tags { display:flex; gap:8px; justify-content:center; flex-wrap:wrap;
          margin-top:8px; font-size:.8em; color:var(--fraco) }
  .tag { background:var(--card); border:1px solid var(--borda);
         padding:2px 9px; border-radius:99px }
  .tag.via-transladar { border-color:var(--ok); color:var(--ok) }
  .tag.alerta { border-color:var(--nao); color:var(--nao) }
  .palco { display:flex; gap:24px; justify-content:center; flex-wrap:wrap;
           background:var(--card); border:1px solid var(--borda);
           border-radius:10px; padding:22px }
  .vista { text-align:center }
  .vista h2 { font-size:.72em; color:var(--fraco); font-weight:500;
              text-transform:uppercase; letter-spacing:.06em; margin:0 0 8px }
  .cena { position:relative; width:224px; height:224px; background:#0e1013;
          border-radius:6px; overflow:hidden }
  .cena i { position:absolute; inset:0; image-rendering:pixelated;
            background-repeat:no-repeat }
  .cena i.corpo { z-index:1 } .cena i.peca { z-index:2 }
  .cena i.atras { z-index:0 }
  .roda { animation:tocar var(--dur) steps(var(--n)) infinite }
  @keyframes tocar { from{background-position-x:var(--x0)}
                     to{background-position-x:calc(var(--x0) - 224px * var(--n))} }
  @media (prefers-reduced-motion: reduce) { .roda { animation:none } }
  .acoes { display:flex; gap:12px; justify-content:center; margin:20px 0 10px }
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
    <div class="info"><b id="nome"></b><div class="tags" id="tags"></div></div>
    <div class="palco" id="palco"></div>
    <div class="acoes">
      <button class="nao" id="btNao">Rejeitar (N)</button>
      <button id="btPular">Pular (espaco)</button>
      <button class="sim" id="btSim">Aceitar (S)</button>
    </div>
    <p class="dica">Corpo masculino padrao. A esquerda de cada par e o que o
      jogador ve HOJE (peca travada no primeiro quadro); a direita e a gerada.<br>
      Setas para voltar. O que voce nao revisar fica FORA do build.</p>
  </div>
  <div class="fim oculto" id="fim">
    <h2 style="margin-top:0">Resultado</h2>
    <p id="resumo" class="conta"></p>
    <p class="dica" style="text-align:left">Copie o bloco e cole na conversa.</p>
    <textarea id="saida" readonly></textarea>
    <div class="acoes">
      <button id="btCopiar" class="sim">Copiar</button>
      <button id="btVoltar">Voltar a revisar</button>
    </div>
  </div>
</main>
<script>
const FILA = __DADOS__;
const CORPO = __CORPO__;
const PIN = "__PIN__";
const CHAVE = "waybuilder-revisao-" + PIN;
const Z = 224, ESC = 3.5;           // 64px * 3.5
let i = 0;
const dec = JSON.parse(localStorage.getItem(CHAVE) || "{}");
const chaveDe = (f) => f.id + "|" + f.animacao + "|c" + f.camada;
const $ = (id) => document.getElementById(id);

function camada(url, larguraQuadros, n, x0, classe) {
  const el = document.createElement("i");
  el.className = classe;
  el.style.background = `url("${url}") no-repeat 0 0/${Z * larguraQuadros}px ${Z}px`;
  el.style.setProperty("--x0", x0 + "px");
  if (n > 1) {
    el.classList.add("roda");
    el.style.setProperty("--n", n);
    el.style.setProperty("--dur", (n / 8) + "s");
  } else {
    el.style.backgroundPositionX = x0 + "px";
  }
  return el;
}

function vista(f, d, gerada) {
  const box = document.createElement("div");
  box.className = "cena";
  const c = CORPO[f.animacao + "|" + d];
  if (c) box.appendChild(camada(c.arq, c.frames, c.frames, 0, "corpo"));
  const q = f.quadros_por_direcao;
  const total = q * f.direcoes.length;
  const x0 = -Z * q * d;
  if (gerada) {
    // a tira gerada tem as direcoes lado a lado: comeca no bloco da direcao
    box.appendChild(camada(f.tira, total, q, x0,
      "peca" + (f.zpos < 10 ? " atras" : "")));
  } else {
    // "hoje": a peca fica PARADA no primeiro quadro, que e o que a decisao 12
    // faz com peca sem a animacao -- o corpo anda e ela nao
    box.appendChild(camada(f.partidas[d] || f.partidas[0], 1, 1, 0,
      "peca" + (f.zpos < 10 ? " atras" : "")));
  }
  return box;
}

function pintar() {
  const f = FILA[i];
  if (!f) return;
  $("nome").textContent = f.nome;
  const s = f.sinais, al = [];
  if (s.razao_componente < 0.75) al.push("fragmentou");
  if (s.queda_bbox > 0.18) al.push("encolheu " + Math.round(s.queda_bbox * 100) + "%");
  $("tags").innerHTML =
      `<span class="tag via-${f.via.replace(" ", "-")}">${f.via}</span>`
    + `<span class="tag">${f.animacao}</span>`
    + `<span class="tag">${f.slot}</span>`
    + `<span class="tag">${f.celulas} corpo(s)</span>`
    + (f.doadora ? `<span class="tag">doadora: ${f.doadora}</span>` : "")
    + al.map((a) => `<span class="tag alerta">${a}</span>`).join("");
  const p = $("palco");
  p.innerHTML = "";
  f.direcoes.forEach((nome, d) => {
    const bloco = document.createElement("div");
    bloco.className = "vista";
    const h = document.createElement("h2");
    h.textContent = nome === "frente" ? "de frente" : "para a direita";
    bloco.appendChild(h);
    const par = document.createElement("div");
    par.style.cssText = "display:flex;gap:10px";
    const a = vista(f, d, false), b = vista(f, d, true);
    a.title = "hoje"; b.title = "gerada";
    par.append(a, b);
    bloco.appendChild(par);
    p.appendChild(bloco);
  });
  const n = Object.keys(dec).length;
  $("conta").textContent = `${i + 1} de ${FILA.length} — ${n} decidida(s)`;
  $("prog").style.width = (n / FILA.length * 100) + "%";
}

function decidir(v) {
  const f = FILA[i]; if (!f) return;
  if (v) dec[chaveDe(f)] = v; else delete dec[chaveDe(f)];
  localStorage.setItem(CHAVE, JSON.stringify(dec));
  if (i < FILA.length - 1) { i++; pintar(); } else mostrarFim();
}

function mostrarFim() {
  const sim = [], nao = [];
  for (const f of FILA) {
    const d = dec[chaveDe(f)];
    if (d === "sim") sim.push(chaveDe(f)); else if (d === "nao") nao.push(chaveDe(f));
  }
  $("resumo").textContent = `${sim.length} aceitas, ${nao.length} rejeitadas, `
    + `${FILA.length - sim.length - nao.length} nao revisadas (ficam de fora).`;
  $("saida").value = JSON.stringify(
    { revisao: "animacoes-geradas", pin: PIN, aceitas: sim, rejeitadas: nao }, null, 1);
  $("tela").classList.add("oculto"); $("fim").classList.remove("oculto");
}

$("btSim").onclick = () => decidir("sim");
$("btNao").onclick = () => decidir("nao");
$("btPular").onclick = () => { if (i < FILA.length - 1) { i++; pintar(); } else mostrarFim(); };
$("btFim").onclick = mostrarFim;
$("btVoltar").onclick = () => {
  $("fim").classList.add("oculto"); $("tela").classList.remove("oculto"); pintar(); };
$("btCopiar").onclick = async () => {
  await navigator.clipboard.writeText($("saida").value);
  $("btCopiar").textContent = "Copiado";
  setTimeout(() => ($("btCopiar").textContent = "Copiar"), 1500); };
addEventListener("keydown", (e) => {
  if (e.key === "s" || e.key === "S") decidir("sim");
  else if (e.key === "n" || e.key === "N") decidir("nao");
  else if (e.key === " ") { e.preventDefault(); $("btPular").click(); }
  else if (e.key === "ArrowLeft" && i > 0) { i--; pintar(); }
  else if (e.key === "ArrowRight" && i < FILA.length - 1) { i++; pintar(); } });
i = (() => { const k = FILA.findIndex((f) => !(chaveDe(f) in dec));
             return k < 0 ? 0 : k; })();
pintar();
</script></body></html>
"""


if __name__ == "__main__":
    sys.exit(main())
