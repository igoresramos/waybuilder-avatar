"""Nome de peca e rotulo de slot em pt-BR -- a tela nao mostra id cru.

Os mapas vivem em `nomes/` e sao traduzidos a mao. O build so junta, valida e
emite: `nome_ptbr` por item e `slots` no topo do catalogo. O nome original
continua em `nome`, como fallback e para depurar id dessincronizado.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build import NOMES, ler_nomes_ptbr, ler_rotulos_de_slot

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGO = os.path.join(RAIZ, "saida", "catalogo.json")


class TestMapas(unittest.TestCase):
    def test_a_uniao_dos_mapas_e_disjunta(self):
        """Id em dois arquivos e conflito de traducao, nao merge."""
        vistos: dict[str, str] = {}
        for a in sorted(os.listdir(NOMES)):
            if not a.endswith(".json") or a == "slots.json":
                continue
            with open(os.path.join(NOMES, a), encoding="utf-8") as f:
                for k in json.load(f):
                    self.assertNotIn(k, vistos, f"{k} em {a} e em {vistos.get(k)}")
                    vistos[k] = a

    def test_nenhum_nome_traduzido_e_vazio(self):
        for k, v in ler_nomes_ptbr().items():
            self.assertTrue(v and v.strip(), f"{k} traduzido para vazio")

    def test_dois_slots_nao_dividem_o_mesmo_rotulo(self):
        """A casa e identificada pelo rotulo: dois iguais viram a mesma casa
        aos olhos do jogador."""
        rotulos = ler_rotulos_de_slot()
        invertido: dict[str, str] = {}
        for slot, rotulo in rotulos.items():
            self.assertNotIn(
                rotulo, invertido,
                f"`{slot}` e `{invertido.get(rotulo)}` mostram {rotulo!r}")
            invertido[rotulo] = slot


@unittest.skipUnless(os.path.isfile(CATALOGO), "precisa de saida/catalogo.json")
class TestCatalogoTraduzido(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CATALOGO, encoding="utf-8") as f:
            cls.cat = json.load(f)

    def test_todo_item_tem_nome_em_ptbr(self):
        sem = [i["id"] for i in self.cat["itens"] if not i.get("nome_ptbr")]
        self.assertEqual(sem, [], f"{len(sem)} itens sem nome_ptbr")

    def test_o_nome_original_continua_disponivel(self):
        sem = [i["id"] for i in self.cat["itens"] if not i.get("nome")]
        self.assertEqual(sem, [], "item sem nome original perde o fallback")

    def test_todo_slot_do_catalogo_tem_rotulo(self):
        rotulos = self.cat.get("slots", {})
        slots = {i["slot"] for i in self.cat["itens"]}
        sem = sorted(s for s in slots if not rotulos.get(s))
        self.assertEqual(sem, [], f"{len(sem)} slots sem rotulo")


if __name__ == "__main__":
    unittest.main()
