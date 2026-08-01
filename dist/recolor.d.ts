/**
 * Recolor por paleta, em runtime.
 *
 * 383 dos 609 itens do acervo dependem disto -- entre eles `body` e `hair`,
 * que ja migraram para o formato novo do upstream. Sem recolor o app fica sem
 * cor de pele e sem cor de cabelo; nao e refinamento, e a feature.
 *
 * A regra vem do `PALETTE_RECOLOR_GUIDE.md` do LPC (documentacao), nao do
 * codigo deles, que e GPL-3.0 -- ver decisao 1 da spec. A arte-base usa uma
 * rampa de referencia (o `base` do `meta_*.json` do material: `orange` para
 * cabelo); recolorir e trocar cada cor dessa rampa pela cor de mesma posicao na
 * rampa escolhida.
 */
/**
 * Troca, in-place, as cores da rampa `de` pelas de `para`.
 *
 * Cada pixel e decidido uma vez so: sem isso, uma rampa cujo destino contem
 * cores da origem recolorizaria em cascata e trocaria duas vezes.
 */
export declare function recolorirPixels(pixels: Uint8ClampedArray, de: string[], para: string[]): void;
export declare function chaveDeRecolor(arq: string, paleta: string, cor: string): string;
/**
 * Guarda o bitmap ja recolorido por (arquivo, paleta, cor).
 *
 * A grade da 5b compoe o personagem inteiro em cada celula -- o maior slot tem
 * 89 pecas. Sem cache, seria uma varredura de pixels por celula a cada
 * navegacao, e o recolor e justamente a parte cara.
 */
export declare class CacheDeRecolor<T> {
    private readonly mapa;
    get tamanho(): number;
    obter(arq: string, paleta: string, cor: string, calcular: () => T): T;
    limpar(): void;
}
