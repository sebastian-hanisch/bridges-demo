"""Die Instanz dieser Demo: das Straßennetz eines Distributionsraums als gestörtes Raster (wie in der BFS-und-DFS-Demo, von dort übernommen). Kreuzungen sind die Knoten, Straßen zwischen Nachbarn die Kanten.
Ein Anteil der Straßen ist gesperrt (Baustellen, Hochwasser, Streik); das Netz darf zerfallen. Als zweiter Netztyp gibt es einen **Zufallsgraphen** mit derselben Knoten- und Kantenzahl (die Kanten
verbinden beliebige Kreuzungspaare, die Karte dient nur der Anzeige). Gefragt wird hier, welche einzelne Straße oder Kreuzung nicht ausfallen darf.

Knoten sind von 0 bis n - 1 durchnummeriert (Zeile für Zeile, Knoten 0 liegt unten links); Kanten (u, v, w) mit u < v, sortiert; w = Länge (für die Suchverfahren ohne Bedeutung)."""

import random
from dataclasses import dataclass

import numpy as np

import brg_constants as C


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    edges: tuple                   # ((u, v, w), ...) sortiert
    side: int
    kind: str = "city"
    nettype: str = "grid"
    blocked: float = 0.0
    seed: int = 0
    blocked_edges: tuple = ()      # gesperrte Straßen (u, v), nur zur Anzeige (nur beim Raster)
    labels: tuple = ()             # Knotennamen (nur Lehrbuchbeispiel)

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.edges)


def grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def make_rng(seed, salt):
    """Zufallsquelle mit fester, plattformunabhängiger Zahlenfolge (Python-`random`, nicht numpy: die Instanzen und alle daraus gezählten Zahlen ändern sich nie mit einer Bibliotheksversion)."""
    return random.Random(int(seed) * 1_000_003 + int(salt))


def block(pairs, share, rng):
    """Sperrt genau `round(share * Zahl der Straßen)` Straßen, zufällig und OHNE Rücksicht auf den Zusammenhang. Gibt (verbleibende, gesperrte) zurück."""
    target = int(round(share * len(pairs)))
    order = list(range(len(pairs)))
    rng.shuffle(order)
    removed = set(order[:target])
    kept = [pairs[j] for j in range(len(pairs)) if j not in removed]
    return kept, [pairs[j] for j in sorted(removed)]


def random_pairs(n, m, rng):
    """`m` verschiedene Kanten zwischen zufälligen verschiedenen Knotenpaaren (einfacher Graph)."""
    max_m = n * (n - 1) // 2
    m = min(m, max_m)
    chosen = set()
    while len(chosen) < m:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v:
            continue
        chosen.add((min(u, v), max(u, v)))
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, blocked=C.DEFAULT_BLOCKED, nettype="grid", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if nettype not in C.NETTYPES:
        raise ValueError(f"unbekannter Netztyp {nettype}")
    side = int(side)
    if side < 2:
        raise ValueError("Seitenlänge mindestens 2")
    n = side * side
    rng = make_rng(seed, 4711)
    xy = np.array([[c * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING, r * C.SPACING + rng.uniform(-jitter, jitter) * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    kept, removed = block(grid_edges(side), float(blocked), rng)
    if nettype == "random":
        rng2 = make_rng(seed, 9173)
        kept = random_pairs(n, len(kept), rng2)
        removed = []
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in kept)
    return Instance(xy, edges, side, "city", nettype, float(blocked), int(seed), tuple(removed))


# --- Handgebautes Lehrbuchbeispiel ----------------------------------------------------------------------------------------------------------------


TEXTBOOK_LABELS = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K")


def textbook_instance():
    """Die **Brückenstadt**, 11 Kreuzungen A bis K, 13 Straßen, ein zusammenhängendes Netz: ein Block links (A, B, C, D: Quadrat mit einer Diagonale), ein Block rechts (E, F, G, H: Rundweg), dazwischen
    die Straße D-E; vom Rundweg führt G-I-J als Stichweg weg, und an A hängt die Stichstraße A-K. Von Hand: **4 Brücken** (D-E, G-I, I-J, A-K), **5 Artikulationspunkte** (A, D, E, G, I), 2 Blöcke mit mehr
    als einer Straße, und die beiden Enden J und K brauchen **eine** neue Straße (J-K), damit keine Brücke bleibt (das Brückenbaum-Blatt-Paar)."""
    xy = np.array([[0, 0], [2, 0], [0, 2], [2, 2], [4, 2], [4, 4], [6, 4], [6, 2], [7, 5], [8, 6], [-1.2, -1]], dtype=float)
    pairs = [(0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (4, 7), (6, 8), (8, 9), (0, 10)]
    edges = tuple((min(u, v), max(u, v), float(np.hypot(*(xy[u] - xy[v])))) for u, v in pairs)
    return Instance(xy, tuple(sorted(edges)), 3, "textbook", "grid", 0.0, 0, (), TEXTBOOK_LABELS)
