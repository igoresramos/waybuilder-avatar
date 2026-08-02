"""Monta o documento de conferencia das animacoes geradas.

O que decide qualidade e ver o boneco ANDANDO, nao o quadro parado: defeito de
pixel art aparece no movimento, quando um pixel pisca entre um frame e outro.
Por isso cada peca sai aqui como tira de sprite animada por CSS, composta sobre
o corpo -- e do lado, uma animacao ORIGINAL da mesma peca, para comparar contra
a arte de verdade e nao contra a memoria.

Uso:
    python3 documento.py [--por-classe N] [--saida docs/...html]
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
from collections import defaultdict

import numpy as np
from PIL import Image

RAIZ = "/home/igor0/waybuilder/app/public/avatar/"
Q = 64
ZOOM = 3
FPS = 8

CICLOS = {"idle": [0, 0, 1, 1], "combat_idle": [0, 0, 1],
          "walk": [1, 2, 3, 4, 5, 6, 7, 8],
          "sit": [0] * 5 + [1] * 5 + [2] * 5,
          "run": [0, 1, 2, 3, 4, 5, 6, 7]}
ROTULO = {"idle": "Parado", "combat_idle": "Em guarda", "walk": "Andando",
          "sit": "Sentado", "run": "Correndo"}


def carregar(rel, _c={}):
    if rel not in _c:
        _c[rel] = np.array(Image.open(RAIZ + rel).convert("RGBA"))
    return _c[rel]


def variante(item, corpo, camada=0):
    if camada >= len(item["camadas"]):
        return None
    return item["camadas"][camada]["corpos"].get(corpo)


def quadro(v, anim, k):
    a = next((x for x in v["animacoes"] if x["nome"] == anim), None)
    if a is None:
        return None
    y = v["cores"].get("base", next(iter(v["cores"].values())))
    x = a["x"] + min(k, a["frames"] - 1) * Q
    return carregar(v["arq"])[y:y + Q, x:x + Q, :]


def sobrepor(fundo, frente):
    """Frente por cima, respeitando o alpha -- e assim que o app compoe."""
    saida = fundo.copy()
    m = frente[..., 3] > 0
    saida[m] = frente[m]
    return saida


def tira(frames):
    """Uma faixa horizontal com os frames do ciclo, em data URI.

    Em tamanho NATIVO -- quem amplia e o CSS, com `image-rendering: pixelated`.
    Gravar ja ampliado multiplicava o peso por nove sem ganhar nitidez nenhuma,
    e com 235 pecas na pagina isso e a diferenca entre abrir e nao abrir.
    """
    faixa = np.concatenate(frames, axis=1)
    im = Image.fromarray(faixa)
    # paleta em vez de RGBA: a arte tem 6 cores por rampa, e guardar 32 bits por
    # pixel para isso e o que fazia a pagina passar de 18 MB
    # FASTOCTREE e o unico quantizador que aceita RGBA, e aqui o alpha PRECISA
    # sobreviver: e ele que deixa o fundo da pagina aparecer atras do boneco
    im = im.quantize(colors=255, method=Image.FASTOCTREE)
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--por-classe", type=int, default=14)
    p.add_argument("--corpo", default="male",
                   help="'todos' inclui os seis; o padrao e so o masculino, "
                        "que e o corpo com mais arte e o que o app abre")
    p.add_argument("--preenchimento", default="preenchimento")
    p.add_argument("--saida", default="docs/2026-08-02_animacoes-geradas.html")
    args = p.parse_args()

    cat = json.load(open(RAIZ + "catalogo.json"))
    byid = {i["id"]: i for i in cat["itens"]}
    dados = json.load(open(os.path.join(args.preenchimento, "preenchimento.json")))
    lacunas = dados["lacunas"]

    # uma entrada por (peca, corpo, camada, animacao); agrupa por peca para
    # mostrar a peca inteira de uma vez
    por_peca = defaultdict(list)
    for r in lacunas:
        if args.corpo != "todos" and r["corpo"] != args.corpo:
            continue
        por_peca[(r["id"], r["corpo"], r["camada"])].append(r)

    # amostra equilibrada: as duas vias tem qualidade diferente e precisam ser
    # julgadas separadas, senao a boa carrega a fraca
    escolhidas = {"analoga": [], "corpo": []}
    for chave, rs in sorted(por_peca.items()):
        via = "corpo" if all(r["via"] == "corpo" for r in rs) else "analoga"
        # `--por-classe 0` mostra TODAS: e o modo de conferencia de verdade,
        # amostra serve para iterar no layout
        if args.por_classe and len(escolhidas[via]) >= args.por_classe:
            continue
        escolhidas[via].append((chave, rs))

    corpo_base = byid.get("body/body-color")
    blocos = []
    for via in ("analoga", "corpo"):
        cartoes = []
        for (ident, corpo, camada), rs in escolhidas[via]:
            item = byid[ident]
            v = variante(item, corpo, camada)
            cv = variante(corpo_base, corpo, 0) if corpo_base else None
            geradas = {r["animacao"]: r for r in rs}
            fitas = []
            # primeiro as GERADAS, depois uma original para comparar
            originais = [a["nome"] for a in v["animacoes"]]
            ordem = ([(a, True) for a in sorted(geradas)]
                     + [(a, False) for a in originais[:1]])
            for anim, sintetica in ordem:
                ciclo = CICLOS.get(anim, [0])
                frames = []
                for k in ciclo:
                    if sintetica:
                        arq = os.path.join(
                            args.preenchimento, "frames",
                            ident.replace("/", "__"), corpo, f"c{camada}",
                            f"{anim}.png")
                        if not os.path.exists(arq):
                            break
                        faixa = np.array(Image.open(arq).convert("RGBA"))
                        n = faixa.shape[1] // Q
                        peca = faixa[:, min(k, n - 1) * Q:min(k, n - 1) * Q + Q, :]
                    else:
                        peca = quadro(v, anim, k)
                    if peca is None:
                        break
                    fundo = (quadro(cv, anim, k) if cv is not None else None)
                    if fundo is None:
                        fundo = np.zeros((Q, Q, 4), dtype=np.uint8)
                    frames.append(sobrepor(fundo, peca))
                if not frames:
                    continue
                r = geradas.get(anim)
                fitas.append({
                    "anim": anim, "rotulo": ROTULO.get(anim, anim),
                    "sintetica": sintetica, "n": len(frames),
                    "b64": tira(frames),
                    "doadora": (byid.get(r["doadora"], {}).get("nome_ptbr")
                                or r["doadora"]) if r else None,
                    "iou": r["iou"] if r else None,
                })
            if not fitas:
                continue
            cartoes.append({
                "nome": item.get("nome_ptbr") or item["nome"],
                "id": ident, "corpo": corpo,
                "slot": cat.get("slots", {}).get(item["slot"], item["slot"]),
                "fitas": fitas,
            })
        blocos.append((via, cartoes))

    html = montar(blocos, dados["resumo"], len(lacunas), len(por_peca))
    os.makedirs(os.path.dirname(args.saida), exist_ok=True)
    open(args.saida, "w").write(html)
    print(f"escrito: {args.saida} ({len(html)/1024:.0f} KB)")
    for via, cartoes in blocos:
        print(f"   {via}: {len(cartoes)} pecas mostradas")


def montar(blocos, resumo, total, pecas):
    def fita(f):
        dur = round(f["n"] / FPS, 3)
        marca = ('<span class="etiqueta nova">gerada</span>' if f["sintetica"]
                 else '<span class="etiqueta orig">original</span>')
        fonte = (f'<p class="fonte">molde: {f["doadora"]}'
                 + (f' &middot; silhueta {int(f["iou"]*100)}%' if f["iou"] else '')
                 + '</p>') if f["sintetica"] and f["doadora"] else ''
        # `--fim` e a largura TOTAL da tira, em px. Sem ela a animacao percorria
        # a largura de um frame so e cada passo deslizava uma fracao -- a peca
        # escorregava para o lado em vez de trocar de quadro.
        return f"""          <figure class="fita">
            <div class="palco" style="--n:{f['n']};--dur:{dur}s;
                 --fim:-{f['n'] * Q * ZOOM}px;
                 background-image:url(data:image/png;base64,{f['b64']})"
                 role="img" aria-label="{f['rotulo']}{' gerada' if f['sintetica'] else ' original'}"></div>
            <figcaption>{f['rotulo']} {marca}{fonte}</figcaption>
          </figure>"""

    def cartao(c):
        return f"""      <article class="peca">
        <header><h3>{c['nome']}</h3>
          <p class="meta">{c['slot']} &middot; {c['corpo']}</p></header>
        <div class="fitas">
{chr(10).join(fita(f) for f in c['fitas'])}
        </div>
      </article>"""

    secoes = []
    titulos = {
        "analoga": ("Molde de peça análoga",
                    "A peça foi refeita a partir de outra peça de silhueta parecida. "
                    "É a via boa: o erro médio cai 62%."),
        "corpo": ("Molde do corpo",
                  "Não havia peça parecida com essa animação, então o molde foi o "
                  "corpo nu. Medido antes, corta só 11% do erro — esta seção é a "
                  "que precisa do seu olho."),
    }
    for via, cartoes in blocos:
        t, sub = titulos[via]
        secoes.append(f"""    <section class="classe">
      <div class="classe-topo"><h2>{t}</h2><p>{sub}</p></div>
      <div class="grade">
{chr(10).join(cartao(c) for c in cartoes)}
      </div>
    </section>""")

    linhas = " &middot; ".join(f"{v} por {k}" for k, v in resumo.items())
    return f"""<title>Animações geradas — conferência de qualidade</title>
