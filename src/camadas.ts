import type {
  Aviso,
  CamadaDesenhavel,
  Catalogo,
  Composicao,
  Item,
  Selecao,
} from "./tipos.js";

/**
 * As camadas desenhaveis de uma selecao, na ordem certa, mais os avisos.
 *
 * Puro: nao toca canvas, nao carrega imagem, nao depende de DOM. E o que
 * permite testar ordem, deslocamento e aviso sem `node-canvas`.
 */
export function montarCamadas(
  catalogo: Catalogo,
  selecao: Selecao,
  corpo: string,
  animacao: string,
): Composicao {
  const porId = new Map<string, Item>(catalogo.itens.map((i) => [i.id, i]));
  const camadas: CamadaDesenhavel[] = [];
  const avisos: Aviso[] = [];

  for (const [slot, escolha] of Object.entries(selecao)) {
    const item = porId.get(escolha.id);
    // (6) id orfao -- peca que sumiu entre snapshots -- produz avatar parcial
    // MAIS aviso. Nunca crash, nunca silencio.
    if (!item) {
      avisos.push({ slot, id: escolha.id, motivo: "id-orfao" });
      continue;
    }

    let desenhou = false;
    for (const camada of item.camadas) {
      const variante = camada.corpos[corpo];
      if (!variante) continue;

      const pedidas = escolha.cores ?? {};
      const nomes = Object.keys(variante.cores);
      // o canal `cor` e o eixo principal; e o unico que indexa o atlas
      const pedidaPrincipal = pedidas["cor"];
      const escolhida =
        pedidaPrincipal !== undefined && pedidaPrincipal in variante.cores
          ? pedidaPrincipal
          : nomes[0]!;
      const anim =
        variante.animacoes.find((a) => a.nome === animacao) ??
        variante.animacoes[0];
      if (!anim) continue;

      // Cor pedida que nao e faixa do atlas vira recolor em runtime, um por
      // canal. Sao 383 dos 609 itens -- inclui pele e cabelo, que o `build.py`
      // deixa explicitamente para o app. Um elmo tem metal e tecido, dois
      // canais independentes.
      const recolors = (item.canais_de_cor ?? []).flatMap((canal) => {
        const cor = pedidas[canal.nome];
        if (cor === undefined || cor in variante.cores) return [];
        const paleta = canal.paletas[0];
        if (paleta === undefined) return [];
        return [{ material: canal.material, paleta, cor }];
      });

      camadas.push({
        arq: variante.arq,
        x: anim.x,
        y: variante.cores[escolhida]!,
        frames: anim.frames,
        zPos: camada.zPos,
        slot,
        ordem: camada.ordem,
        ...(recolors.length > 0 ? { recolor: recolors } : {}),
      });
      desenhou = true;
    }

    // (5d) a peca existe mas nao cobre este corpo. Sem o aviso, a celula da
    // grade mostraria o personagem inalterado e o preview mentiria por omissao.
    if (!desenhou) {
      avisos.push({ slot, id: escolha.id, motivo: "sem-arte-no-corpo" });
    }
  }

  // (5e) 30 dos 64 zPos do acervo sao compartilhados por mais de um slot.
  // Ordenar so por zPos deixaria o resto por conta da ordem de insercao -- ou
  // seja, a ordem em que o jogador clicou decidiria o desenho, e duas fichas
  // com a mesma selecao renderizariam diferente.
  camadas.sort(
    (a, b) =>
      a.zPos - b.zPos ||
      a.slot.localeCompare(b.slot) ||
      a.ordem - b.ordem,
  );
  return { camadas, avisos };
}
