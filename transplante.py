"""Transplante de animacao entre pecas analogas -- spec, decisao 11.

170 dos 627 itens do acervo sao do formato legado do LPC e nao tem as animacoes
novas -- 77% da armadura, 75% dos acessorios. Nao ha de onde tirar essa arte:
tres caminhos foram medidos e os relatorios estao em `docs/`. O que sobrou, e
que o dono aceitou olhando a arte, e este: aproveitar OUTRA peca do mesmo slot
que tenha a animacao.

A ideia em uma frase: a doadora aparece nas duas poses, entao ela sabe para onde
cada pixel foi; a alvo parte de pixels quase iguais e recebe o mesmo caminho.

Deterministico de proposito -- nao ha modelo, peso nem sorteio. A trava 3 da
spec exige o build reproduzivel byte a byte, e um gerador treinado quebraria
isso. A contrapartida esta medida e assumida: o erro medio cai 62%, mas so 9,1%
dos frames saem exatos. O que sai e arte APROXIMADA ocupando o lugar de arte que
nao existe, nao a arte que faltava.
"""
from __future__ import annotations

import numpy as np


def _silhueta(a: np.ndarray) -> np.ndarray:
    """Onde a peca existe. So a forma importa -- a cor nao entra na conta."""
    return a[..., 3] > 0


def sobreposicao(a: np.ndarray, b: np.ndarray) -> float:
    """Quanto duas pecas ocupam o mesmo espaco (IoU das silhuetas), de 0 a 1.

    E o criterio de "parecida" que escolhe a doadora. Medido no acervo, peca e
    peca do mesmo slot chegam a 1,0 -- duas mangas longas ocupam exatamente os
    mesmos pixels --, enquanto o corpo nu nunca chega perto: e por isso que o
    corpo, testado antes, nao servia de molde.
    """
    sa, sb = _silhueta(a), _silhueta(b)
    uniao = int(np.count_nonzero(sa | sb))
    if uniao == 0:
        return 0.0
    return int(np.count_nonzero(sa & sb)) / uniao


def pixels_diferentes(a: np.ndarray, b: np.ndarray) -> int:
    """Quantos pixels a TELA mostraria diferentes entre duas artes.

    Pixel invisivel e pixel invisivel sao iguais, qualquer que seja o RGB por
    baixo. Os atlas do acervo gravam o transparente como branco com alpha zero
    e o transplante devolve preto com alpha zero -- comparar os quatro canais
    crus acusava 3.816 diferencas num quadro de 4.096, mais erro do que a peca
    inteira tem de pixel. Era defeito da MEDIDA, nao da arte.
    """
    va, vb = _silhueta(a), _silhueta(b)
    so_um = va ^ vb
    nos_dois = va & vb
    cor_diferente = np.any(a[..., :3] != b[..., :3], axis=-1) & nos_dois
    alpha_diferente = (a[..., 3] != b[..., 3]) & nos_dois
    return int(np.count_nonzero(so_um | cor_diferente | alpha_diferente))


def escolher_doadora(alvo: np.ndarray, candidatas) -> str | None:
    """O id da peca mais parecida, ou `None` se nenhuma serve.

    Empate resolve pelo id, nunca pela ordem da lista: duas fichas com a mesma
    selecao tem de desenhar igual, e a ordem em que o build varre o diretorio
    nao e promessa de nada.
    """
    melhor_id, melhor = None, 0.0
    for ident, arte in candidatas:
        s = sobreposicao(alvo, arte)
        # `>` mantem a primeira em caso de empate, e a lista vai ordenada por id
        if s > melhor or (s == melhor and s > 0.0 and ident < (melhor_id or "￿")):
            melhor_id, melhor = ident, s
    return melhor_id if melhor > 0.0 else None


