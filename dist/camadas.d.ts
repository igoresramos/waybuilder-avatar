import type { Catalogo, Composicao, Selecao } from "./tipos.js";
/**
 * As camadas desenhaveis de uma selecao, na ordem certa, mais os avisos.
 *
 * Puro: nao toca canvas, nao carrega imagem, nao depende de DOM. E o que
 * permite testar ordem, deslocamento e aviso sem `node-canvas`.
 */
export declare function montarCamadas(catalogo: Catalogo, selecao: Selecao, corpo: string, animacao: string): Composicao;
