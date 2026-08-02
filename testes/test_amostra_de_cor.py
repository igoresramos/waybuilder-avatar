"""A amostra de cor de uma faixa de atlas -- spec, decisao 5f.

O painel tinha dois seletores de cor diferentes: quadradinho colorido para as
227 pecas do formato novo (onde a paleta diz o RGB) e o NOME escrito para as
391 do formato antigo (onde a cor esta embutida na arte e o app nao sabe qual
e). Padronizar em quadradinho exige o build olhar a arte e dizer a cor.

Duas armadilhas, e as duas tem teste aqui:

1. **Contar pixel nao serve.** O contorno e a cor mais frequente em peca
   pequena, e ele e quase preto em toda faixa -- amostrar por frequencia
   pintaria o acervo inteiro de preto. A rampa do LPC tem 6 tons ordenados
   sombra->luz e o representativo e o do MEIO, que e o mesmo criterio que o app
   ja usa para as paletas.
2. **Bicolor nao existe no acervo**, e a premissa contraria foi testada e caiu
   -- ver `TesteNaoExisteBicolor`. Uma cor por faixa, sempre.
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import amostra_da_faixa  # noqa: E402


def faixa(*cores, vazios: int = 0) -> np.ndarray:
    """Uma faixa de teste: cada cor repetida, mais transparentes opcionais."""
    px = []
    for c, n in cores:
        px.extend([c] * n)
    px.extend([(0, 0, 0, 0)] * vazios)
    a = np.zeros((1, len(px), 4), dtype=np.uint8)
    for i, p in enumerate(px):
        a[0, i] = p if len(p) == 4 else (*p, 255)
    return a


class TesteAmostraSimples(unittest.TestCase):
    def test_faixa_de_uma_cor_devolve_essa_cor(self):
        a = faixa(((30, 120, 200, 255), 40))
        self.assertEqual(amostra_da_faixa(a), "#1e78c8")

    def test_faixa_vazia_nao_devolve_amostra(self):
        a = faixa(vazios=50)
        self.assertIsNone(amostra_da_faixa(a))

    def test_pixel_transparente_nao_entra_na_conta(self):
        """Alfa e binario no LPC; o RGB por baixo do vazio e lixo."""
        a = faixa(((200, 40, 40, 255), 10), ((0, 255, 0, 0), 90))
        self.assertEqual(amostra_da_faixa(a), "#c82828")


class TesteContornoNaoVence(unittest.TestCase):
    def test_o_contorno_frequente_nao_e_a_amostra(self):
        """O caso que quebraria tudo: contorno escuro em maioria.

        Sem descartar as pontas, a peca inteira viraria um quadradinho preto.
        """
        a = faixa(
            ((20, 15, 25, 255), 60),      # contorno, o mais frequente
            ((90, 60, 140, 255), 25),     # sombra
            ((140, 100, 200, 255), 25),   # cor
            ((190, 160, 235, 255), 20),   # luz
            ((240, 230, 250, 255), 10),   # brilho
        )
        r = amostra_da_faixa(a)
        self.assertNotEqual(r, "#140f19", "escolheu o contorno")
        # tem de cair no miolo da rampa, nao nas pontas
        v = int(r[1:3], 16)
        self.assertGreater(v, 0x20)
        self.assertLess(v, 0xF0)


class TesteNaoExisteBicolor(unittest.TestCase):
    """Uma cor por faixa, sempre -- e a premissa contraria foi testada e caiu.

    A primeira versao devolvia um PAR quando a faixa parecia bicolor, porque 99
    dos 182 nomes de faixa do acervo sao compostos (`kite_blue_blue`,
    `base_black`). Rodando no acervo real, o detector marcou 40% das faixas como
    bicolor; apertando os criterios caiu para 4,5%, e ao olhar a arte dos casos
    que sobraram todos eram de UMA cor com sombreamento
    (`docs/2026-08-02_amostras-suspeitas.png`).

    O nome composto era artefato de nomenclatura, nao duas cores:
    `kite_blue_blue` e o slug da peca (`kite_blue`) mais a cor (`blue`) -- o
    mesmo achado que ja tinha gerado o rotulo "Azul e Azul".
    """

    def test_duas_cores_bem_separadas_ainda_dao_UMA_amostra(self):
        a = faixa(((200, 40, 40, 255), 50), ((40, 60, 200, 255), 50))
        self.assertIsInstance(amostra_da_faixa(a), str)

    def test_contorno_com_matiz_proprio_nao_desloca_a_amostra(self):
        """Caso real: `hat/tricorne` em `maroon`.

        O contorno roxo-escuro (`#1d131e`) e o tom mais frequente; a cor da
        peca e o marrom. A amostra tem de ser o marrom.
        """
        a = faixa(
            ((29, 19, 30, 255), 60),
            ((104, 33, 33, 255), 40),
            ((150, 60, 60, 255), 20),
        )
        r = amostra_da_faixa(a)
        self.assertNotEqual(r, "#1d131e", "escolheu o contorno")
        self.assertIn(r, ("#682121", "#963c3c"))


class TesteDeterminismo(unittest.TestCase):
    def test_mesma_entrada_mesma_saida(self):
        """A trava 3 da spec: o build tem de ser reproduzivel byte a byte."""
        a = faixa(((200, 40, 40, 255), 50), ((40, 60, 200, 255), 50))
        self.assertEqual(amostra_da_faixa(a), amostra_da_faixa(a.copy()))

    def test_a_ordem_dos_pixels_nao_muda_o_resultado(self):
        a = faixa(((200, 40, 40, 255), 50), ((40, 60, 200, 255), 50))
        b = a[:, ::-1].copy()
        self.assertEqual(amostra_da_faixa(a), amostra_da_faixa(b))


if __name__ == "__main__":
    unittest.main()
