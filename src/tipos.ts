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
  paletas: string[];
  rotulo?: string;
  /** Rampa que a arte usa; sem ela, vale o `base` do material. */
  base?: string;
}

export interface Item {
  id: string;
  nome: string;
  categoria: string;
  slot: Slot;
  caminho: string[];
  grupo: string;
  camadas: Camada[];
  canais_de_cor?: CanalDeCor[];
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
    altura_do_frame: number;
  };
  grupos: Record<string, { prioridade: number; rotulo?: string }>;
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
  recolor?: { material: string; paleta: string; cor: string }[];
}

/** Por que uma peca escolhida nao entrou no desenho. */
export interface Aviso {
  slot: Slot;
  id: string;
  motivo: "id-orfao" | "sem-arte-no-corpo";
}

export interface Composicao {
  camadas: CamadaDesenhavel[];
  avisos: Aviso[];
}
