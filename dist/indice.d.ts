/**
 * Renderer do avatar do Waybuilder.
 *
 * Puro: nada aqui toca canvas ou DOM. `montarCamadas` resolve o que desenhar e
 * em que ordem; `recolorirPixels` e `CacheDeRecolor` cuidam da cor. Quem
 * desenha e o app, que injeta o carregamento de imagem -- e o que permite
 * testar ordem, deslocamento, aviso e recolor sem `node-canvas`.
 */
export { montarCamadas } from "./camadas.js";
export { CacheDeRecolor, chaveDeRecolor, recolorirPixels } from "./recolor.js";
export type { Animacao, Aviso, Camada, CamadaDesenhavel, CanalDeCor, Catalogo, Composicao, Escolha, Item, Selecao, Slot, Variante, } from "./tipos.js";