<style>
  :root {{
    --tinta:#15181c; --papel:#1e242c; --linha:#2f3947; --texto:#f2f5f8;
    --fraco:#98a3b3; --nova:#ffa03a; --orig:#5bc8a8;
    --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
    --corpo:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  }}
  @media (prefers-color-scheme: light) {{
    :root {{ --tinta:#f5f2ee; --papel:#fff; --linha:#e2dbd2; --texto:#191d22;
             --fraco:#5f6b7a; --nova:#c25a06; --orig:#127a5c; }}
  }}
  :root[data-theme="light"] {{ --tinta:#f5f2ee; --papel:#fff; --linha:#e2dbd2;
    --texto:#191d22; --fraco:#5f6b7a; --nova:#c25a06; --orig:#127a5c; }}
  :root[data-theme="dark"] {{ --tinta:#15181c; --papel:#1e242c; --linha:#2f3947;
    --texto:#f2f5f8; --fraco:#98a3b3; --nova:#ffa03a; --orig:#5bc8a8; }}
  body {{ margin:0; padding:clamp(20px,4vw,48px) 20px 72px; background:var(--tinta);
          color:var(--texto); font-family:var(--corpo); line-height:1.6; }}
  .folha {{ max-width:1180px; margin:0 auto; display:flex; flex-direction:column; gap:44px; }}
  .eyebrow {{ font-family:var(--mono); font-size:.72rem; letter-spacing:.14em;
              text-transform:uppercase; color:var(--nova); margin:0 0 10px; }}
  h1 {{ margin:0 0 10px; font-size:clamp(1.55rem,3.4vw,2.15rem); line-height:1.15;
        text-wrap:balance; letter-spacing:-.015em; font-weight:650; }}
  .abre p {{ margin:0; max-width:66ch; color:var(--fraco); }}
  .placar {{ font-family:var(--mono); font-size:.85rem; color:var(--fraco);
             margin-top:12px; font-variant-numeric:tabular-nums; }}
  .classe-topo h2 {{ margin:0 0 4px; font-size:1.22rem; font-weight:640; }}
  .classe-topo p {{ margin:0 0 18px; color:var(--fraco); max-width:70ch; font-size:.95rem; }}
  .grade {{ display:grid; gap:16px;
            grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); }}
  .peca {{ background:var(--papel); border:1px solid var(--linha); border-radius:10px;
           padding:14px; display:flex; flex-direction:column; gap:12px; }}
  .peca h3 {{ margin:0; font-size:1rem; font-weight:620; }}
  .meta {{ margin:2px 0 0; font-family:var(--mono); font-size:.7rem;
           text-transform:uppercase; letter-spacing:.07em; color:var(--fraco); }}
  .fitas {{ display:flex; flex-wrap:wrap; gap:12px; }}
  .fita {{ margin:0; display:flex; flex-direction:column; gap:5px; }}
  .palco {{ width:{Q*ZOOM}px; height:{Q*ZOOM}px; image-rendering:pixelated;
            border:1px solid var(--linha); border-radius:6px;
            background-repeat:no-repeat;
            /* a tira vem em 64px por quadro; o CSS e que amplia */
            background-size:calc(var(--n) * {Q*ZOOM}px) {Q*ZOOM}px;
            animation:anda var(--dur) steps(var(--n)) infinite; }}
  @keyframes anda {{ from {{ background-position:0 0; }}
                     to {{ background-position:var(--fim) 0; }} }}
  @media (prefers-reduced-motion: reduce) {{ .palco {{ animation:none; }} }}
  figcaption {{ font-size:.76rem; color:var(--fraco); max-width:{Q*ZOOM}px; }}
  .etiqueta {{ font-family:var(--mono); font-size:.62rem; letter-spacing:.08em;
               text-transform:uppercase; padding:1px 5px; border-radius:3px;
               border:1px solid currentColor; margin-left:4px; }}
  .nova {{ color:var(--nova); }} .orig {{ color:var(--orig); }}
  .fonte {{ margin:3px 0 0; font-size:.68rem; color:var(--fraco); }}
</style>
<div class="folha">
  <div class="abre">
    <p class="eyebrow">Waybuilder &middot; acervo do avatar &middot; 2 de agosto de 2026</p>
    <h1>Animações geradas: confira a qualidade</h1>
    <p>
      As peças do formato legado do LPC não têm as animações novas. Estas aqui foram
      refeitas por transplante: o molde vem de outra peça que tem a animação, e os
      pixels que se movem são os da própria peça. Não há IA, não há desenho novo —
      só rearranjo. Cada fita está rodando a 8 quadros por segundo, igual ao app.
      A marcada como <span class="etiqueta orig">original</span> é arte de verdade,
      para comparar.
    </p>
    <p class="placar">{total} lacunas preenchidas em {pecas} combinações de peça e corpo &middot; {linhas}</p>
  </div>
{chr(10).join(secoes)}
</div>
"""


if __name__ == "__main__":
    main()
