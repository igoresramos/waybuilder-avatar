"""Roteador por rigidez -- spec, decisao 11b.

A decisao 11 mandava gerar a animacao que falta por transplante de peca
analoga. A pesquisa de 2026-08-02 (`docs/2026-08-02_PESQUISA-transplante.md`)
mediu que existe caminho melhor -- e que ele nao serve para todas as pecas.

O que a medicao mostrou, em uma linha: `idle` k=1 e quase sempre `walk` k=0
deslocado alguns pixels, e quando isso vale, vale inteiro. Nas pecas em que
existe um (dy, dx) exato -- 78,7% do acervo -- a translacao acerta 98,5% dos
frames e a doadora nem e consultada. Nas outras 21,3% ela acerta 0,0%, e ai e
PIOR que o transplante: mediana de 88 pixels errados contra 51, com 80,2% dos
fracassos acima de um quarto da area da peca.

Por isso o roteador nao escolhe por slot, escolhe por RIGIDEZ. E onde nao ha
evidencia de rigidez, a resposta certa nao e "tenta assim mesmo": e NAO MEXER.
Em 61 das 76 pecas legadas medidas, nao mexer foi a decisao certa.

Os dois limiares nao sao chute. O chute original da pesquisa (3 pecas de
treino, 80% de concordancia) foi medido contra 47 alternativas e perdeu:
10,5% de frames exatos contra 14,5%, com as mesmas zero regressoes
(`docs/2026-08-02_calibracao-do-roteador.md`, varredura por leave-one-out em
76 pecas do corpo male, confirmada em outros 5 corpos).
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from transplante import pixels_diferentes

# Medidos, nao arbitrados -- ver o cabecalho. `test_roteador.py` trava os dois:
# se alguem "arredondar" de volta para o chute, o teste cai.
N_MIN_TREINO = 2
FRACAO_MIN_CONCORDANCIA = 0.70

# O mesmo raio do campo de deslocamento do transplante. O deslocamento real
# medido no acervo e quase sempre (-1, 0); 6 px cobre a cauda com folga.
RAIO = 6


def eh_referencia(anims_da_peca, anims_do_recorte) -> bool:
    """A peca pode ENSINAR o deslocamento do slot?

    So a peca COMPLETA -- que tem todas as animacoes do recorte -- serve. Ter
    `walk` e `idle` nao basta, e a diferenca nao e detalhe: a calibracao mediu
    zero regressao justamente porque restringiu o treino a pecas completas, e
    atribuiu as 13 regressoes da medicao anterior ao treino contaminado por
    pecas legadas. O caso `hat/tiara` -- arte que estava EXATA e foi destruida
    pela moda do slot -- veio de um treino assim.

    Deixar a legada votar reabre esse caminho: um slot com uma peca completa e
    uma legada-com-idle atinge o `N_MIN_TREINO` e translada onde a regra
    calibrada mandaria nao mexer.
    """
    return set(anims_do_recorte) <= set(anims_da_peca)


def _ordem_de_busca(raio: int = RAIO):
    """Deslocamentos do menor para o maior.

    Mesma ordem de `campo_de_deslocamento`: na duvida entre andar 1 e andar 5,
    andar 1 e quase sempre o certo. Empate resolvido assim e deterministico, e
    o build tem de ser reproduzivel byte a byte (trava 3 da spec).
    """
    return sorted(
        ((dy, dx) for dy in range(-raio, raio + 1) for dx in range(-raio, raio + 1)),
        key=lambda p: (p[0] * p[0] + p[1] * p[1], abs(p[0]) + abs(p[1]), p[0], p[1]),
    )


def transladar(arte: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """A arte deslocada, com o que saiu do quadro descartado.

    `np.roll` faria a peca dar a volta e reaparecer do outro lado -- arte
    fantasma colada na borda oposta, que e defeito pior que a lacuna.
    """
    saida = np.zeros_like(arte)
    h, w = arte.shape[:2]
    oy0, oy1 = max(0, dy), min(h, h + dy)
    ox0, ox1 = max(0, dx), min(w, w + dx)
    if oy0 >= oy1 or ox0 >= ox1:
        return saida
    saida[oy0:oy1, ox0:ox1] = arte[oy0 - dy:oy1 - dy, ox0 - dx:ox1 - dx]
    return saida


def deslocamento_otimo(
    origem: np.ndarray, destino: np.ndarray, raio: int = RAIO,
) -> tuple[int, int] | None:
    """O (dy, dx) que leva `origem` exatamente em `destino`, ou `None`.

    `None` quer dizer "esta peca nao e rigida": ela muda de FORMA entre as duas
    poses, e nenhuma translacao a resolve. E o sinal que o roteador usa para
    nao aplicar translacao onde ela seria pior que o transplante.

    Exato quer dizer ZERO pixel diferente na tela -- o mesmo criterio de
    `pixels_diferentes`, que ignora o RGB por baixo do transparente.
    """
    for dy, dx in _ordem_de_busca(raio):
        if pixels_diferentes(transladar(origem, dy, dx), destino) == 0:
            return (dy, dx)
    return None


def decidir(treino: list[tuple[int, int]]) -> tuple[str, tuple[int, int]]:
    """O que fazer com uma peca, dado o (dy, dx) otimo das pecas de referencia.

    `treino` sao os deslocamentos das pecas NAO-LEGADAS do mesmo slot e corpo
    -- as que tem as duas poses e portanto podem ser medidas. A peca sob
    decisao nunca entra na propria lista (leave-one-out), senao a medicao se
    valida sozinha.

    Devolve `("transladar", (dy, dx))` ou `("nao mexer", (0, 0))`.

    Concordar em (0, 0) tambem e concordancia: o resultado e o mesmo de nao
    mexer, e foi o que preservou as 4 pecas legadas que ja saiam exatas sem
    tratamento nenhum -- o treino do slot delas dizia "nao mexe".
    """
    if len(treino) < N_MIN_TREINO:
        return ("nao mexer", (0, 0))
    contagem = Counter(treino)
    # empate na moda resolve pelo menor deslocamento, nunca pela ordem da lista
    mais = max(contagem.values())
    candidatos = [d for d, n in contagem.items() if n == mais]
    moda = min(candidatos, key=lambda p: (p[0] * p[0] + p[1] * p[1], p[0], p[1]))
    if contagem[moda] / len(treino) < FRACAO_MIN_CONCORDANCIA:
        return ("nao mexer", (0, 0))
    return ("transladar", moda)
