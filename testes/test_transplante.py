"""Transplante de animacao entre pecas analogas -- spec, decisao 11.

A peca que nao tem uma animacao ganha os frames dela a partir de OUTRA peca do
mesmo slot que tenha. A doadora aparece nas duas poses, entao ela diz para onde
cada pixel foi; a alvo parte de pixels quase iguais e recebe o mesmo caminho.

Deterministico de proposito: mesma entrada, mesma saida, sem modelo nem peso.
A trava 3 da spec exige o build reproduzivel byte a byte.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from transplante import (  # noqa: E402
    aplicar_campo,
    campo_de_deslocamento,
    escolher_doadora,
    pixels_diferentes,
    sobreposicao,
)


def arte(mascara: str) -> np.ndarray:
    """Uma arte de teste a partir de um desenho em texto.

    `.` e transparente; qualquer outro caractere vira um pixel opaco cuja cor
    e o proprio caractere -- assim da para conferir que o pixel CERTO andou,
    nao so que alguma coisa andou.
    """
    linhas = [l for l in mascara.strip().splitlines()]
    h, w = len(linhas), len(linhas[0])
    a = np.zeros((h, w, 4), dtype=np.uint8)
    for y, linha in enumerate(linhas):
        for x, c in enumerate(linha):
            if c != ".":
                a[y, x] = (ord(c), ord(c), ord(c), 255)
    return a


class TesteSobreposicao(unittest.TestCase):
    def test_silhuetas_iguais_dao_um(self):
        a = arte("""
.##.
####
""")
        self.assertEqual(sobreposicao(a, a.copy()), 1.0)

    def test_silhuetas_disjuntas_dao_zero(self):
        a = arte("""
##..
##..
""")
        b = arte("""
..##
..##
""")
        self.assertEqual(sobreposicao(a, b), 0.0)

    def test_metade_em_comum(self):
        # 2 pixels em comum, 6 na uniao
        a = arte("""
####
....
""")
        b = arte("""
..##
..##
""")
        self.assertAlmostEqual(sobreposicao(a, b), 2 / 6)

    def test_a_cor_nao_entra_na_conta_so_a_forma(self):
        a = arte("""
##..
""")
        b = arte("""
XX..
""")
        self.assertEqual(sobreposicao(a, b), 1.0)


class TesteEscolherDoadora(unittest.TestCase):
    def test_pega_a_de_silhueta_mais_parecida(self):
        alvo = arte("""
.##.
.##.
""")
        longe = arte("""
####
....
""")
        perto = arte("""
.##.
.#..
""")
        escolha = escolher_doadora(alvo, [("longe", longe), ("perto", perto)])
        self.assertEqual(escolha, "perto")

    def test_empate_resolve_pelo_id_para_nao_depender_da_ordem(self):
        alvo = arte("""
##..
""")
        a = arte("""
##..
""")
        b = arte("""
##..
""")
        self.assertEqual(escolher_doadora(alvo, [("zeta", a), ("alfa", b)]), "alfa")
        self.assertEqual(escolher_doadora(alvo, [("alfa", b), ("zeta", a)]), "alfa")

    def test_sem_candidata_nenhuma_devolve_nada(self):
        self.assertIsNone(escolher_doadora(arte("##"), []))

    def test_candidata_sem_sobreposicao_alguma_nao_serve(self):
        # doadora que nao encosta na alvo nao tem o que ensinar
        alvo = arte("""
##..
""")
        nada = arte("""
..##
""")
        self.assertIsNone(escolher_doadora(alvo, [("nada", nada)]))


class TestePixelsDiferentes(unittest.TestCase):
    """O que conta como erro e o que a TELA mostra, nao o byte.

    Os atlas do acervo gravam o pixel transparente como branco com alpha zero;
    o transplante devolve preto com alpha zero. Os dois sao invisiveis e iguais
    aos olhos, e comparar os quatro canais crus acusava 3.816 diferencas
    fantasmas num quadro de 4.096 -- mais erro do que a peca tem pixel.
    """

    def test_transparente_e_transparente_sao_iguais_seja_qual_for_o_rgb(self):
        a = np.zeros((2, 2, 4), dtype=np.uint8)
        b = np.zeros((2, 2, 4), dtype=np.uint8)
        b[..., :3] = 255  # branco invisivel, como o atlas grava
        self.assertEqual(pixels_diferentes(a, b), 0)

    def test_cor_diferente_no_pixel_visivel_conta(self):
        a = arte("AB")
        b = arte("AC")
        self.assertEqual(pixels_diferentes(a, b), 1)

    def test_peca_que_aparece_onde_a_outra_nao_tem_conta(self):
        a = arte("AA")
        b = arte("A.")
        self.assertEqual(pixels_diferentes(a, b), 1)


class TesteCampoDeDeslocamento(unittest.TestCase):
    def test_translacao_pura_e_recuperada(self):
        # o caso que decide: a doadora andou 1 para baixo e 2 para a direita.
        # O campo tem de descobrir isso, e aplicado a OUTRA peca produzir o
        # mesmo movimento.
        origem = arte("""
.AB...
.CD...
......
""")
        destino = arte("""
......
...AB.
...CD.
""")
        campo, silhueta = campo_de_deslocamento(origem, destino, raio=3, patch=1)
        np.testing.assert_array_equal(
            aplicar_campo(campo, origem, silhueta), destino)

    def test_aplicar_campo_parado_nao_mexe_em_nada(self):
        a = arte("""
.XY.
.ZW.
""")
        parado = np.zeros(a.shape[:2] + (2,), dtype=np.int16)
        np.testing.assert_array_equal(aplicar_campo(parado, a), a)

    def test_o_campo_transporta_a_peca_ALVO_nao_a_doadora(self):
        # a doadora ensina o caminho; quem viaja e a alvo, com as cores dela
        doadora_antes = arte("""
AA..
....
""")
        doadora_depois = arte("""
....
AA..
""")
        alvo = arte("""
QQ..
....
""")
        campo, silhueta = campo_de_deslocamento(
            doadora_antes, doadora_depois, raio=2, patch=1)
        esperado = arte("""
....
QQ..
""")
        np.testing.assert_array_equal(
            aplicar_campo(campo, alvo, silhueta), esperado)

    def test_e_deterministico(self):
        origem = arte("""
.AB.
.CD.
""")
        destino = arte("""
..AB
..CD
""")
        um, _ = campo_de_deslocamento(origem, destino, raio=2, patch=1)
        outro, _ = campo_de_deslocamento(origem, destino, raio=2, patch=1)
        np.testing.assert_array_equal(um, outro)

    def test_pixel_transparente_no_destino_nao_ganha_deslocamento(self):
        # onde a peca nao existe nao ha o que transportar; deixar lixo ali
        # sujaria a alvo com pixel que a doadora nem tem
        origem = arte("""
AA..
""")
        destino = arte("""
A...
""")
        campo, _ = campo_de_deslocamento(origem, destino, raio=2, patch=1)
        np.testing.assert_array_equal(campo[0, 1:], 0)


if __name__ == "__main__":
    unittest.main()