def campo_de_deslocamento(
    origem: np.ndarray, destino: np.ndarray, raio: int = 6, patch: int = 5,
) -> np.ndarray:
    """Para onde cada pixel andou entre duas poses da MESMA peca.

    Devolve `(altura, largura, 2)` com o par `(dy, dx)`: o pixel que fica em
    `(y, x)` no destino veio de `(y + dy, x + dx)` na origem.

    A busca compara vizinhancas, nao pixels soltos. Um pixel isolado casa com
    qualquer outro da mesma cor -- e a paleta tem seis --, entao a comparacao
    por patch e o que impede o campo de virar ruido. Os deslocamentos sao
    varridos do menor para o maior, e o primeiro que empata vence: na duvida
    entre andar 1 ou andar 5, andar 1 e quase sempre o certo, e a regra deixa a
    escolha deterministica.

    Devolve o par `(campo, silhueta)`. Sem a silhueta o campo e ambiguo: onde a
    peca nao existe o deslocamento e zero, e zero tambem quer dizer "nao saiu do
    lugar" -- aplicar o campo copiava a arte da origem para fora da forma nova, e
    a peca saia com um fantasma da pose anterior colado.
    """
    o = origem.astype(np.int32)
    d = destino.astype(np.int32)
    h, w = d.shape[:2]
    m = patch // 2

    ordem = sorted(
        ((dy, dx) for dy in range(-raio, raio + 1) for dx in range(-raio, raio + 1)),
        key=lambda p: (p[0] * p[0] + p[1] * p[1], abs(p[0]) + abs(p[1]), p[0], p[1]),
    )

    # bordas repetidas: sem isso o pixel da beirada nao teria vizinhanca e a
    # peca encostada na moldura perderia o contorno
    pad = raio + m
    o_pad = np.pad(o, ((pad, pad), (pad, pad), (0, 0)), mode="edge")
    d_pad = np.pad(d, ((m, m), (m, m), (0, 0)), mode="edge")

    melhor_custo = np.full((h, w), np.inf)
    campo = np.zeros((h, w, 2), dtype=np.int16)

    for dy, dx in ordem:
        janela = o_pad[pad + dy - m:pad + dy - m + h + 2 * m,
                       pad + dx - m:pad + dx - m + w + 2 * m, :]
        erro = ((d_pad - janela) ** 2).sum(axis=-1)
        # soma do patch por somas acumuladas -- evita depender de scipy
        custo = _somar_janela(erro, patch)
        melhora = custo < melhor_custo
        melhor_custo = np.where(melhora, custo, melhor_custo)
        campo[..., 0] = np.where(melhora, dy, campo[..., 0])
        campo[..., 1] = np.where(melhora, dx, campo[..., 1])

    # onde a peca nao existe no destino nao ha o que transportar: deslocamento
    # ali sujaria a alvo com pixel que a doadora nem tem naquele lugar
    silhueta = _silhueta(destino)
    campo[~silhueta] = 0
    return campo, silhueta


def _somar_janela(erro: np.ndarray, patch: int) -> np.ndarray:
    """Soma de cada bloco `patch x patch`, por tabela de somas acumuladas."""
    ac = np.pad(erro, ((1, 0), (1, 0)), mode="constant").cumsum(0).cumsum(1)
    h = erro.shape[0] - patch + 1
    w = erro.shape[1] - patch + 1
    return (ac[patch:patch + h, patch:patch + w] - ac[0:h, patch:patch + w]
            - ac[patch:patch + h, 0:w] + ac[0:h, 0:w])


def aplicar_campo(
    campo: np.ndarray, arte: np.ndarray, silhueta: np.ndarray | None = None,
) -> np.ndarray:
    """Move a arte pelo caminho que a doadora ensinou.

    Quem viaja e a ALVO, com as cores dela -- a doadora so emprestou o
    movimento. Fora da `silhueta` o resultado sai vazio: a peca nova tem a forma
    da pose nova, nao a soma das duas.
    """
    h, w = arte.shape[:2]
    ys, xs = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")
    oy = np.clip(ys + campo[..., 0], 0, h - 1)
    ox = np.clip(xs + campo[..., 1], 0, w - 1)
    fora = arte[oy, ox, :]
    if silhueta is not None:
        fora = np.where(silhueta[..., None], fora, 0)
    return fora
