/**
 * As camadas desenhaveis de uma selecao, na ordem certa, mais os avisos.
 *
 * Puro: nao toca canvas, nao carrega imagem, nao depende de DOM. E o que
 * permite testar ordem, deslocamento e aviso sem `node-canvas`.
 */
export function montarCamadas(catalogo, selecao, corpo, animacao) {
    const porId = new Map(catalogo.itens.map((i) => [i.id, i]));
    // (3j) o tom de pele do corpo equipado. Cabeca, nariz, orelha, rugas e
    // expressao sao slots SEPARADOS com material `body`: sem herdar, trocar a
    // pele deixa a cabeca de outra cor. O gerador forca isso em render
    // (`state/palettes.ts:119-123`).
    const corDoCorpo = (() => {
        const escolha = selecao["body"];
        if (!escolha?.cores)
            return undefined;
        const item = porId.get(escolha.id);
        const canal = item?.canais_de_cor?.[0]?.nome ?? "cor";
        return escolha.cores[canal];
    })();
    const camadas = [];
    const avisos = [];
    for (const [slot, escolha] of Object.entries(selecao)) {
        const item = porId.get(escolha.id);
        // (6) id orfao -- peca que sumiu entre snapshots -- produz avatar parcial
        // MAIS aviso. Nunca crash, nunca silencio.
        if (!item) {
            avisos.push({ slot, id: escolha.id, motivo: "id-orfao" });
            continue;
        }
        let desenhou = false;
        let substituiu = false;
        for (const camada of item.camadas) {
            const variante = camada.corpos[corpo];
            if (!variante)
                continue;
            const pedidas = escolha.cores ?? {};
            const nomes = Object.keys(variante.cores);
            // o canal `cor` e o eixo principal; e o unico que indexa o atlas
            const pedidaPrincipal = pedidas["cor"];
            const escolhida = pedidaPrincipal !== undefined && pedidaPrincipal in variante.cores
                ? pedidaPrincipal
                : nomes[0];
            // Peca sem a animacao atual aparece PARADA, nao some.
            //
            // O gerador omite a camada (`canvas/renderer.ts:343`) e nos copiavamos.
            // Medido no acervo, isso apagava 170 dos 627 itens -- 77% da armadura,
            // 75% dos acessorios --, pecas do formato legado que nunca ganharam as
            // animacoes novas. O jogador equipava e a peca sumia sem explicacao.
            //
            // A substituicao trava no PRIMEIRO frame (`frames: 1` abaixo), e nunca
            // roda a tira alheia em movimento -- esse era o risco que o gerador
            // evitava, e ele continua evitado. A ordem vem do RECORTE, nao da ordem
            // em que o build gravou: duas fichas com a mesma selecao tem de desenhar
            // igual.
            let anim = variante.animacoes.find((a) => a.nome === animacao);
            const substituta = anim === undefined;
            if (substituta) {
                for (const nome of catalogo.recorte.animacoes) {
                    const alt = variante.animacoes.find((a) => a.nome === nome);
                    if (alt) {
                        anim = alt;
                        break;
                    }
                }
            }
            if (!anim)
                continue;
            if (substituta)
                substituiu = true;
            // Cor pedida que nao e faixa do atlas vira recolor em runtime, um por
            // canal. Sao 383 dos 609 itens -- inclui pele e cabelo, que o `build.py`
            // deixa explicitamente para o app. Um elmo tem metal e tecido, dois
            // canais independentes.
            const recolors = (item.canais_de_cor ?? []).flatMap((canal) => {
                // A heranca FORCA: a pele tem de ser uma so. Uma cor gravada na peca
                // deixaria rosto e torso em tons diferentes.
                const herda = item.segue_cor_do_corpo && canal.material === "body" && corDoCorpo;
                const cor = herda ? corDoCorpo : pedidas[canal.nome];
                if (cor === undefined || cor in variante.cores)
                    return [];
                // A cor pode vir qualificada como "paleta:nome". Precisa: 18 dos 19
                // nomes repetidos entre as paletas de um canal sao RAMPAS DIFERENTES
                // -- ha tres `white` e tres `orange` distintos. So o nome e ambiguo.
                const [qual, nome] = cor.includes(":")
                    ? cor.split(":")
                    : [canal.paletas[0], cor];
                if (qual === undefined)
                    return [];
                // A rampa de ORIGEM viaja junto: 41 canais declaram um `base` proprio
                // e o app, deduzindo pelo material, recolorizava a partir da rampa
                // errada -- a cor aparecia na lista e nao pintava nada.
                return [{
                        material: canal.material,
                        paleta: qual,
                        cor: nome,
                        ...(canal.base !== undefined ? { base: canal.base } : {}),
                        ...(canal.fonte !== undefined ? { fonte: canal.fonte } : {}),
                    }];
            });
            camadas.push({
                arq: variante.arq,
                x: anim.x,
                y: variante.cores[escolhida],
                frames: substituta ? 1 : anim.frames,
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
        else if (substituiu) {
            // desenhou, mas travada: a tela precisa poder dizer isso, senao o
            // jogador acha que a peca e que esta com defeito
            avisos.push({ slot, id: escolha.id, motivo: "animacao-substituida" });
        }
    }
    // (5e) 30 dos 64 zPos do acervo sao compartilhados por mais de um slot.
    // Ordenar so por zPos deixaria o resto por conta da ordem de insercao -- ou
    // seja, a ordem em que o jogador clicou decidiria o desenho, e duas fichas
    // com a mesma selecao renderizariam diferente.
    camadas.sort((a, b) => a.zPos - b.zPos ||
        a.slot.localeCompare(b.slot) ||
        a.ordem - b.ordem);
    return { camadas, avisos };
}
