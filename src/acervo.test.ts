/**
 * Integracao contra o acervo real em `saida/` -- nao contra exemplo inventado.
 *
 * Estes testes pegam a classe de erro que fixture nenhuma pega: o catalogo
 * emitido mudar de forma sem o renderer saber.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { montarCamadas } from "./camadas.js";
import { recolorirPixels } from "./recolor.js";
import type { Catalogo } from "./tipos.js";

const RAIZ = join(import.meta.dirname, "..");
const cat = JSON.parse(
  readFileSync(join(RAIZ, "saida", "catalogo.json"), "utf-8"),
) as Catalogo;

function ler(rel: string): Record<string, string[]> {
  return JSON.parse(readFileSync(join(RAIZ, "saida", rel), "utf-8"));
}

describe("o acervo real", () => {
  it("compoe uma cabeca e um nariz ao mesmo tempo", () => {
    // O erro do prototipo: tratar `head/` como escolha unica apagaria o nariz.
    const cabeca = cat.itens.find((i) => i.slot === "head")!;
    const nariz = cat.itens.find((i) => i.slot === "nose")!;
    const { camadas, avisos } = montarCamadas(
      cat,
      { head: { id: cabeca.id }, nose: { id: nariz.id } },
      "male",
      "idle",
    );

    expect(avisos).toEqual([]);
    expect(camadas.map((c) => c.slot).sort()).toEqual(["head", "nose"]);
  });

  it("a mesma selecao desenha igual em qualquer ordem de escolha", () => {
    const [a, b] = [
      cat.itens.find((i) => i.slot === "hair")!,
      cat.itens.find((i) => i.slot === "hat")!,
    ];
    const chave = (s: object) =>
      montarCamadas(cat, s as never, "male", "idle").camadas
        .map((c) => `${c.slot}:${c.zPos}:${c.arq}`)
        .join("|");

    expect(chave({ hair: { id: a.id }, hat: { id: b.id } }))
      .toBe(chave({ hat: { id: b.id }, hair: { id: a.id } }));
  });

  it("pecas do mesmo slot compartilham o atlas consolidado", () => {
    const cabelos = cat.itens.filter((i) => i.slot === "hair").slice(0, 2);
    const arqs = cabelos.map(
      (i) =>
        montarCamadas(cat, { hair: { id: i.id } }, "male", "idle").camadas[0]
          ?.arq,
    );
    expect(arqs[0]).toBe(arqs[1]);
  });

  it("a rampa base do material existe na paleta que o item declara", () => {
    // `meta_hair.json` declara base "orange": e a rampa que a arte usa.
    const meta = JSON.parse(
      readFileSync(join(RAIZ, "saida", "paletas", "hair", "meta_hair.json"), "utf-8"),
    ) as { base: string; default: string };
    const paleta = ler(`paletas/hair/hair_${meta.default}.json`);

    expect(paleta[meta.base]).toBeDefined();
    expect(paleta[meta.base]!.length).toBeGreaterThan(0);
  });

  it("recolorir com a rampa real troca a cor da arte", () => {
    const meta = JSON.parse(
      readFileSync(join(RAIZ, "saida", "paletas", "hair", "meta_hair.json"), "utf-8"),
    ) as { base: string; default: string };
    const paleta = ler(`paletas/hair/hair_${meta.default}.json`);
    const de = paleta[meta.base]!;
    const para = paleta["platinum"] ?? paleta[Object.keys(paleta)[1]!]!;

    // um pixel exatamente na primeira cor da rampa base
    const n = parseInt(de[0]!.replace("#", ""), 16);
    const buf = new Uint8ClampedArray([
      (n >> 16) & 255, (n >> 8) & 255, n & 255, 255,
    ]);
    recolorirPixels(buf, de, para);

    const esperado = parseInt(para[0]!.replace("#", ""), 16);
    expect([buf[0], buf[1], buf[2]]).toEqual([
      (esperado >> 16) & 255, (esperado >> 8) & 255, esperado & 255,
    ]);
  });

  it("todo item que pede recolor tem paleta em disco", () => {
    const materiais = new Set(
      cat.itens.flatMap((i) => i.canais_de_cor ?? []).map((c) => c.material),
    );
    for (const m of materiais) {
      expect(() =>
        readFileSync(join(RAIZ, "saida", "paletas", m, `meta_${m}.json`)),
      ).not.toThrow();
    }
  });
});
