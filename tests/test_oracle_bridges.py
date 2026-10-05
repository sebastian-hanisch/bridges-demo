"""Unabhängiges Orakel auf kleinen Zufallsgraphen (auch unzusammenhängend): Brücken/Artikulationspunkte/Blöcke gegen networkx, Ausfallschaden durch wirkliches Entfernen
und Paarzählung mit networkx, Verstärkung je Komponente durch Aufzählung aller Straßenmengen (einfacher Graph; Komponenten aus nur einer Straße zählen 1: dort ist die neue Straße parallel)."""

import itertools
import random

import pytest

nx = pytest.importorskip("networkx")

import brg_algorithm as A


def _pairs(g):
    return sum(len(c) * (len(c) - 1) // 2 for c in nx.connected_components(g))


def _min_augmentation(g0, limit=4):
    total = 0
    for comp in nx.connected_components(g0):
        sub = g0.subgraph(comp).copy()
        if not any(True for _ in nx.bridges(sub)):
            continue
        if len(comp) == 2:
            total += 1
            continue
        missing = [p for p in itertools.combinations(sorted(comp), 2) if not sub.has_edge(*p)]
        for k in range(limit + 1):
            if any(not any(True for _ in nx.bridges(nx.Graph(list(sub.edges) + list(extra)))) for extra in itertools.combinations(missing, k)):
                total += k
                break
        else:
            raise AssertionError("Grenze zu klein")
    return total


def test_random_small_graphs_against_networkx_and_enumeration():
    rng = random.Random(1)
    for it in range(200):
        n = rng.randrange(1, 9)
        allp = list(itertools.combinations(range(n), 2))
        rng.shuffle(allp)
        edges = sorted(allp[:rng.randrange(0, min(len(allp), 2 * n) + 1)])
        g = nx.Graph()
        g.add_nodes_from(range(n))
        g.add_edges_from(edges)
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges], "shuffled" if it % 2 else "fixed", seed=it)
        ll = A.low_link(adj)
        assert sorted(ll.bridges) == sorted(tuple(sorted(e)) for e in nx.bridges(g))
        assert ll.articulation == set(nx.articulation_points(g))
        assert {frozenset(b) for b in ll.blocks} == {frozenset(tuple(sorted(e)) for e in b) for b in nx.biconnected_component_edges(g)}
        d, _ = A.damages(adj, ll)
        base = _pairs(g)
        for b in ll.bridges:
            h = g.copy()
            h.remove_edge(*b)
            assert d[("bridge", b)] == base - _pairs(h)
        for x in ll.articulation:
            h = g.copy()
            h.remove_node(x)
            assert d[("cut", x)] == (base - (len(nx.node_connected_component(g, x)) - 1)) - _pairs(h)
        assert A.augmentation_need(adj, ll)[0] == _min_augmentation(g)
