"""O catalogo emitido carrega slot, caminho e grupos -- spec, decisao 6b.

Roda contra `saida/catalogo.json`, o artefato versionado que o app consome.
"""
import json
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(RAIZ, "saida", "catalogo.json")


@unittest.skipUnless(os.path.isfile(CATALOGO), "precisa de saida/catalogo.json")
class TestCatalogo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CATALOGO, encoding="utf-8") as f:
            cls.cat = json.load(f)
        cls.itens = cls.cat["itens"]

    def test_todo_item_declara_slot(self):
        sem = [i["id"] for i in self.itens if not i.get("slot")]
        self.assertEqual(sem, [], f"{len(sem)} itens sem slot")

    def test_todo_item_declara_caminho_de_navegacao(self):
        sem = [i["id"] for i in self.itens if not i.get("caminho")]
        self.assertEqual(sem, [], f"{len(sem)} itens sem caminho")

    def test_ha_muito_mais_slots_do_que_categorias(self):
        """104 slots contra 10 categorias -- o achatamento que @3 fazia."""
        slots = {i["slot"] for i in self.itens}
        categorias = {i["categoria"] for i in self.itens}
        self.assertGreater(len(slots), 5 * len(categorias), f"{len(slots)} slots")

    def test_o_slot_head_agrupa_pecas_de_varios_caminhos(self):
        caminhos = {"/".join(i["caminho"]) for i in self.itens if i["slot"] == "head"}
        self.assertIn("head/heads/human", caminhos)
        self.assertGreater(len(caminhos), 1)

    def test_pecas_do_caminho_head_ocupam_slots_distintos(self):
        """Cabeca, nariz e olhos coexistem: nao e um slot so."""
        slots = {i["slot"] for i in self.itens if i["caminho"][0] == "head"}
        self.assertIn("head", slots)
        self.assertIn("nose", slots)
        self.assertGreater(len(slots), 5)

    def test_pecas_homonimas_de_slots_diferentes_nao_se_fundem(self):
        """"Long Topknot" existe como `hair` e como `ponytail`.

        Sao pecas distintas que coexistem no boneco -- o cabelo e a extensao.
        Com o id derivado da categoria, uma sobrescrevia a outra em silencio,
        no catalogo e no proprio atlas.
        """
        homonimas = [i for i in self.itens if i["nome"] == "Long Topknot"]
        slots = sorted(i["slot"] for i in homonimas)
        self.assertEqual(slots, ["hair", "ponytail"])

    def test_todo_id_e_unico(self):
        vistos: dict[str, int] = {}
        for i in self.itens:
            vistos[i["id"]] = vistos.get(i["id"], 0) + 1
        repetidos = {k: v for k, v in vistos.items() if v > 1}
        self.assertEqual(repetidos, {})

    def test_o_catalogo_traz_os_grupos_de_navegacao(self):
        grupos = self.cat.get("grupos")
        self.assertTrue(grupos, "catalogo sem mapa de grupos")
        self.assertEqual(grupos["head/heads/human"]["rotulo"], "Human Heads")
        self.assertIn("prioridade", grupos["head"])


if __name__ == "__main__":
    unittest.main()
