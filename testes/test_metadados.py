"""Metadados que a UI de slots precisa e o build ate @4 nao emitia.

- `combina_com`: trim/overlay/fivela pareados ao chapeu por prefixo de nome
- `sem_arte`:    variantes de corpo em que a peca nao aparece
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import (GRUPO_DE_SLOT, grupo_do_slot, normalizar_recolors,
                   parear_por_prefixo, segue_cor_do_corpo, sem_arte_em)


class TestPareamento(unittest.TestCase):
    """`hat`, `hat_trim` e `hat_overlay` sao slots separados por decisao do
    dono. O pareamento nao os funde -- so filtra a grade e permite avisar
    quando o trim fica orfao."""

    def test_casa_trim_com_o_chapeu_de_mesmo_prefixo(self):
        pares = parear_por_prefixo(
            [{"id": "hat_trim/tricorne-captain-trim", "nome": "Tricorne Captain Trim"}],
            [{"id": "hat/tricorne-captain", "nome": "Tricorne Captain"}],
        )
        self.assertEqual(
            pares["hat_trim/tricorne-captain-trim"], ["hat/tricorne-captain"]
        )

    def test_prefere_o_chapeu_de_nome_mais_longo(self):
        """"Tricorne Captain Trim" casa com "Tricorne" e "Tricorne Captain".

        O par certo e o mais especifico -- senao todo trim de tricorne cai no
        chapeu generico.
        """
        pares = parear_por_prefixo(
            [{"id": "hat_trim/t", "nome": "Tricorne Captain Trim"}],
            [
                {"id": "hat/tricorne", "nome": "Tricorne"},
                {"id": "hat/tricorne-captain", "nome": "Tricorne Captain"},
            ],
        )
        self.assertEqual(pares["hat_trim/t"], ["hat/tricorne-captain"])

    def test_acessorio_sem_par_nao_entra_no_mapa(self):
        pares = parear_por_prefixo(
            [{"id": "hat_trim/santa", "nome": "Santa Trim"}],
            [{"id": "hat/tricorne", "nome": "Tricorne"}],
        )
        self.assertEqual(pares, {})


class TestSemArte(unittest.TestCase):
    """A grade mostra a peca NO personagem. Se a peca nao tem arte para o corpo
    atual, a celula mostra o boneco inalterado -- e o preview mente por
    omissao. A UI precisa saber para marcar a celula."""

    def test_lista_os_corpos_sem_arte(self):
        item = {"camadas": [{"corpos": {"male": {}, "female": {}}}]}
        self.assertEqual(sem_arte_em(item, ["male", "female", "pregnant", "teen"]),
                         ["pregnant", "teen"])

    def test_peca_completa_nao_lista_nada(self):
        item = {"camadas": [{"corpos": {"male": {}, "female": {}}}]}
        self.assertEqual(sem_arte_em(item, ["male", "female"]), [])

    def test_basta_uma_camada_ter_o_corpo(self):
        item = {"camadas": [{"corpos": {"male": {}}}, {"corpos": {"female": {}}}]}
        self.assertEqual(sem_arte_em(item, ["male", "female"]), [])


class TestGrupoDeSlot(unittest.TestCase):
    """A UI e um painel de quadradinhos, um por slot. Os grupos so decidem em
    que secao o quadradinho aparece -- nunca exclusividade, que e do slot."""

    def test_cada_slot_cai_num_grupo(self):
        self.assertEqual(grupo_do_slot("hat"), "Chapéu")
        self.assertEqual(grupo_do_slot("hair"), "Cabelo")
        self.assertEqual(grupo_do_slot("shield_pattern"), "Armas")

    def test_slot_desconhecido_nao_some(self):
        """Slot novo no upstream cai num grupo de sobra, com aviso -- nunca
        desaparece da UI em silencio."""
        self.assertEqual(grupo_do_slot("slot_que_nao_existe"), "Outros")

    def test_nenhum_slot_esta_em_dois_grupos(self):
        vistos: dict[str, str] = {}
        for grupo, slots in GRUPO_DE_SLOT.items():
            for s in slots:
                self.assertNotIn(s, vistos, f"{s} em {grupo} e em {vistos.get(s)}")
                vistos[s] = grupo


class TestNormalizarRecolors(unittest.TestCase):
    """O upstream declara cor de dois jeitos; a decisao 3a manda o app ver um.

    359 itens usam o formato direto e 27 declaram dois canais independentes --
    um elmo com metal e tiras de tecido tem duas cores, nao uma.
    """

    # os `meta_<material>.json` dizem em que rampa a arte foi pintada; sem eles
    # o canal sai sem `base` e o app nao tem de onde recolorir
    METAS = {"metal": {"default": "ulpc", "base": "steel"},
             "cloth": {"default": "ulpc", "base": "white"}}

    def test_formato_direto_vira_um_canal(self):
        canais = normalizar_recolors(
            {"material": "metal", "palettes": ["ulpc", "lpcr"]}, self.METAS
        )
        self.assertEqual(canais, [
            {"nome": "cor", "material": "metal", "paletas": ["ulpc", "lpcr"],
             "base": "ulpc.steel"},
        ])

    def test_formato_por_cor_vira_um_canal_por_cor(self):
        canais = normalizar_recolors({
            "color_1": {"material": "metal", "palettes": ["ulpc"]},
            "color_2": {"type_name": "hat_secondary", "label": "Helmet Strands",
                        "material": "cloth", "base": "brown",
                        "palettes": ["ulpc"]},
        }, self.METAS)
        self.assertEqual(canais, [
            {"nome": "color_1", "material": "metal", "paletas": ["ulpc"],
             "base": "ulpc.steel"},
            {"nome": "hat_secondary", "rotulo": "Helmet Strands",
             "material": "cloth", "base": "ulpc.brown", "paletas": ["ulpc"]},
        ])

    def test_sem_recolors_nao_gera_canal(self):
        self.assertEqual(normalizar_recolors(None, self.METAS), [])
        self.assertEqual(normalizar_recolors({}, self.METAS), [])

class TestSegueCorDoCorpo(unittest.TestCase):
    """`match_body_color` -- 79 definitions do acervo.

    Cabeca, nariz, orelha e expressao sao slots SEPARADOS com material `body`.
    Sem a flag, trocar o tom de pele deixa a cabeca de outra cor: o gerador
    forca a cor do corpo nesses itens em tempo de render
    (`sources/state/palettes.ts:119-123`).
    """

    def test_marca_o_item_que_segue_a_cor_do_corpo(self):
        self.assertTrue(segue_cor_do_corpo({"match_body_color": True}))

    def test_item_comum_nao_e_marcado(self):
        self.assertFalse(segue_cor_do_corpo({}))
        self.assertFalse(segue_cor_do_corpo({"match_body_color": False}))

if __name__ == "__main__":
    unittest.main()
