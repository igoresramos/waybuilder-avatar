/**
 * O contrato do catalogo emitido por `build.py`.
 *
 * Os nomes ficam em pt-BR como o resto do projeto -- escolha consciente, nao
 * descuido: o catalogo, a spec e o build ja falam pt-BR, e um renderer em
 * ingles obrigaria a traduzir campo a campo na fronteira.
 */

/** Onde a peca fica no boneco. Peca do mesmo slot e mutuamente exclusiva. */
export type Slot = string;

export interface Animacao {
  nome: string;
  frames: number;
  /** Deslocamento horizontal da animacao dentro da tira. */
  x: number;
}

export interface Variante {
  /** Atlas do slot -- varias pecas dividem o mesmo arquivo. */
  arq: string;
  animacoes: Animacao[];
  /** nome da cor -> deslocamento vertical no atlas. */
  cores: Record<string, number>;
  /**
   * A cor de cada faixa nomeada, para a tela desenhar o quadradinho -- 5f.
   *
   * Uma cor por faixa: o acervo nao tem faixa bicolor, e a premissa contraria
   * foi medida e caiu (nome composto como `kite_blue_blue` e slug da peca mais
   * cor, nao duas cores). Opcional porque acervo anterior a decisao nao traz o
   * campo, e ai a tela cai no nome escrito, que era o comportamento antigo.
   */
  amostras?: Record<string, string>;
}

export interface Camada {
  ordem: number;
  zPos: number;
  corpos: Record<string, Variante>;
}

/** Um eixo de cor independente da peca. Um elmo pode ter metal e tecido. */
export interface CanalDeCor {
  nome: string;
  material: string;
  /**
   * Paletas oferecidas. `all.lpcr` quer dizer MATERIAL `all`, paleta `lpcr`:
   * o ponto separa os dois, e e por isso que a chave da cor precisa ser o par
   * `paleta:nome`.
   */
  paletas: string[];
  rotulo?: string;
  /**
   * Rampa em que a arte foi pintada, no formato `<versao>.<rampa>` -- ja
   * resolvida pelo build (`base_do_canal`). 41 canais declaram uma propria; o
   * app que deduzisse pelo material recolorizaria a partir da rampa errada e a
   * cor nao pintaria.
   */
  base?: string;
  /** Rampa de origem embutida na peca (`source`); vence a busca por paleta. */
  fonte?: string[];
}

export interface Item {
  id: string;
  /** Nome do upstream, em ingles. Fallback quando falta traducao. */
  nome: string;
  /** Nome em pt-BR -- e o que a tela mostra. */
  nome_ptbr?: string;
  categoria: string;
  slot: Slot;
  caminho: string[];
  grupo: string;
  camadas: Camada[];
  canais_de_cor?: CanalDeCor[];
  /** Herda o tom de pele do corpo equipado (`match_body_color`, 54 itens). */
  segue_cor_do_corpo?: boolean;
  /** Corpos em que a peca nao aparece -- a celula da grade precisa marcar. */
  sem_arte?: string[];
  /** Ids de pecas com que esta combina (trim -> chapeu). */
  combina_com?: string[];
}

export interface Catalogo {
  pin: string;
  recorte: {
    animacoes: string[];
    corpos: string[];
    direcao: string;
    /**
     * As 4 direcoes, na ordem em que o build as grava lado a lado no eixo X
     * (decisao 3b3 @10). `frente` vem primeiro de proposito -- e o endereco
     * base, o mesmo que `direcao` (singular) ja apontava. Catalogo antigo (sem
     * este campo) so tem frente: o app cai no fallback do indice 0.
     */
    direcoes?: string[];
    altura_do_frame: number;
    /**
     * Ciclo de frames por animacao, do gerador
     * (`state/constants.ts:124-154`). `walk` e [1..8] e pula o frame 0, que e
     * pose parada: em ordem crua a caminhada soluca a cada volta.
     */
    ciclos?: Record<string, number[]>;
    /** Quadros por segundo (`canvas/preview-animation.ts:180`). */
    fps?: number;
  };
  grupos: Record<string, { prioridade: number; rotulo?: string }>;
  /** slot -> rotulo em pt-BR. A casa mostrava `facial_eyes` cru. */
  slots?: Record<string, string>;
  /** nome cru da cor -> rotulo em pt-BR (rampa de paleta e faixa de atlas). */
  cores?: Record<string, string>;
  itens: Item[];
}

/**
 * O que o jogador escolheu, por slot.
 *
 * A cor mora aqui e nao no item: um `Record<slot, id>` puro perderia a cor ao
 * trocar de peca, e o `estado.cores` do visualizador -- chaveado por id --
 * ainda vaza cor de peca desequipada.
 */
export interface Escolha {
  id: string;
  /**
   * canal -> cor escolhida.
   *
   * O canal `cor` cobre a peca de um eixo so. Vale para os dois mundos: se o
   * valor for uma faixa do atlas (formato antigo), vira deslocamento; se for
   * cor de paleta, vira recolor em runtime.
   */
  cores?: Record<string, string>;
}

export type Selecao = Record<Slot, Escolha>;

/** Uma camada pronta para desenhar, com atlas e recortes ja resolvidos. */
export interface CamadaDesenhavel {
  arq: string;
  x: number;
  y: number;
  frames: number;
  zPos: number;
  slot: Slot;
  ordem: number;
  /** Recolors a aplicar em runtime, um por canal pedido. */
  recolor?: {
    /** Material do CANAL -- decide de onde sai a rampa de origem. */
    material: string;
    /** Paleta de DESTINO; pode ser de outro material (`all.lpcr`). */
    paleta: string;
    cor: string;
    /** Rampa de origem, `<versao>.<rampa>` dentro de `material`. */
    base?: string;
    /** Rampa de origem embutida; quando existe, dispensa `base`. */
    fonte?: string[];
  }[];
}

/** Por que uma peca escolhida nao entrou no desenho. */
export interface Aviso {
  slot: Slot;
  id: string;
  motivo: "id-orfao" | "sem-arte-no-corpo" | "animacao-substituida";
}

export interface Composicao {
  camadas: CamadaDesenhavel[];
  avisos: Aviso[];
}
