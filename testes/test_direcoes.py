"""As direcoes na tira -- spec, decisao 3b3 @12.

O boneco passou a girar: frente e perfil direito, por decisao do dono. As
direcoes vao lado a lado no eixo X, ao lado dos frames, e nao empilhadas no Y
junto das cores -- medido no catalogo de 643 atlas, empilhar no Y fazia 105
deles passarem do teto de textura de 16.384 px (o pior, `wings`, chegava a
65.280 com 4 direcoes).

O teste que mais importa aqui e o da ORDEM: a frente e gravada primeiro, contra
a ordem do LPC. Se fosse ao contrario, o endereco antigo (`x + k*64`) passaria
a apontar para as costas e o acervo inteiro viraria de costas sem erro nenhum.

Os testes nao chumbam QUANTAS direcoes existem: o numero e decisao de produto e
ja mudou uma vez (4 -> 2). O que eles travam e o layout e a ordem, que sao
contrato.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image  # noqa: E402

from build import ALTURA, DIRECOES, LINHA_DA_FRENTE, recortar_frente  # noqa: E402


def folha(frames: int, cor_por_linha: dict[int, tuple]) -> Image.Image:
    """Uma folha do LPC de mentira: 4 linhas de 64px, cada uma de uma cor."""
    im = Image.new("RGBA", (frames * ALTURA, 4 * ALTURA), (0, 0, 0, 0))
    for linha, cor in cor_por_linha.items():
        bloco = Image.new("RGBA", (frames * ALTURA, ALTURA), cor)
        im.paste(bloco, (0, linha * ALTURA))
    return im


COSTAS = (10, 0, 0, 255)
PERFIL_E = (0, 10, 0, 255)
FRENTE = (0, 0, 10, 255)
PERFIL_D = (10, 10, 0, 255)
TODAS = {0: COSTAS, 1: PERFIL_E, 2: FRENTE, 3: PERFIL_D}


class TesteOrdemDasDirecoes(unittest.TestCase):
    def test_a_frente_vem_primeiro_nao_a_ordem_do_LPC(self):
        """A trava mais importante do arquivo.

        O endereco base (indice 0) tem de ser a FRENTE, senao todo consumidor
        que ainda enderece `x + k*64` mostra o boneco de costas -- em silencio.
        """
        self.assertEqual(DIRECOES[0][0], "frente")
        self.assertEqual(DIRECOES[0][1], LINHA_DA_FRENTE)

    def test_cada_direcao_aparece_uma_vez_e_aponta_para_linha_valida(self):
        """Nao trava o NUMERO de direcoes -- isso e decisao de produto."""
        nomes = [n for n, _ in DIRECOES]
        linhas = [l for _, l in DIRECOES]
        self.assertEqual(len(set(nomes)), len(nomes), "direcao repetida")
        self.assertEqual(len(set(linhas)), len(linhas), "duas direcoes na mesma linha")
        for l in linhas:
            self.assertIn(l, (0, 1, 2, 3), "a folha do LPC so tem 4 linhas")


class TesteRecortarLinha(unittest.TestCase):
    def test_recorta_a_linha_pedida_e_nao_outra(self):
        im = folha(2, TODAS)
        for _nome, linha in DIRECOES:
            faixa = recortar_frente(im, im.size[0], linha)
            self.assertEqual(faixa.getpixel((0, 0)), TODAS[linha],
                             f"linha {linha} recortou a arte errada")

    def test_o_padrao_continua_sendo_a_frente(self):
        """Chamada sem `linha` tem de dar a frente -- e o contrato antigo."""
        im = folha(2, TODAS)
        self.assertEqual(recortar_frente(im, im.size[0]).getpixel((0, 0)), FRENTE)

    def test_folha_sem_a_linha_devolve_nada(self):
        """Peca fora do layout universal: melhor lacuna que arte errada."""
        curta = Image.new("RGBA", (128, ALTURA), (0, 0, 0, 0))
        self.assertIsNone(recortar_frente(curta, 128, linha=3))


class TesteEnderecoDoFrame(unittest.TestCase):
    """O endereco que o renderer usa: x + (direcao * frames + k) * 64."""

    def test_a_conta_do_endereco_bate_com_o_layout(self):
        frames, x_anim = 3, 640
        # direcao 0 (frente), frame 0 -> o proprio x da animacao
        self.assertEqual(x_anim + (0 * frames + 0) * ALTURA, 640)
        # direcao 0, frame 2
        self.assertEqual(x_anim + (0 * frames + 2) * ALTURA, 768)
        # direcao 1 (costas), frame 0 -> pula o bloco inteiro da frente
        self.assertEqual(x_anim + (1 * frames + 0) * ALTURA, 832)
        # a ultima direcao nao pode passar da largura reservada
        largura = frames * ALTURA * len(DIRECOES)
        ultimo = (len(DIRECOES) - 1) * frames + (frames - 1)
        self.assertLess(ultimo * ALTURA, largura)


if __name__ == "__main__":
    unittest.main()
