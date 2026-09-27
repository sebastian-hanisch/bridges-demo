"""Korrektheits-Kette: Brücken, Artikulationspunkte, Blöcke gegen networkx; naiv == Low-Link; Blockbaum; Schaden und Verstärkung gegen Brute-Force; Buchführung."""

import random

import networkx as nx
import pytest

import brg_algorithm as A
import brg_scenario as S


def _graph(inst_or_pair):
    if isinstance(inst_or_pair, tuple):
        n, edges = inst_or_pair
        pairs = [(u, v) for u, v in edges]
    else:
        n, pairs = inst_or_pair.n, [(u, v) for u, v, _ in inst_or_pair.edges]
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(pairs)
    return g


def _instances():
    out = [S.textbook_instance()]
    for side in (2, 3, 5, 8):
        for nettype in S.C.NETTYPES:
            for blocked in (0.0, 0.2, 0.45, 0.5, 0.6, 0.9, 1.0):
                for seed in (1, 2, 3):
                    out.append(S.generate(side, blocked, nettype, seed))
    return out


INSTANCES = _instances()          # 169


def _special():
    return [(1, []), (2, []), (2, [(0, 1)]), (3, [(0, 1), (1, 2)]), (3, [(0, 1), (1, 2), (0, 2)]), (6, [(i, i + 1) for i in range(5)]), (6, [(0, i) for i in range(1, 6)]),
            (5, [(i, j) for i in range(5) for j in range(i + 1, 5)]), (6, [(i, (i + 1) % 6) for i in range(6)]), (7, [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (5, 6)]), (5, [])]


def _canonical_edges(blocks):
    return {frozenset(tuple(sorted(e)) for e in b) for b in blocks}


# --- 1. Brücken, Artikulationspunkte, Blöcke == networkx ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("order", ["fixed", "shuffled"])
def test_low_link_matches_networkx_on_all_instances(order):
    assert len(INSTANCES) == 169
    for inst in INSTANCES:
        g = _graph(inst)
        adj = A.adjacency(inst.n, inst.edges, order, seed=inst.seed)
        ll = A.low_link(adj)
        assert sorted(ll.bridges) == sorted(tuple(sorted(e)) for e in nx.bridges(g)), (inst.kind, inst.nettype, inst.blocked, inst.seed)
        assert ll.articulation == set(nx.articulation_points(g))
        want_blocks = {frozenset(tuple(sorted(e)) for e in b) for b in nx.biconnected_component_edges(g)}
        assert _canonical_edges(ll.blocks) == want_blocks and len(ll.blocks) == len(want_blocks)


def test_special_cases_match_networkx():
    for n, edges in _special():
        g = _graph((n, edges))
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges])
        ll = A.low_link(adj)
        assert sorted(ll.bridges) == sorted(tuple(sorted(e)) for e in nx.bridges(g))
        assert ll.articulation == set(nx.articulation_points(g))
        assert _canonical_edges(ll.blocks) == {frozenset(tuple(sorted(e)) for e in b) for b in nx.biconnected_component_edges(g)}


def test_naive_equals_low_link():
    for inst in INSTANCES[::2]:
        adj = A.adjacency(inst.n, inst.edges)
        ll = A.low_link(adj)
        br, _ = A.bridges_naive(adj)
        ar, _ = A.articulation_naive(adj)
        assert br == sorted(ll.bridges) and ar == ll.articulation
    for n, edges in _special():
        adj = A.adjacency(n, [(u, v, 1.0) for u, v in edges])
        ll = A.low_link(adj)
        assert A.bridges_naive(adj)[0] == sorted(ll.bridges) and A.articulation_naive(adj)[0] == ll.articulation


def test_result_sets_do_not_depend_on_the_neighbour_order():
    for inst in INSTANCES[::5]:
        a = A.low_link(A.adjacency(inst.n, inst.edges, "fixed"))
        b = A.low_link(A.adjacency(inst.n, inst.edges, "shuffled", seed=7))
        assert sorted(a.bridges) == sorted(b.bridges) and a.articulation == b.articulation and _canonical_edges(a.blocks) == _canonical_edges(b.blocks)


