"""A cor que o app oferece tem de ser real e aplicavel na peca.

Tres regras, medidas no acervo e confirmadas no gerador oficial:

- a rampa de ORIGEM sai do canal, nao do material: 41 canais declaram um
  `base` proprio (`cloth.brown`, `body.lpcr.ivory`) e o app usava o `base` do
  material -- recolor que nao casava pixel nenhum
  (`scripts/generateSources/item-helper.js:55-66`).
- alguns canais trazem a rampa de origem embutida (`source`), e ela vence a
  busca por paleta (`sources/state/palettes.ts:179-182`).
- faixa do atlas que a peca nao declara em `variants` nao e cor da peca: sao
  arquivos soltos no diretorio (`_leather`, `crown_red`), e o gerador so
  oferece o que esta declarado (`components/tree/ItemWithVariants.ts`).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import base_do_canal, faixas_declaradas, normalizar_recolors

METAS = {
    "cloth": {"default": "ulpc", "base": "white"},
    "hair": {"default": "ulpc", "base": "orange"},
    "body": {"default": "ulpc", "base": "light"},
}


class TestBaseDoCanal(unittest.TestCase):
    """`applyRecolorDefaults` do gerador, regra por regra."""

    def test_sem_base_cai_no_padrao_do_material(self):
        self.assertEqual(base_do_canal("hair", None, METAS), "ulpc.orange")

    def test_base_sem_ponto_ganha_a_versao_padrao(self):
        """`base: "brown"` no material `cloth` quer dizer `ulpc.brown`."""
        self.assertEqual(base_do_canal("cloth", "brown", METAS), "ulpc.brown")

    def test_base_com_ponto_manda_inteiro(self):
        self.assertEqual(base_do_canal("body", "lpcr.ivory", METAS), "lpcr.ivory")

    def test_material_desconhecido_nao_quebra_o_build(self):
        self.assertIsNone(base_do_canal("inexistente", None, METAS))


class TestNormalizarRecolorsComBase(unittest.TestCase):
    def test_todo_canal_sai_com_a_rampa_de_origem_resolvida(self):
        """Sem isto o app teria de reimplementar a regra -- e reimplementou
        errado: usava sempre o `base` do material."""
        canais = normalizar_recolors(
            {"material": "hair", "palettes": ["ulpc", "all.lpcr"]}, METAS
        )
        self.assertEqual(canais, [{
            "nome": "cor", "material": "hair",
            "paletas": ["ulpc", "all.lpcr"], "base": "ulpc.orange",
        }])

    def test_o_base_proprio_do_canal_vence_o_do_material(self):
        canais = normalizar_recolors({
            "color_1": {"material": "cloth", "base": "brown",
                        "palettes": ["ulpc"]},
        }, METAS)
        self.assertEqual(canais[0]["base"], "ulpc.brown")

    def test_source_vira_a_rampa_de_origem_embutida(self):
        """`getBasePalette` devolve o `source` direto quando ele existe."""
        canais = normalizar_recolors({
            "material": "cloth", "palettes": ["ulpc"],
            "source": ["#111111", "#222222"],
        }, METAS)
        self.assertEqual(canais[0]["fonte"], ["#111111", "#222222"])


class TestFaixasDeclaradas(unittest.TestCase):
    """A faixa e uma cor da peca so quando a peca a declara em `variants`."""

    def test_filtra_arquivo_solto_que_nao_e_variante(self):
        achadas = ["_leather", "black", "blue"]
        self.assertEqual(
            faixas_declaradas(achadas, ["black", "blue"]), ["black", "blue"]
        )

    def test_espaco_na_declaracao_vira_underscore_no_arquivo(self):
        """`variantToFilename` do gerador: `"kite blue blue"` e
        `kite_blue_blue.png`."""
        self.assertEqual(
            faixas_declaradas(["kite_blue_blue", "kite_gray"],
                              ["kite blue blue", "kite gray"]),
            ["kite_blue_blue", "kite_gray"],
        )

    def test_peca_sem_variants_declaradas_mantem_o_que_achou(self):
        """4 pecas do acervo tem faixa e nao declaram `variants`. Filtrar por
        lista vazia apagaria a peca inteira."""
        self.assertEqual(faixas_declaradas(["black", "blue"], []),
                         ["black", "blue"])

    def test_formato_novo_nao_e_faixa_e_passa_intacto(self):
        """`None` = a cor vem da paleta, nao do arquivo."""
        self.assertEqual(faixas_declaradas([None], ["black"]), [None])

    def test_nunca_apaga_a_peca_inteira(self):
        """Se nada casar, e a declaracao que esta errada -- perder a arte seria
        pior que oferecer uma cor a mais."""
        self.assertEqual(faixas_declaradas(["spear"], ["medium", "light"]),
                         ["spear"])


if __name__ == "__main__":
    unittest.main()
