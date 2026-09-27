"""Instanzen: Größen, Sperranteil, Netztypen, Determinismus, Brückenstadt."""

import numpy as np
import pytest

import brg_constants as C
import brg_scenario as S


def test_grid_sizes_and_exact_blocking_count():
    for side in (2, 5, 12):
        total = len(S.grid_edges(side))
        assert total == 2 * side * (side - 1)
        for share in (0.0, 0.3, 0.5, 1.0):
            inst = S.generate(side, share, "grid", 7)
            assert inst.n == side * side and inst.m + len(inst.blocked_edges) == total and len(inst.blocked_edges) == int(round(share * total))
            assert all(u < v for u, v, _ in inst.edges) and list(inst.edges) == sorted(inst.edges)


def test_random_graph_has_the_same_number_of_edges_as_the_blocked_grid_and_is_simple():
    for share in (0.0, 0.4, 0.8):
        g, r = S.generate(9, share, "grid", 3), S.generate(9, share, "random", 3)
        assert r.m == g.m and r.n == g.n and r.blocked_edges == ()
        assert len({(u, v) for u, v, _ in r.edges}) == r.m and all(u < v for u, v, _ in r.edges)


def test_determinism_and_platform_independent_stream():
    a, b = S.generate(8, 0.3, "grid", 5), S.generate(8, 0.3, "grid", 5)
    assert a.edges == b.edges and np.array_equal(a.xy, b.xy) and S.generate(8, 0.3, "grid", 6).edges != a.edges
    inst = S.generate(12, 0.3, "grid", 35)
    assert inst.m == 185 and len(inst.blocked_edges) == 79 and S.generate(20, 0.5, "grid", 27).m == 380


def test_brueckenstadt_shape():
    inst = S.textbook_instance()
    assert inst.n == 11 and inst.m == 13 and inst.kind == "textbook" and inst.labels == S.TEXTBOOK_LABELS
    assert {(u, v) for u, v, _ in inst.edges} == {(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (4, 7), (6, 8), (8, 9), (0, 10)}


def test_errors():
    with pytest.raises(ValueError):
        S.generate(4, 0.1, "wheel", 1)
    with pytest.raises(ValueError):
        S.generate(1, 0.1, "grid", 1)
    assert C.SIDE_MIN >= 2