# --- 2. Blöcke, Blockbaum ------------------------------------------------------------------------------------------------------------------------


def test_blocks_partition_the_edges_and_form_a_forest():
    for inst in INSTANCES:
        adj = A.adjacency(inst.n, inst.edges)
        ll = A.low_link(adj)
        all_edges = [e for b in ll.blocks for e in b]
        assert len(all_edges) == len(set(all_edges)) == inst.m                       # jede Straße in genau einem Block
        singles = [next(iter(b)) for b in ll.blocks if len(b) == 1]
        assert sorted(singles) == sorted(ll.bridges)                                  # Blöcke mit einer Straße sind genau die Brücken
        for b in ll.blocks:
            if len(b) >= 3 or (len(b) == 2):
                bg = nx.Graph(list(b))
                assert nx.is_biconnected(bg) or len(b) < 3
        bct = nx.Graph(A.block_cut_tree(ll))
        assert nx.is_forest(bct) if bct.number_of_nodes() else True
        # zwei Blöcke teilen höchstens einen Knoten, und der ist ein Artikulationspunkt
        nodes = [set(A.block_nodes(b)) for b in ll.blocks]
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                common = nodes[i] & nodes[j]
                assert len(common) <= 1 and common <= ll.articulation


def test_every_block_of_three_or_more_edges_is_biconnected():
    inst = S.generate(8, 0.3, "grid", 5)
    ll = A.low_link(A.adjacency(inst.n, inst.edges))
    big = [b for b in ll.blocks if len(b) >= 3]
    assert big and all(nx.is_biconnected(nx.Graph(list(b))) for b in big)


# --- 3. Schaden gegen Brute-Force ----------------------------------------------------------------------------------------------------------------


def test_damage_matches_bruteforce_and_is_positive_exactly_for_critical_elements():
    checked = 0
    for inst in INSTANCES[::2]:
        if inst.n > 70:
            continue
        adj = A.adjacency(inst.n, inst.edges)
        ll = A.low_link(adj)
        d, ranking = A.damages(adj, ll)
        for (kind, el), val in d.items():
            assert val == A.damage_bruteforce(adj, "bridge" if kind == "bridge" else "cut", el) and val > 0
            checked += 1
        assert [v for _, v in ranking] == sorted((v for _, v in ranking), reverse=True)
        # nicht kritische Straßen und Kreuzungen: kein Schaden
        for u, v, _ in inst.edges:
            if (u, v) not in set(ll.bridges):
                assert A.damage_bruteforce(adj, "bridge", (u, v)) == 0
        for x in range(inst.n):
            if x not in ll.articulation:
                assert A.damage_bruteforce(adj, "cut", x) == 0
    assert checked > 100


def test_damage_by_hand_on_the_bridge_city():
    inst = S.textbook_instance()
    adj = A.adjacency(inst.n, inst.edges)
    ll = A.low_link(adj)
    d, ranking = A.damages(adj, ll)
    assert sorted(ll.bridges) == [(0, 10), (3, 4), (6, 8), (8, 9)] and ll.articulation == {0, 3, 4, 6, 8}
    assert d[("bridge", (3, 4))] == 5 * 6 and d[("bridge", (0, 10))] == 10 and d[("bridge", (8, 9))] == 10 and d[("bridge", (6, 8))] == 2 * 9
    assert d[("cut", 3)] == 45 - 6 - 15 and d[("cut", 4)] == 45 - 10 - 10 and d[("cut", 0)] == 45 - 36 and ranking[0][1] >= ranking[-1][1]      # von Hand: D trennt 4 | 6, E trennt 5 | 5, A trennt K ab
    assert ranking[0] == (("bridge", (3, 4)), 30)


# --- 4. Verstärkung -------------------------------------------------------------------------------------------------------------------------------


def _random_connected_with_bridges(rng, n):
    g = nx.random_labeled_tree(n, seed=rng.randrange(10 ** 6)) if hasattr(nx, "random_labeled_tree") else nx.random_tree(n, seed=rng.randrange(10 ** 6))
    edges = {tuple(sorted(e)) for e in g.edges}
    for _ in range(rng.randrange(0, 3)):
        a, b = rng.sample(range(n), 2)
        edges.add((min(a, b), max(a, b)))
    return sorted(edges)


