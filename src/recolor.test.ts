import { describe, expect, it, vi } from "vitest";
import { CacheDeRecolor, chaveDeRecolor, recolorirPixels } from "./recolor.js";

/** Monta um buffer RGBA a partir de triplas, com alpha 255. */
function pixels(...cores: [number, number, number][]): Uint8ClampedArray {
  const buf = new Uint8ClampedArray(cores.length * 4);
  cores.forEach(([r, g, b], i) => {
    buf.set([r, g, b, 255], i * 4);
  });
  return buf;
}

const DE = ["#000000", "#808080"];
const PARA = ["#FF0000", "#00FF00"];

describe("recolorirPixels", () => {
  it("troca a cor da rampa de origem pela correspondente na de destino", () => {
    const buf = pixels([0, 0, 0], [128, 128, 128]);
    recolorirPixels(buf, DE, PARA);
    expect(Array.from(buf)).toEqual([255, 0, 0, 255, 0, 255, 0, 255]);
  });

  it("casa dentro da tolerancia de um por canal", () => {
    // O guia do LPC usa tolerancia 1: compressao e antialias movem o valor.
    const buf = pixels([1, 0, 1]);
    recolorirPixels(buf, DE, PARA);
    expect(Array.from(buf).slice(0, 3)).toEqual([255, 0, 0]);
  });

  it("nao toca pixel fora da rampa", () => {
    const buf = pixels([10, 20, 30]);
    recolorirPixels(buf, DE, PARA);
    expect(Array.from(buf).slice(0, 3)).toEqual([10, 20, 30]);
  });

  it("preserva o alpha, inclusive transparente", () => {
    const buf = pixels([0, 0, 0]);
    buf[3] = 0;
    recolorirPixels(buf, DE, PARA);
    expect(buf[3]).toBe(0);
  });

  it("nao recoloriza em cascata dentro da mesma passada", () => {
    // Se #000 -> #808080 e #808080 -> #FFF, um pixel preto tem de virar
    // cinza e parar ali. Reprocessar o resultado seria trocar duas vezes.
    const buf = pixels([0, 0, 0]);
    recolorirPixels(buf, ["#000000", "#808080"], ["#808080", "#FFFFFF"]);
    expect(Array.from(buf).slice(0, 3)).toEqual([128, 128, 128]);
  });

  it("ignora sobra quando as rampas tem tamanhos diferentes", () => {
    const buf = pixels([0, 0, 0], [128, 128, 128]);
    recolorirPixels(buf, DE, ["#FF0000"]);
    expect(Array.from(buf).slice(4, 7)).toEqual([128, 128, 128]);
  });
});

describe("CacheDeRecolor", () => {
  it("so calcula uma vez por (arquivo, paleta, cor)", () => {
    // Sem isto, a grade recoloriza 89 celulas a cada navegacao.
    const cache = new CacheDeRecolor<string>();
    const caro = vi.fn(() => "bitmap");

    const a = cache.obter("atlas/hair/L1/male.png", "ulpc", "platinum", caro);
    const b = cache.obter("atlas/hair/L1/male.png", "ulpc", "platinum", caro);

    expect(a).toBe("bitmap");
    expect(b).toBe("bitmap");
    expect(caro).toHaveBeenCalledTimes(1);
  });

  it("separa entradas de cores diferentes do mesmo atlas", () => {
    const cache = new CacheDeRecolor<string>();
    cache.obter("a.png", "ulpc", "platinum", () => "um");
    expect(cache.obter("a.png", "ulpc", "ash", () => "dois")).toBe("dois");
    expect(cache.tamanho).toBe(2);
  });

  it("a chave distingue paletas homonimas em materiais diferentes", () => {
    expect(chaveDeRecolor("a.png", "ulpc", "black"))
      .not.toBe(chaveDeRecolor("b.png", "ulpc", "black"));
  });
});
