"""Kennzahlen und Sweeps: kritische Straßen und Kreuzungen, Aufwand naiv gegen Low-Link, Ausfallschaden, Verstärkungsbedarf."""

import math
from dataclasses import dataclass

import numpy as np

import brg_algorithm as A
import brg_constants as C
import brg_scenario as S


@dataclass(frozen=True)
class Settings:
    kind: str = "city"
    side: int = C.DEFAULT_SIDE
    blocked: float = C.DEFAULT_BLOCKED
    nettype: str = "grid"
    seed: int = C.DEFAULT_SEED
    order: str = "fixed"


def build(s):
    if s.kind == "textbook":
        return S.textbook_instance()
    return S.generate(s.side, s.blocked, s.nettype, s.seed)


@dataclass
class Analysis:
    inst: object
    adj: list
    ll: object
    naive_bridge_steps: int
    naive_artic_steps: int
    n: int
    m: int
    c: int
    largest: int                 # Knoten der größten Komponente
    largest_root: int
    lc_edges: int                # Straßen in der größten Komponente
    lc_bridges: int              # Brücken in der größten Komponente
    lc_artic: int                # Artikulationspunkte in der größten Komponente
    bridge_share: float          # Brücken / Straßen der größten Komponente
    artic_share: float           # Artikulationspunkte / Knoten der größten Komponente
    big_blocks: int              # Blöcke mit mindestens 3 Straßen
    largest_block_edges: int
    damages: dict
    ranking: list
    total_damage: int
    pareto: float                # Anteil des Gesamtschadens der schlimmsten 10 % der kritischen Elemente
    augmentation: int            # Summe über alle Komponenten
    aug_lc: int                  # größte Komponente
    aug_detail: list
    leaf_nodes: list
    artic_not_bridge_end: int    # Artikulationspunkte, die kein Ende einer Brücke sind

    @property
    def naive_steps(self):
        return self.naive_bridge_steps + self.naive_artic_steps

    @property
    def low_steps(self):
        return self.ll.steps


def analyse(s, naive=False):
    """Analyse einer Instanz; der naive Ausfalltest (teuer) läuft nur mit `naive=True`."""
    inst = build(s)
    adj = A.adjacency(inst.n, inst.edges, s.order, seed=s.seed)
    ll = A.low_link(adj)
    nb = na = 0
    if naive:
        nb = A.bridges_naive(adj)[1]
        na = A.articulation_naive(adj)[1]
    root_big = max(ll.comp_size, key=lambda r: (ll.comp_size[r], -r))
    largest = ll.comp_size[root_big]
    lc_edges = sum(1 for u, v, _ in inst.edges if ll.root[u] == root_big)
    lc_bridges = sum(1 for u, v in ll.bridges if ll.root[u] == root_big)
    lc_artic = sum(1 for x in ll.articulation if ll.root[x] == root_big)
    d, ranking = A.damages(adj, ll)
    total = sum(d.values())
    k = max(1, math.ceil(0.1 * len(ranking))) if ranking else 0
    pareto = (sum(v for _, v in ranking[:k]) / total) if total else 0.0
    aug, detail, leaves = A.augmentation_need(adj, ll)
    aug_lc = next((need for root_v, _, need in detail if root_v == root_big), 0)
    bridge_ends = {x for b in ll.bridges for x in b}
    return Analysis(inst, adj, ll, nb, na, inst.n, inst.m, len(ll.comp_size), largest, root_big, lc_edges, lc_bridges, lc_artic,
                    (lc_bridges / lc_edges) if lc_edges else 0.0, lc_artic / largest, sum(1 for b in ll.blocks if len(b) >= 3), max((len(b) for b in ll.blocks), default=0),
                    d, ranking, total, pareto, aug, aug_lc, detail, leaves, len(ll.articulation - bridge_ends))


def median_over_seeds(func, seeds=C.SWEEP_SEEDS):
    vals = [func(sd) for sd in seeds]
    return float(np.median(vals)), float(np.percentile(vals, 10)), float(np.percentile(vals, 90))


# --- Aufwand: naiv gegen Low-Link --------------------------------------------------------------------------------------------------------------