def test_augmentation_need_equals_bruteforce_minimum():
    rng = random.Random(11)
    mismatches, checked = [], 0
    for _ in range(70):
        n = rng.randrange(3, 8)
        edges = _random_connected_with_bridges(rng, n)
        adj = A.adjacency(n, edges)
        ll = A.low_link(adj)
        total, detail, leaves = A.augmentation_need(adj, ll)
        want = A.brute_force_augmentation(n, [(u, v, 1.0) for u, v in edges], limit=4)
        checked += 1
        if total != want:
            mismatches.append((n, edges, total, want))
    assert checked == 70 and not mismatches, mismatches[:3]


def test_augmentation_special_cases():
    path = (6, [(i, i + 1) for i in range(5)])
    ll = A.low_link(A.adjacency(*[path[0], [(u, v, 1.0) for u, v in path[1]]]))
    total, detail, leaves = A.augmentation_need(A.adjacency(path[0], path[1]), ll)
    assert total == 1 and detail == [(0, 2, 1)] and sorted(leaves) == [0, 5]
    star = (7, [(0, i) for i in range(1, 7)])
    assert A.augmentation_need(A.adjacency(*star))[0] == 3
    cycle = (6, [(i, (i + 1) % 6) for i in range(6)])
    assert A.augmentation_need(A.adjacency(*cycle))[0] == 0
    inst = S.textbook_instance()
    total, detail, leaves = A.augmentation_need(A.adjacency(inst.n, inst.edges))
    assert total == 1 and detail == [(0, 2, 1)] and sorted(leaves) == [9, 10]


# --- 5. Buchführung ------------------------------------------------------------------------------------------------------------------------------


def test_low_link_steps_are_n_plus_two_m_and_naive_steps_recounted():
    for inst in INSTANCES[::5]:
        adj = A.adjacency(inst.n, inst.edges, "shuffled", seed=3)
        ll = A.low_link(adj)
        assert ll.steps == inst.n + 2 * inst.m                                        # alle Komponenten werden besucht
        # naive Schritte: eine Komponentenzählung ohne Entfernen + je Straße eine Zählung
        base_steps = A._component_count(adj)[1]
        assert base_steps == inst.n + 2 * inst.m
        br, st = A.bridges_naive(adj)
        assert st == base_steps * (1 + 0) + sum(A._component_count(adj, skip_edge=(u, v))[1] for u in range(inst.n) for v in adj[u] if u < v)


def test_events_are_complete_and_flags_agree_with_the_results():
    inst = S.generate(7, 0.3, "grid", 4)
    ll = A.low_link(A.adjacency(inst.n, inst.edges))
    discovers = [e for e in ll.events if e[0] == "discover"]
    finishes = [e for e in ll.events if e[0] == "finish"]
    assert len(finishes) == inst.n and len(discovers) == inst.n - len(ll.comp_size)
    assert sum(1 for e in finishes if e[4]) == len(ll.bridges)
    assert {e[2] for e in finishes if e[5]} <= ll.articulation                # das Flag gehört zum Elternknoten p: er trennt den Teilbaum von u ab


def test_textbook_by_hand():
    inst = S.textbook_instance()
    adj = A.adjacency(inst.n, inst.edges)
    ll = A.low_link(adj)
    assert inst.n == 11 and inst.m == 13 and len(ll.comp_size) == 1
    assert len(ll.blocks) == 6 and sorted(len(b) for b in ll.blocks) == [1, 1, 1, 1, 4, 5]
    assert [S.TEXTBOOK_LABELS[v] for v in sorted(ll.articulation)] == ["A", "D", "E", "G", "I"]
    bct = A.block_cut_tree(ll)
    assert len(bct) == sum(1 for b in ll.blocks for v in A.block_nodes(b) if v in ll.articulation)


def test_invalid_order_raises():
    with pytest.raises(ValueError):
        A.adjacency(3, [], "sorted")
