"""Auswertung: Analyse, Sweeps, Feldbelegung."""

import networkx as nx

import brg_constants as C
import brg_evaluation as ev
from brg_evaluation import Settings


def test_analysis_fields_are_consistent_with_networkx():
    for s in (Settings(), Settings("city", 9, 0.5, "grid", 4), Settings("city", 9, 0.5, "random", 4), Settings("textbook")):
        a = ev.analyse(s, naive=True)
        g = nx.Graph()
        g.add_nodes_from(range(a.n))
        g.add_edges_from((u, v) for u, v, _ in a.inst.edges)
        comps = sorted(nx.connected_components(g), key=len, reverse=True)
        assert a.c == len(comps) and a.largest == len(comps[0])
        lc = comps[0]
        assert a.lc_edges == g.subgraph(lc).number_of_edges()
        assert a.lc_bridges == sum(1 for u, v in nx.bridges(g) if u in lc) and a.lc_artic == len({x for x in nx.articulation_points(g) if x in lc})
        assert abs(a.bridge_share - a.lc_bridges / a.lc_edges) < 1e-12 if a.lc_edges else a.bridge_share == 0.0
        assert a.naive_steps > a.low_steps and a.low_steps == a.n + 2 * a.m
        assert len(a.ranking) == len(a.ll.bridges) + len(a.ll.articulation) and a.total_damage == sum(v for _, v in a.ranking)
        assert 0.0 <= a.pareto <= 1.0


def test_naive_is_skipped_by_default():
    a = ev.analyse(Settings("city", 6, 0.3, "grid", 1))
    assert a.naive_steps == 0 and a.low_steps == a.n + 2 * a.m


def test_pareto_and_damage_edge_cases():
    a = ev.analyse(Settings("city", 6, 0.0, "grid", 1))                 # ungesperrtes Raster: nichts kritisch
    assert a.ranking == [] and a.pareto == 0.0 and a.total_damage == 0 and a.aug_lc == 0
    b = ev.analyse(Settings("city", 4, 1.0, "grid", 1))                 # alles gesperrt: keine Straße
    assert b.m == 0 and b.ranking == [] and b.c == b.n


def test_sweeps_have_the_expected_shape_and_monotone_parts():
    rows = ev.critical_sweep(10, shares=(0.0, 0.3, 0.5))
    assert [r["blocked"] for r in rows] == [0.0, 0.3, 0.5]
    for nt in C.NETTYPES:
        for key in ("bridge", "artic", "giant"):
            for r in rows:
                med, lo, hi = r[(nt, key)]
                assert lo <= med <= hi <= 1.0
    assert rows[0][("grid", "bridge")][0] == 0.0 and rows[0][("grid", "bridge")][0] <= rows[1][("grid", "bridge")][0] <= rows[2][("grid", "bridge")][0]
    dens = ev.density_sweep(60, (0.5, 1.0, 3.0), seeds=range(100000, 100003))
    assert dens[0]["bridge_share"] >= dens[1]["bridge_share"] >= dens[2]["bridge_share"]
    cost = ev.cost_sweep(Settings(blocked=0.3), sides=(4, 6), seeds=range(100000, 100003))
    assert all(r["naive"] > r["low"] and r["ratio"] > 1 for r in cost) and cost[1]["ratio"] > cost[0]["ratio"]
    aug = ev.augmentation_sweep(10, (0.1, 0.3), "grid", seeds=range(100000, 100003))
    assert all(r["need"] <= r["bridges"] for r in aug)
    par = ev.pareto_sweep(10, (0.3,), seeds=range(100000, 100003))
    assert 0.0 <= par[0][("grid", "pareto")] <= 1.0


def test_median_over_seeds():
    med, lo, hi = ev.median_over_seeds(lambda sd: float(sd - 100000), seeds=range(100000, 100005))
    assert med == 2.0 and abs(lo - 0.4) < 1e-9 and abs(hi - 3.6) < 1e-9