def cost_sweep(base=Settings(), sides=(4, 6, 8, 10, 12, 14), seeds=C.SWEEP_SEEDS):
    """Elementarschritte für "alle Brücken und Artikulationspunkte": naiver Ausfalltest (beide Fragen) gegen eine Low-Link-Tiefensuche; Median über die festen Instanzen."""
    rows = []
    for side in sides:
        nv, lw, n_nodes = [], [], []
        for sd in seeds:
            a = analyse(Settings("city", side, base.blocked, base.nettype, sd, base.order), naive=True)
            nv.append(a.naive_steps)
            lw.append(a.low_steps)
            n_nodes.append(a.n)
        rows.append({"side": side, "n": side * side, "naive": float(np.median(nv)), "low": float(np.median(lw)), "ratio": float(np.median([x / y for x, y in zip(nv, lw)]))})
    return rows


# --- Kritische Anteile über den Sperranteil und die Dichte ------------------------------------------------------------------------------------------


PERC_SHARES = tuple(round(x * 0.05, 2) for x in range(0, 19))     # 0, 0.05, ..., 0.90


def critical_sweep(side=20, shares=None, seeds=C.SWEEP_SEEDS):
    """Brückenanteil (an den Straßen der größten Komponente), Artikulationsanteil (an ihren Knoten) und Größe der größten Komponente je Sperranteil und Netztyp (Median, 10./90. Perzentil)."""
    shares = tuple(shares) if shares is not None else PERC_SHARES
    rows = []
    for sh in shares:
        row = {"blocked": sh}
        for nt in C.NETTYPES:
            for key, fn in (("bridge", lambda a: a.bridge_share), ("artic", lambda a: a.artic_share), ("giant", lambda a: a.largest / a.n)):
                row[(nt, key)] = median_over_seeds(lambda sd, nt=nt, sh=sh, fn=fn: fn(analyse(Settings("city", side, sh, nt, sd))), seeds)
        rows.append(row)
    return rows


def density_sweep(n=144, factors=(0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0), seeds=C.SWEEP_SEEDS):
    """Zufallsgraph G(n, m) mit m = Faktor * n Straßen: Brückenanteil an allen Straßen (Median); zum Vergleich der Anteil der Knoten, die zu einer Brücke gehören."""
    rows = []
    for f in factors:
        m = int(round(f * n))
        shares, arts = [], []
        for sd in seeds:
            rng = S.make_rng(sd, 8888)
            pairs = S.random_pairs(n, m, rng)
            adj = A.adjacency(n, [(u, v, 1.0) for u, v in pairs])
            ll = A.low_link(adj)
            shares.append(len(ll.bridges) / m)
            arts.append(len(ll.articulation) / n)
        rows.append({"factor": f, "m": m, "bridge_share": float(np.median(shares)), "artic_share": float(np.median(arts))})
    return rows


def augmentation_sweep(side=20, shares=(0.1, 0.2, 0.3, 0.4, 0.5), nettype="grid", seeds=C.SWEEP_SEEDS):
    """Verstärkungsbedarf der größten Komponente und Zahl ihrer Brücken je Sperranteil (Median)."""
    rows = []
    for sh in shares:
        need, br = [], []
        for sd in seeds:
            a = analyse(Settings("city", side, sh, nettype, sd))
            need.append(a.aug_lc)
            br.append(a.lc_bridges)
        rows.append({"blocked": sh, "need": float(np.median(need)), "bridges": float(np.median(br))})
    return rows


def pareto_sweep(side=20, shares=(0.2, 0.3, 0.4, 0.5), seeds=C.SWEEP_SEEDS):
    """Wie stark konzentriert sich der Ausfallschaden? Anteil des Gesamtschadens, den die schlimmsten 10 % der kritischen Elemente tragen (Median), und Anteil der Artikulationspunkte, die kein Ende
    einer Brücke sind (Median), je Sperranteil und Netztyp. Der Gesamtschaden zählt Brücken und Artikulationspunkte je für sich (eine Brücke und ihr Ende sind oft beide kritisch)."""
    rows = []
    for sh in shares:
        row = {"blocked": sh}
        for nt in C.NETTYPES:
            an = [analyse(Settings("city", side, sh, nt, sd)) for sd in seeds]
            row[(nt, "pareto")] = float(np.median([a.pareto for a in an]))
            row[(nt, "cut_only")] = float(np.median([a.artic_not_bridge_end / max(1, len(a.ll.articulation)) for a in an]))
            row[(nt, "bridges")] = float(np.median([len(a.ll.bridges) for a in an]))
        rows.append(row)
    return rows
