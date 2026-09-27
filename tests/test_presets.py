"""Presets: gültige Werte und jede Zahl der Hilfetexte gegen die echten Auswertungsfunktionen."""

import brg_constants as C
import brg_evaluation as ev
from brg_evaluation import Settings
from brg_presets import PRESET_KEYS, SETTING_SPECS


def _settings(name):
    p = C.PRESETS[name]
    return Settings(p["kind"], p.get("side", C.DEFAULT_SIDE), p.get("blocked", 0.0), p.get("nettype", "grid"), p.get("seed", C.DEFAULT_SEED), p.get("order", "fixed"))


def _has(name, *values):
    for v in values:
        assert v in C.PRESET_HELP[name], (name, v)


def test_every_preset_has_valid_values_and_a_help_text():
    assert list(C.PRESETS) == list(C.PRESET_HELP) and len(C.PRESETS) == 9
    for name, p in C.PRESETS.items():
        assert set(p) <= set(PRESET_KEYS) and {"kind", "step"} <= set(p), name
        assert p["step"] in C.STEPS
        for key, state_key in PRESET_KEYS.items():
            if key in p and state_key in SETTING_SPECS:
                spec = SETTING_SPECS[state_key]
                assert spec.caster(p[key]) == p[key], (name, key)
                if spec.lo is not None:
                    assert spec.lo <= p[key] <= spec.hi, (name, key)
        assert C.PRESET_HELP[name].strip()


def test_help_textbook_and_standard():
    a = ev.analyse(_settings("Brückenstadt (Lehrbuch)"), naive=True)
    assert (a.n, a.m, len(a.ll.bridges), len(a.ll.articulation)) == (11, 13, 4, 5)
    _has("Brückenstadt (Lehrbuch)", "11 Kreuzungen", "13 Straßen", "4 Brücken", "5 Artikulationspunkte")
    a = ev.analyse(_settings("Standardfall (Voreinstellung)"))
    assert (a.n, a.m, a.c, len(a.ll.bridges), len(a.ll.articulation), a.lc_bridges, a.lc_edges, round(a.bridge_share * 1000), a.largest_block_edges, len(a.ll.blocks)) == (144, 185, 4, 21, 17, 20, 184, 109, 164, 22)
    _has("Standardfall (Voreinstellung)", "185 Straßen, 4 Komponenten", "21 Brücken", "17 Artikulationspunkte", "184 Straßen", "20 Brücken (10.9 %)", "164 Straßen", "22 Blöcke")


def test_help_low_and_threshold_presets():
    a = ev.analyse(_settings("Kaum gesperrt"))
    assert (a.m, a.c, len(a.ll.bridges), len(a.ll.articulation), a.largest_block_edges, a.aug_lc) == (238, 1, 4, 3, 234, 1)
    _has("Kaum gesperrt", "238 Straßen", "4 Brücken", "3 Artikulationspunkten", "234 von 238", "Eine einzige neue Straße")
    a = ev.analyse(_settings("Nahe der Schwelle"))
    top_key, top_val = a.ranking[0]
    assert (a.largest, a.lc_bridges, a.lc_edges, round(a.bridge_share * 1000), a.lc_artic, round(a.artic_share * 1000), top_key, top_val, a.aug_lc) == (237, 153, 260, 588, 132, 557, ("cut", 151), 18378, 27)
    _has("Nahe der Schwelle", "237 Knoten", "58.8 %", "153 von 260", "55.7 %", "132 Kreuzungen", "Kreuzung 151", "18378", "27 neuen Straßen")


def test_help_random_presets():
    a = ev.analyse(_settings("Zufallsgraph, dicht"))
    deg = [len(x) for x in a.adj]
    pend = sum(1 for u, v in a.ll.bridges if deg[u] == 1 or deg[v] == 1)
    assert (a.n, a.m, len(a.ll.bridges), pend, len(a.ll.articulation), round(a.bridge_share * 1000), a.largest_block_edges) == (144, 264, 19, 16, 17, 72, 245)
    _has("Zufallsgraph, dicht", "144 Knoten und 264 Straßen", "19 Brücken (7.2 %)", "16 Stichstraßen", "17 Artikulationspunkte", "245 von 264")
    a = ev.analyse(_settings("Zufallsgraph, dünn"))
    assert (a.m, a.c, a.largest, a.lc_bridges, a.lc_edges, round(a.bridge_share * 1000), a.augmentation) == (132, 31, 105, 47, 123, 382, 20)
    _has("Zufallsgraph, dünn", "132 Straßen", "31 Komponenten", "105 Knoten", "38.2 %", "47 von 123", "20 neue Straßen")


def test_help_skew_cost_and_augmentation_presets():
    a = ev.analyse(_settings("Der Schaden ist schief verteilt"))
    assert (len(a.ll.bridges), len(a.ll.articulation), round(a.pareto * 100), a.ranking[0]) == (136, 123, 71, (("bridge", (146, 166)), 26404))
    _has("Der Schaden ist schief verteilt", "136 Brücken", "123 Artikulationspunkte", "71 %", "146-166", "26404")
    a = ev.analyse(_settings("Aufwand: naiv gegen Low-Link"), naive=True)
    assert (a.naive_steps, a.low_steps, round(a.naive_steps / a.low_steps)) == (169620, 514, 330)
    _has("Aufwand: naiv gegen Low-Link", "169620", "514", "330-Fache")
    a = ev.analyse(_settings("Verstärkung: wie viele Straßen fehlen?"))
    assert a.aug_lc == 1 and sorted(a.leaf_nodes) == [9, 10]
    _has("Verstärkung: wie viele Straßen fehlen?", "J und K", "J-K", "ceil(Blätter / 2)")
