"""Consolidacao do atlas por slot, com teto de altura.

Um PNG por (slot, camada, corpo) em vez de um por peca: 2.800 arquivos viram
~460, o que importa para o precache do service worker.

O teto existe porque medir mostrou 12 grupos passando de 19.072 px -- acima do
limite de textura de 16.384 px que navegadores garantem. Sem ele, o atlas de
`wings` falharia no navegador, em alguns casos sem erro.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import TETO_DE_TEXTURA, empacotar_por_teto


class TestEmpacotamento(unittest.TestCase):
    def test_tudo_num_grupo_quando_cabe(self):
        self.assertEqual(empacotar_por_teto([64, 128, 64], teto=1000), [[0, 1, 2]])

    def test_abre_grupo_novo_ao_estourar_o_teto(self):
        self.assertEqual(empacotar_por_teto([600, 600, 600], teto=1000),
                         [[0], [1], [2]])

    def test_enche_o_grupo_antes_de_abrir_outro(self):
        self.assertEqual(empacotar_por_teto([400, 400, 400], teto=1000),
                         [[0, 1], [2]])

    def test_peca_maior_que_o_teto_fica_sozinha_e_nao_some(self):
        """Nao da para dividir uma peca ao meio: ela vai sozinha, mesmo
        estourando. Perder a peca seria pior que um atlas grande."""
        self.assertEqual(empacotar_por_teto([5000], teto=1000), [[0]])

    def test_lista_vazia_nao_gera_grupo(self):
        self.assertEqual(empacotar_por_teto([], teto=1000), [])

    def test_o_teto_padrao_respeita_o_limite_de_textura(self):
        self.assertLessEqual(TETO_DE_TEXTURA, 16384)


if __name__ == "__main__":
    unittest.main()
