"""Slot e caminho de navegacao de uma peca -- spec, decisao 6b.

O slot decide exclusividade e vem do `type_name`. O caminho serve so para a UI
agrupar. Confundir os dois foi o defeito que o prototipo do renderer herdou.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import FONTE, identidade_da_peca, ler_definitions, ler_grupos

TEM_FONTE = os.path.isdir(os.path.join(FONTE, "sheet_definitions"))


def _escrever(raiz: str, rel: str, conteudo: dict) -> None:
    destino = os.path.join(raiz, rel)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(conteudo, f)


class TestSlot(unittest.TestCase):
    def test_slot_vem_do_type_name_e_nao_do_caminho(self):
        """`weapon` mora dentro de `tools/` -- o caminho mentiria aqui."""
        ident = identidade_da_peca(
            os.path.join("tools", "fishing_pole.json"),
            {"name": "Fishing Pole", "type_name": "weapon"},
        )
        self.assertEqual(ident["slot"], "weapon")


class TestCaminho(unittest.TestCase):
    def test_caminho_preserva_a_hierarquia_inteira(self):
        """`head -> heads -> human`, nao so o primeiro segmento."""
        ident = identidade_da_peca(
            os.path.join("head", "heads", "human", "heads_human_elderly_small.json"),
            {"name": "Human Elderly Small", "type_name": "head"},
        )
        self.assertEqual(ident["caminho"], ["head", "heads", "human"])

    def test_peca_na_raiz_de_uma_categoria_tem_caminho_de_um_nivel(self):
        ident = identidade_da_peca(
            os.path.join("head", "wrinkles.json"),
            {"name": "Wrinkles", "type_name": "wrinkles"},
        )
        self.assertEqual(ident["caminho"], ["head"])


class TestGrupos(unittest.TestCase):
    """Os `meta_*.json`, que o build ate @3 pulava junto com os demais."""

    def test_le_prioridade_e_rotulo_de_cada_diretorio(self):
        with tempfile.TemporaryDirectory() as raiz:
            _escrever(raiz, os.path.join("head", "meta_head.json"), {"priority": 20})
            _escrever(
                raiz,
                os.path.join("head", "heads", "human", "meta_human.json"),
                {"priority": 10, "label": "Human Heads"},
            )
            grupos = ler_grupos(raiz)

        self.assertEqual(grupos["head"]["prioridade"], 20)
        self.assertEqual(grupos["head/heads/human"]["prioridade"], 10)
        self.assertEqual(grupos["head/heads/human"]["rotulo"], "Human Heads")

    def test_diretorio_sem_meta_nao_entra_no_mapa(self):
        with tempfile.TemporaryDirectory() as raiz:
            _escrever(raiz, os.path.join("head", "solta.json"), {"type_name": "head"})
            self.assertEqual(ler_grupos(raiz), {})


@unittest.skipUnless(TEM_FONTE, "precisa do clone do LPC (buscar_fonte.sh)")
class TestContraAFonteReal(unittest.TestCase):
    """Regressao contra o acervo no pin, nao contra exemplo inventado."""

    @classmethod
    def setUpClass(cls):
        cls.defs = ler_definitions()

    def test_toda_peca_tem_slot(self):
        sem = [d["_arquivo"] for d in self.defs if not d.get("_slot")]
        self.assertEqual(sem, [], f"{len(sem)} pecas sem slot")

    def test_o_slot_head_cruza_varios_diretorios(self):
        """45 pecas, 6 diretorios, um slot -- o caso que o prototipo errou."""
        dirs = {"/".join(d["_caminho"]) for d in self.defs if d["_slot"] == "head"}
        self.assertGreater(len(dirs), 1, "head deveria vir de varios diretorios")
        self.assertIn("head/heads/human", dirs)

    def test_slots_convivem_dentro_do_mesmo_caminho_de_head(self):
        """Dentro de `head/` ha muitos slots que coexistem, nao um so."""
        slots = {d["_slot"] for d in self.defs if d["_caminho"][0] == "head"}
        self.assertIn("head", slots)
        self.assertIn("nose", slots)
        self.assertGreater(len(slots), 10, f"esperava dezenas de slots, veio {slots}")


if __name__ == "__main__":
    unittest.main()
