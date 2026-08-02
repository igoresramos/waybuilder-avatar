import { describe, expect, it } from "vitest";
import { montarCamadas } from "./camadas.js";
import type { Catalogo, Item, Selecao } from "./tipos.js";

function peca(over: Partial<Item> & { id: string; slot: string }): Item {
  return {
    nome: over.nome ?? over.id,
    categoria: "teste",
    caminho: ["teste"],
    grupo: "Teste",
    camadas: [
      {
        ordem: 1,
        zPos: 10,
        corpos: {
          male: {
            arq: `atlas/${over.slot}/L1/male.png`,
            animacoes: [{ nome: "idle", frames: 2, x: 0 }],
            cores: { base: 0 },
          },
        },
      },
    ],
    ...over,
  } as Item;
}

function catalogo(itens: Item[]): Catalogo {
  return {
    pin: "teste",
    recorte: {
      animacoes: ["idle"],
      corpos: ["male", "female"],
      direcao: "frente",
      altura_do_frame: 64,
    },
    grupos: {},
    itens,
  };
}

describe("montarCamadas", () => {
  it("resolve o atlas e o recorte de uma peca equipada", () => {
    const cat = catalogo([peca({ id: "hair/afro", slot: "hair" })]);
    const { camadas } = montarCamadas(cat, { hair: { id: "hair/afro" } }, "male", "idle");

    expect(camadas).toHaveLength(1);
    expect(camadas[0]).toMatchObject({
      arq: "atlas/hair/L1/male.png",
      x: 0,
      y: 0,
      frames: 2,
      slot: "hair",
    });
  });

  it("ordena por zPos crescente", () => {
    const cat = catalogo([
      { ...peca({ id: "a/x", slot: "a" }), camadas: [{ ordem: 1, zPos: 90, corpos: peca({ id: "a/x", slot: "a" }).camadas[0]!.corpos }] } as Item,
      { ...peca({ id: "b/y", slot: "b" }), camadas: [{ ordem: 1, zPos: 10, corpos: peca({ id: "b/y", slot: "b" }).camadas[0]!.corpos }] } as Item,
    ]);
    const { camadas } = montarCamadas(cat, { a: { id: "a/x" }, b: { id: "b/y" } }, "male", "idle");
    expect(camadas.map((c) => c.slot)).toEqual(["b", "a"]);
  });

  it("desempata zPos igual por slot, nao pela ordem de escolha", () => {
    // 30 dos 64 zPos do acervo sao compartilhados por mais de um slot. Sem
    // desempate, a ordem em que o jogador clicou decidiria o desenho, e duas
    // fichas com a mesma selecao renderizariam diferente.
    const cat = catalogo([
      peca({ id: "hat/a", slot: "hat" }),
      peca({ id: "backpack/b", slot: "backpack" }),
    ]);

    const clicouHatPrimeiro: Selecao = { hat: { id: "hat/a" }, backpack: { id: "backpack/b" } };
    const clicouMochilaPrimeiro: Selecao = { backpack: { id: "backpack/b" }, hat: { id: "hat/a" } };

    expect(montarCamadas(cat, clicouHatPrimeiro, "male", "idle").camadas.map((c) => c.slot))
      .toEqual(montarCamadas(cat, clicouMochilaPrimeiro, "male", "idle").camadas.map((c) => c.slot));
  });

  it("id orfao vira aviso e o resto do avatar continua desenhando", () => {
    const cat = catalogo([peca({ id: "hair/afro", slot: "hair" })]);
    const { camadas, avisos } = montarCamadas(
      cat,
      { hair: { id: "hair/afro" }, hat: { id: "hat/sumiu-no-pin-novo" } },
      "male",
      "idle",
    );

    expect(camadas).toHaveLength(1);
    expect(avisos).toEqual([
      { slot: "hat", id: "hat/sumiu-no-pin-novo", motivo: "id-orfao" },
    ]);
  });

  it("peca sem arte no corpo atual avisa em vez de sumir calada", () => {
    const cat = catalogo([peca({ id: "hair/afro", slot: "hair" })]);
    const { camadas, avisos } = montarCamadas(
      cat,
      { hair: { id: "hair/afro" } },
      "female", // a fixture so tem arte para `male`
      "idle",
    );

    expect(camadas).toEqual([]);
    expect(avisos).toEqual([
      { slot: "hair", id: "hair/afro", motivo: "sem-arte-no-corpo" },
    ]);
  });

  it("usa o deslocamento da cor escolhida", () => {
    const base = peca({ id: "torso/blusa", slot: "torso" });
    base.camadas[0]!.corpos.male!.cores = { base: 0, azul: 64, verde: 128 };
    const { camadas } = montarCamadas(
      catalogo([base]),
      { torso: { id: "torso/blusa", cores: { cor: "verde" } } },
      "male",
      "idle",
    );
    expect(camadas[0]!.y).toBe(128);
  });

  it("cor inexistente cai na primeira, sem quebrar", () => {
    const base = peca({ id: "torso/blusa", slot: "torso" });
    base.camadas[0]!.corpos.male!.cores = { base: 0, azul: 64 };
    const { camadas } = montarCamadas(
      catalogo([base]),
      { torso: { id: "torso/blusa", cores: { cor: "roxo-que-nao-existe" } } },
      "male",
      "idle",
    );
    expect(camadas[0]!.y).toBe(0);
  });

  it("peca sem a animacao atual NAO desenha, em vez de congelar noutra", () => {
    // O gerador omite a camada naquela linha (`canvas/renderer.ts:343`). Cair
    // na primeira animacao desenharia a tira errada -- a peca ficaria parada
    // enquanto o resto anda.
    const cat = catalogo([peca({ id: "hair/afro", slot: "hair" })]);
    const { camadas, avisos } = montarCamadas(
      cat, { hair: { id: "hair/afro" } }, "male", "run",
    );
    expect(camadas).toEqual([]);
    expect(avisos).toEqual([
      { slot: "hair", id: "hair/afro", motivo: "sem-arte-no-corpo" },
    ]);
  });

  it("pede recolor quando a peca declara paleta e a cor nao e faixa do atlas", () => {
    // 383 dos 609 itens dependem disso -- inclui cor de pele e de cabelo.
    const base = peca({ id: "hair/afro", slot: "hair" });
    base.canais_de_cor = [{ nome: "cor", material: "hair", paletas: ["ulpc", "lpcr"] }];
    const { camadas } = montarCamadas(
      catalogo([base]),
      { hair: { id: "hair/afro", cores: { cor: "platinum" } } },
      "male",
      "idle",
    );
    expect(camadas[0]!.recolor).toEqual([
      { material: "hair", paleta: "ulpc", cor: "platinum" },
    ]);
  });

  it("pede um recolor por canal quando a peca tem duas cores", () => {
    // 27 itens declaram dois eixos -- um elmo com metal e tiras de tecido.
    const base = peca({ id: "hat/barbarian", slot: "hat" });
    base.canais_de_cor = [
      { nome: "color_1", material: "metal", paletas: ["ulpc"] },
      { nome: "hat_secondary", material: "cloth", paletas: ["ulpc"] },
    ];
    const { camadas } = montarCamadas(
      catalogo([base]),
      { hat: { id: "hat/barbarian", cores: { color_1: "steel", hat_secondary: "brown" } } },
      "male",
      "idle",
    );
    expect(camadas[0]!.recolor).toEqual([
      { material: "metal", paleta: "ulpc", cor: "steel" },
      { material: "cloth", paleta: "ulpc", cor: "brown" },
    ]);
  });

  it("peca que segue a cor do corpo herda o tom de pele equipado", () => {
    // 54 itens tem `match_body_color`: cabeca, nariz, orelha, rugas e
    // expressao sao slots SEPARADOS com material `body`. Sem herdar, trocar o
    // tom de pele deixa a cabeca de outra cor -- quebrado na cara.
    const corpo = peca({ id: "body/body-color", slot: "body" });
    corpo.canais_de_cor = [{ nome: "cor", material: "body", paletas: ["ulpc"] }];
    const cabeca = peca({ id: "head/human-male", slot: "head" });
    cabeca.canais_de_cor = [{ nome: "color_1", material: "body", paletas: ["ulpc"] }];
    cabeca.segue_cor_do_corpo = true;

    const { camadas } = montarCamadas(
      catalogo([corpo, cabeca]),
      { body: { id: "body/body-color", cores: { cor: "bronze" } },
        head: { id: "head/human-male" } },
      "male",
      "idle",
    );

    const daCabeca = camadas.find((c) => c.slot === "head")!;
    expect(daCabeca.recolor).toEqual([
      { material: "body", paleta: "ulpc", cor: "bronze" },
    ]);
  });

  it("a heranca do corpo VENCE a cor explicita da peca", () => {
    const corpo = peca({ id: "body/body-color", slot: "body" });
    corpo.canais_de_cor = [{ nome: "cor", material: "body", paletas: ["ulpc"] }];
    const cabeca = peca({ id: "head/human-male", slot: "head" });
    cabeca.canais_de_cor = [{ nome: "color_1", material: "body", paletas: ["ulpc"] }];
    cabeca.segue_cor_do_corpo = true;

    const { camadas } = montarCamadas(
      catalogo([corpo, cabeca]),
      { body: { id: "body/body-color", cores: { cor: "bronze" } },
        head: { id: "head/human-male", cores: { color_1: "olive" } } },
      "male",
      "idle",
    );
    // O gerador FORCA a cor do corpo nesses itens em render
    // (`state/palettes.ts:119-123`): a pele tem de ser uma so. Sem isso, uma
    // cor gravada na peca deixaria o rosto de um tom e o torso de outro --
    // medido na tela antes desta correcao.
    expect(camadas.find((c) => c.slot === "head")!.recolor).toEqual([
      { material: "body", paleta: "ulpc", cor: "bronze" },
    ]);
  });

  it("nao pede recolor quando a cor ja e uma faixa do atlas", () => {
    const base = peca({ id: "torso/blusa", slot: "torso" });
    base.camadas[0]!.corpos.male!.cores = { base: 0, azul: 64 };
    base.canais_de_cor = [{ nome: "cor", material: "cloth", paletas: ["ulpc"] }];
    const { camadas } = montarCamadas(
      catalogo([base]),
      { torso: { id: "torso/blusa", cores: { cor: "azul" } } },
      "male",
      "idle",
    );
    expect(camadas[0]!.recolor).toBeUndefined();
    expect(camadas[0]!.y).toBe(64);
  });
});
