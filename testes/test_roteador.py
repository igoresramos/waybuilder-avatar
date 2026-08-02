"""O roteador por rigidez -- spec, decisao 11b.

A peca legada que nao tem `idle` recebe a animacao de um dos dois jeitos, e a
escolha NAO e por slot: e por rigidez. A pesquisa de 2026-08-02 mediu que a
translacao rigida acerta 98,5% das pecas em que existe um (dy,dx) exato e
0,0% naquelas em que nao existe -- onde ela e PIOR que o transplante e falha
mais fundo (fracao de area errada mediana 0,454 contra 0,192).

Entao o roteador so translada quando o proprio treino do slot concorda, e no
resto NAO MEXE. "Nao mexer" e uma saida legitima e frequente: em 61 das 76
pecas legadas medidas foi a decisao certa.

Os dois limiares vieram de varredura por leave-one-out
(`docs/2026-08-02_calibracao-do-roteador.md`), nao de chute -- o chute
original (3 pecas, 80%) foi medido e perdeu.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roteador import (  # noqa: E402
    N_MIN_TREINO,
    FRACAO_MIN_CONCORDANCIA,
    decidir,
    deslocamento_otimo,
    eh_referencia,
    transladar,
)

RECORTE = ["idle", "combat_idle", "walk", "sit", "run"]


def arte(mascara: str) -> np.ndarray:
    """Mesma convencao de `test_transplante.py`: `.` transparente, resto opaco."""
    linhas = [l for l in mascara.strip().splitlines()]
    h, w = len(linhas), len(linhas[0])
    a = np.zeros((h, w, 4), dtype=np.uint8)
    for y, linha in enumerate(linhas):
        for x, c in enumerate(linha):
            if c != ".":
                a[y, x] = (ord(c), ord(c), ord(c), 255)
    return a


class TesteDeslocamentoOtimo(unittest.TestCase):
    def test_acha_a_translacao_que_zera_o_erro(self):
        a = arte("""
....
.ab.
.cd.
....
""")
        b = arte("""
.ab.
.cd.
....
....
""")
        # b e a subindo 1 px
        self.assertEqual(deslocamento_otimo(a, b), (-1, 0))

    def test_peca_parada_devolve_zero(self):
        a = arte("""
.##.
.##.
""")
        self.assertEqual(deslocamento_otimo(a, a.copy()), (0, 0))

    def test_devolve_None_quando_nenhuma_translacao_acerta(self):
        """Peca que MUDA de forma nao e rigida -- nao ha (dy,dx) que resolva.

        E o caso que a pesquisa mediu em 21,3% do acervo, e onde transladar e
        pior do que nao mexer.
        """
        a = arte("""
.##.
.##.
""")
        b = arte("""
####
....
""")
        self.assertIsNone(deslocamento_otimo(a, b))

    def test_empate_prefere_o_menor_deslocamento(self):
        """Peca simetrica pode casar de dois jeitos; o build tem de ser estavel."""
        a = arte("""
.#.#.
.....
""")
        b = arte("""
.....
.#.#.
""")
        self.assertEqual(deslocamento_otimo(a, b), (1, 0))


class TesteTransladar(unittest.TestCase):
    def test_move_a_peca_e_esvazia_o_que_saiu(self):
        a = arte("""
....
.ab.
....
""")
        esperado = arte("""
.ab.
....
....
""")
        np.testing.assert_array_equal(transladar(a, -1, 0)[..., 3], esperado[..., 3])

    def test_parado_devolve_a_mesma_arte(self):
        a = arte("""
.##.
.##.
""")
        np.testing.assert_array_equal(transladar(a, 0, 0), a)

    def test_o_que_sai_do_quadro_nao_reaparece_do_outro_lado(self):
        """`np.roll` faria a peca dar a volta -- seria arte fantasma na borda."""
        a = arte("""
##..
##..
""")
        movida = transladar(a, 0, -2)
        self.assertEqual(int(np.count_nonzero(movida[..., 3])), 0)


class TesteEhReferencia(unittest.TestCase):
    """Quem pode ensinar o deslocamento do slot.

    Esta e a trava da correcao 1 da revisao de spec de 2026-08-02: o codigo
    aceitava qualquer peca com `walk` + `idle`, mas a calibracao mediu os 14,5%
    e o zero-regressao com o treino restrito a pecas COMPLETAS. Sem esta regra
    a spec promete um numero que o build nao entrega.
    """

    def test_peca_completa_ensina(self):
        self.assertTrue(eh_referencia(RECORTE, RECORTE))

    def test_legada_com_walk_e_idle_NAO_ensina(self):
        """O caso exato que reabria o caminho da regressao `hat/tiara`."""
        self.assertFalse(eh_referencia(["walk", "idle"], RECORTE))

    def test_falta_uma_animacao_ja_desqualifica(self):
        self.assertFalse(eh_referencia(
            ["idle", "combat_idle", "walk", "run"], RECORTE))

    def test_animacao_a_mais_nao_atrapalha(self):
        """Peca do formato legado pode trazer animacao velha junto."""
        self.assertTrue(eh_referencia(RECORTE + ["thrust", "hurt"], RECORTE))


class TesteDecidir(unittest.TestCase):
    """A regra em si. O treino e uma lista de (dy,dx) das pecas NAO-legadas."""

    def test_translada_quando_o_treino_concorda(self):
        treino = [(-1, 0), (-1, 0), (-1, 0)]
        self.assertEqual(decidir(treino), ("transladar", (-1, 0)))

    def test_nao_mexe_quando_o_treino_e_pequeno_demais(self):
        self.assertEqual(decidir([(-1, 0)]), ("nao mexer", (0, 0)))

    def test_nao_mexe_quando_o_treino_discorda(self):
        """Metade diz uma coisa, metade diz outra: o slot nao sabe."""
        treino = [(-1, 0), (-1, 0), (0, 0), (1, 0)]
        self.assertEqual(decidir(treino), ("nao mexer", (0, 0)))

    def test_treino_que_concorda_em_ficar_parado_nao_mexe_na_peca(self):
        """Concordar em (0,0) e concordancia de verdade, e o resultado e o mesmo.

        Foi o que salvou as 4 pecas legadas que ja saiam exatas sem mexer: o
        proprio treino do slot dizia "nao mexe".
        """
        acao, d = decidir([(0, 0), (0, 0), (0, 0)])
        self.assertEqual(d, (0, 0))

    def test_treino_vazio_nao_mexe(self):
        """36 dos 50 slots legados nao tem parceiro nenhum -- e o caso comum."""
        self.assertEqual(decidir([]), ("nao mexer", (0, 0)))

    def test_o_limiar_e_o_medido_nao_o_chutado(self):
        """Trava de regressao: o chute (3, 0,80) foi medido e perdeu.

        Se alguem "arredondar" os limiares de volta, este teste cai.
        """
        self.assertEqual(N_MIN_TREINO, 2)
        self.assertEqual(FRACAO_MIN_CONCORDANCIA, 0.70)

    def test_exatamente_no_limiar_de_concordancia_translada(self):
        """0,70 de 10 e 7: o limiar e inclusivo."""
        treino = [(-1, 0)] * 7 + [(0, 0)] * 3
        self.assertEqual(decidir(treino), ("transladar", (-1, 0)))

    def test_um_abaixo_do_limiar_nao_translada(self):
        treino = [(-1, 0)] * 6 + [(0, 0)] * 4
        self.assertEqual(decidir(treino), ("nao mexer", (0, 0)))


if __name__ == "__main__":
    unittest.main()
