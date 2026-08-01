"""Integridade do atlas consolidado -- um PNG por (slot, camada, corpo).

Abre os PNGs de verdade: um offset que cai fora da imagem nao aparece no
catalogo, so no boneco quebrado.
"""
import json
import os
import unittest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "saida")
CATALOGO = os.path.join(SAIDA, "catalogo.json")

try:
    from PIL import Image
    TEM_PIL = True
except ImportError:
    TEM_PIL = False


@unittest.skipUnless(os.path.isfile(CATALOGO), "precisa de saida/catalogo.json")
class TestAtlas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CATALOGO, encoding="utf-8") as f:
            cls.cat = json.load(f)
        cls.variantes = [
            (i["id"], corpo, v)
            for i in cls.cat["itens"]
            for cam in i["camadas"]
            for corpo, v in cam["corpos"].items()
        ]

    def test_toda_variante_aponta_para_um_atlas(self):
        sem = [f"{i}/{c}" for i, c, v in self.variantes if not v.get("arq")]
        self.assertEqual(sem, [], f"{len(sem)} variantes sem atlas")

    def test_o_atlas_existe_em_disco(self):
        faltando = {
            v["arq"] for _, _, v in self.variantes
            if not os.path.isfile(os.path.join(SAIDA, v["arq"]))
        }
        self.assertEqual(faltando, set())

    def test_pecas_do_mesmo_slot_compartilham_atlas(self):
        """O ponto da consolidacao: abrir um picker e um request."""
        porslot = {}
        for i in self.cat["itens"]:
            for cam in i["camadas"]:
                for corpo, v in cam["corpos"].items():
                    porslot.setdefault(i["slot"], set()).add(v["arq"])
        # `hair` tem 89 pecas; sem consolidacao seriam centenas de arquivos
        self.assertLess(len(porslot["hair"]), 20, porslot["hair"])

    @unittest.skipUnless(TEM_PIL, "precisa de Pillow")
    def test_todo_offset_de_cor_cabe_dentro_do_atlas(self):
        alturas: dict[str, int] = {}
        larguras: dict[str, int] = {}
        for _, _, v in self.variantes:
            if v["arq"] not in alturas:
                with Image.open(os.path.join(SAIDA, v["arq"])) as im:
                    larguras[v["arq"]], alturas[v["arq"]] = im.size
        Q = self.cat["recorte"]["altura_do_frame"]
        for ident, corpo, v in self.variantes:
            for cor, y in v["cores"].items():
                self.assertLessEqual(
                    y + Q, alturas[v["arq"]],
                    f"{ident}/{corpo} cor {cor}: y={y} estoura {v['arq']}")
            for a in v["animacoes"]:
                self.assertLessEqual(
                    a["x"] + a["frames"] * Q, larguras[v["arq"]],
                    f"{ident}/{corpo} anim {a['nome']} estoura {v['arq']}")

    @unittest.skipUnless(TEM_PIL, "precisa de Pillow")
    def test_nenhum_atlas_passa_do_limite_de_textura(self):
        """12 grupos passariam de 19.072 px sem o teto -- o canvas falharia."""
        for arq in {v["arq"] for _, _, v in self.variantes}:
            with Image.open(os.path.join(SAIDA, arq)) as im:
                self.assertLessEqual(max(im.size), 16384, f"{arq} = {im.size}")


if __name__ == "__main__":
    unittest.main()
