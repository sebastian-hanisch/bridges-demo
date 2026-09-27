"""Jede Zahl aus README und Konstanten-Kommentar, nachgerechnet über die echten Auswertungsfunktionen (Median über 5 feste Instanzen, Seeds 100000-100004)."""

from functools import lru_cache

import brg_constants as C
import brg_evaluation as ev
from brg_evaluation import Settings


@lru_cache(maxsize=None)
def _crit():
    return {r["blocked"]: r for r in ev.critical_sweep(C.CRIT_SIDE)}


def _pct(rows, nt, key, sh):
    return round(rows[sh][(nt, key)][0] * 100)


def test_critical_shares_over_the_blocked_share():
    rows = _crit()
    assert _pct(rows, "grid", "bridge", 0.0) == 0 and _pct(rows, "grid", "artic", 0.0) == 0
    assert [_pct(rows, "grid", "bridge", sh) for sh in (0.1, 0.2, 0.3, 0.4, 0.5)] == [1, 4, 11, 24, 44]
    assert [_pct(rows, "grid", "artic", sh) for sh in (0.1, 0.2, 0.3, 0.4, 0.5)] == [2, 6, 14, 26, 43]
    assert _pct(rows, "random", "bridge", 0.0) == 5 and _pct(rows, "random", "artic", 0.0) == 10


def test_both_critical_shares_rise_monotonically_up_to_the_threshold():
    rows = _crit()
    shares = [sh for sh in sorted(rows) if sh <= 0.5]
    for key in ("bridge", "artic"):
        vals = [rows[sh][("grid", key)][0] for sh in shares]
        assert vals == sorted(vals)


def test_density_of_random_graphs():
    rows = {r["factor"]: r for r in ev.density_sweep(C.DENSITY_N, C.DENSITY_FACTORS)}
    assert [round(rows[f]["bridge_share"] * 100) for f in C.DENSITY_FACTORS] == [100, 58, 30, 21, 10, 4, 1, 0]


def test_cost_ratio_grows_with_the_size():
    rows = ev.cost_sweep(Settings(blocked=0.3), C.COST_SIDES)
    assert [round(r["ratio"]) for r in rows] == [34, 79, 143, 227, 330, 452]
    assert all(2.0 <= r["ratio"] / r["n"] <= 2.6 for r in rows[1:])            # etwa das 2.3-Fache von n


def test_damage_concentration_and_cut_only_articulation_points():
    rows = {r["blocked"]: r for r in ev.pareto_sweep()}
    assert [round(rows[sh][("grid", "pareto")] * 100) for sh in (0.2, 0.3, 0.4, 0.5)] == [25, 33, 61, 58]
    assert [round(rows[sh][("random", "pareto")] * 100) for sh in (0.2, 0.3, 0.4, 0.5)] == [21, 23, 28, 33]
    assert max(rows[sh][(nt, "cut_only")] for sh in rows for nt in C.NETTYPES) <= 0.02


def test_augmentation_need_against_bridges():
    rows = {r["blocked"]: r for r in ev.augmentation_sweep(C.CRIT_SIDE, (0.1, 0.2, 0.3, 0.4, 0.5), "grid")}
    assert [rows[sh]["need"] for sh in (0.1, 0.2, 0.3, 0.4, 0.5)] == [3.0, 9.0, 21.0, 30.0, 26.0]
    assert [rows[sh]["bridges"] for sh in (0.1, 0.2, 0.3, 0.4, 0.5)] == [6.0, 23.0, 56.0, 100.0, 106.0]
    assert all(0.24 <= rows[sh]["need"] / rows[sh]["bridges"] <= 0.5 for sh in rows)          # ein Viertel bis die Hälfte


def test_zero_blocked_grid_has_no_critical_elements():
    a = ev.analyse(Settings("city", 20, 0.0, "grid", 100000))
    assert a.ll.bridges == [] and a.ll.articulation == set()
