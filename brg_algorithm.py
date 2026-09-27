"""Brücken, Artikulationspunkte und Blöcke - naiv (jede Straße bzw. Kreuzung entfernen und neu zählen) und mit Tarjans Low-Link (eine Tiefensuche); Ausfallschaden und Verstärkungsbedarf.

**Elementarschritte** (das Aufwandsmaß dieser Reihe, keine Laufzeit): jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante zählt 1 (wie in der BFS-und-DFS-Demo). Low-Link ist eine
Tiefensuche: n_besucht + 2 m_besucht. Der naive Test führt je Straße (bzw. Kreuzung) eine vollständige Komponentenzählung durch.

Begriffe: Eine **Brücke** ist eine Straße, deren Ausfall das Netz teilt (die Komponentenzahl wächst). Ein **Artikulationspunkt** ist eine Kreuzung mit derselben Eigenschaft (ohne sie zerfällt ihre Komponente).
Ein **Block** ist eine maximale Menge von Straßen, in der je zwei auf einem gemeinsamen Kreis liegen (zweifach zusammenhängende Komponente); eine Brücke ist ein Block aus genau einer Straße."""

import itertools
import random
from collections import deque
from dataclasses import dataclass, field


def adjacency(n, edges, order="fixed", seed=0):
    """Adjazenzliste aus Kanten (u, v, ...); "fixed" = aufsteigende Nachbarn, "shuffled" = je Knoten gemischt (Seed fest, Python-`random`)."""
    adj = [[] for _ in range(n)]
    for e in edges:
        u, v = int(e[0]), int(e[1])
        adj[u].append(v)
        adj[v].append(u)
    for lst in adj:
        lst.sort()
    if order == "shuffled":
        rng = random.Random(int(seed) * 1_000_003 + 5150)
        for lst in adj:
            rng.shuffle(lst)
    elif order != "fixed":
        raise ValueError(f"unbekannte Reihenfolge {order}")
    return adj


def _key(u, v):
    return (u, v) if u < v else (v, u)


# --- Low-Link ------------------------------------------------------------------------------------------------------------------------------------


@dataclass
class LowLink:
    disc: list                                            # Entdeckungszeit je Knoten (1, 2, ...)
    low: list                                             # kleinste Entdeckungszeit, die vom Teilbaum des Knotens über höchstens eine Rückwärtskante erreichbar ist
    parent: list
    root: list                                            # Wurzel der Tiefensuche-Komponente je Knoten
    size: list                                            # Größe des Teilbaums je Knoten
    bridges: list = field(default_factory=list)           # (u, v) mit u < v, in Fundreihenfolge
    articulation: set = field(default_factory=set)
    blocks: list = field(default_factory=list)            # frozenset von Straßen (u, v) je Block, in Fundreihenfolge
    steps: int = 0
    events: list = field(default_factory=list)            # ("root", s) | ("discover", v, u) | ("back", u, v) | ("finish", u, parent, low, bridge_flag, artic_flag); artic_flag gehört zum Elternknoten
    comp_size: dict = field(default_factory=dict)         # Wurzel -> Größe der Komponente


def low_link(adj):
    """Tarjans Low-Link, iterativ: Baumkante (p, u) ist Brücke, wenn low[u] > disc[p]; p ist Artikulationspunkt, wenn ein Kind u low[u] >= disc[p] hat (Wurzel: mindestens zwei Kinder).
    Die Blöcke werden mit einem Kantenstapel abgetrennt (Hopcroft und Tarjan 1973)."""
    n = len(adj)
    disc, low, parent, root, size = [0] * n, [0] * n, [-1] * n, [-1] * n, [1] * n
    r = LowLink(disc, low, parent, root, size)
    clock = 0
    children = [0] * n
    pos = [0] * n
    edge_stack = []
    for s in range(n):
        if disc[s]:
            continue
        clock += 1
        disc[s] = low[s] = clock
        root[s] = s
        r.steps += 1
        r.events.append(("root", s))
        stack = [s]
        while stack:
            u = stack[-1]
            if pos[u] < len(adj[u]):
                v = adj[u][pos[u]]
                pos[u] += 1
                r.steps += 1                              # Kante von u aus angesehen
                if not disc[v]:
                    parent[v] = u
                    root[v] = s
                    children[u] += 1
                    edge_stack.append(_key(u, v))
                    clock += 1
                    disc[v] = low[v] = clock
                    r.steps += 1                          # Knoten v abgearbeitet
                    stack.append(v)
                    r.events.append(("discover", v, u))
                elif v != parent[u] and disc[v] < disc[u]:
                    edge_stack.append(_key(u, v))         # Rückwärtskante zu einem Vorfahren (einmal, vom Nachkommen aus)
                    if disc[v] < low[u]:
                        low[u] = disc[v]
                    r.events.append(("back", u, v))
            else:
                stack.pop()
                p = parent[u]
                bridge_flag = artic_flag = False
                if p != -1:
                    size[p] += size[u]
                    if low[u] < low[p]:
                        low[p] = low[u]
                    if low[u] > disc[p]:
                        r.bridges.append(_key(p, u))
                        bridge_flag = True
                    if low[u] >= disc[p]:                # p trennt den Teilbaum von u ab: ein Block ist fertig
                        block = []
                        while True:
                            e = edge_stack.pop()
                            block.append(e)
                            if e == _key(p, u):
                                break
                        r.blocks.append(frozenset(block))
                        if parent[p] != -1:
                            r.articulation.add(p)
                            artic_flag = True
                r.events.append(("finish", u, p, low[u], bridge_flag, artic_flag))
        if children[s] >= 2:
            r.articulation.add(s)
        r.comp_size[s] = size[s]
    return r


def _component_count(adj, skip_edge=None, skip_node=None):
    """Zahl der Komponenten des Graphen ohne die Straße `skip_edge` bzw. die Kreuzung `skip_node` (die dann nicht mitgezählt wird) und die dafür nötigen Schritte (Breitensuche je Komponente)."""
    n = len(adj)
    seen = [False] * n
    if skip_node is not None:
        seen[skip_node] = True
    count = steps = 0
    for s in range(n):
        if seen[s]:
            continue
        count += 1
        seen[s] = True
        queue = deque([s])
        while queue:
            u = queue.popleft()
            steps += 1
            for v in adj[u]:
                steps += 1
                if skip_edge is not None and _key(u, v) == skip_edge:
                    continue
                if not seen[v]:
                    seen[v] = True
                    queue.append(v)
    return count, steps


def bridges_naive(adj):
    """Ausfalltest je Straße: Straße entfernen, Komponenten neu zählen; wächst die Zahl, ist sie eine Brücke. Gibt (Brücken, Schritte) zurück."""
    n = len(adj)
    base, steps = _component_count(adj)
    out = []
    for u in range(n):
        for v in adj[u]:
            if u < v:
                c, st = _component_count(adj, skip_edge=(u, v))
                steps += st
                if c > base:
                    out.append((u, v))
    return sorted(out), steps


def articulation_naive(adj):
    """Ausfalltest je Kreuzung: Kreuzung x entfernen, die übrigen Knoten neu in Komponenten zählen. x trennt seine Komponente, wenn danach mehr Komponenten übrig sind, als der Graph vorher ohne den
    Beitrag von x hatte (eine einzelne Kreuzung ohne Straße bildet eine eigene Komponente, die beim Entfernen wegfällt). Gibt (Artikulationspunkte, Schritte) zurück."""
    n = len(adj)
    base, steps = _component_count(adj)
    out = set()
    for x in range(n):
        c, st = _component_count(adj, skip_node=x)
        steps += st
        expected = base - (1 if not adj[x] else 0)          # ohne x: eine Komponente weniger, wenn x allein war; sonst gleich viele, solange x nichts trennt
        if c > expected:
            out.add(x)
    return out, steps


# --- Blockbaum, Brückenbaum, Verstärkung -----------------------------------------------------------------------------------------------------------


def block_nodes(block):
    return sorted({x for e in block for x in e})


def block_cut_tree(ll):
    """Blockbaum: Knoten sind die Blöcke ("B", i) und die Artikulationspunkte ("A", v); ein Artikulationspunkt hängt an jedem Block, der ihn enthält. Gibt die Kantenliste zurück."""
    out = []
    for i, blk in enumerate(ll.blocks):
        for v in block_nodes(blk):
            if v in ll.articulation:
                out.append((("B", i), ("A", v)))
    return out


def two_edge_components(adj, bridges):
    """Komponenten ohne die Brücken (zweifach kantenzusammenhängende Komponenten). Gibt (Etikett je Knoten, Zahl) zurück."""
    bset = set(bridges)
    n = len(adj)
    label = [-1] * n
    c = 0
    for s in range(n):
        if label[s] >= 0:
            continue
        label[s] = c
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if label[v] < 0 and _key(u, v) not in bset:
                    label[v] = c
                    queue.append(v)
        c += 1
    return label, c


def augmentation_need(adj, ll=None):
    """Wie viele Straßen fehlen mindestens, damit jede Komponente brückenfrei wird? Je Komponente mit Brücken: ceil(L / 2), L = Blätter des Brückenbaums (Eswaran und Tarjan 1976). Gibt
    (Summe, Liste (Wurzel der Komponente, Blätter, Bedarf), Vertreter der Blattknoten) zurück; nur gezählt, nicht konstruiert."""
    ll = ll or low_link(adj)
    label, c = two_edge_components(adj, ll.bridges)
    deg = [0] * c
    for u, v in ll.bridges:
        deg[label[u]] += 1
        deg[label[v]] += 1
    first = {}
    for v in range(len(adj)):
        first.setdefault(label[v], v)
    leaves_by_root = {}
    leaf_nodes = []
    for comp in range(c):
        if deg[comp] == 1:
            rep = first[comp]
            leaf_nodes.append(rep)
            leaves_by_root.setdefault(ll.root[rep], []).append(rep)
    detail = []
    total = 0
    for root_v, leaves in sorted(leaves_by_root.items()):
        need = (len(leaves) + 1) // 2
        detail.append((root_v, len(leaves), need))
        total += need
    return total, detail, leaf_nodes


# --- Ausfallschaden ------------------------------------------------------------------------------------------------------------------------------


def _pairs(k):
    return k * (k - 1) // 2


def damage_bridge(ll, bridge):
    """Knotenpaare, die durch den Ausfall der Brücke die Verbindung verlieren: a * (S - a) mit Komponentengröße S und Teilbaumgröße a."""
    u, v = bridge
    child = v if ll.parent[v] == u else u
    S = ll.comp_size[ll.root[child]]
    a = ll.size[child]
    return a * (S - a)


def damage_articulation(ll, adj, x):
    """Knotenpaare (ohne x), die durch den Ausfall der Kreuzung x die Verbindung verlieren: Paare der Restkomponente minus Paare innerhalb der entstehenden Teile."""
    S = ll.comp_size[ll.root[x]]
    cut_sizes = [ll.size[c] for c in adj[x] if ll.parent[c] == x and ll.low[c] >= ll.disc[x]]
    rest = S - 1 - sum(cut_sizes)
    parts = cut_sizes + ([rest] if rest > 0 else [])
    return _pairs(S - 1) - sum(_pairs(p) for p in parts)


def damages(adj, ll=None):
    """Schaden je kritischem Element: ({("bridge", (u, v)): Paare, ("cut", v): Paare}, absteigend sortierte Rangliste)."""
    ll = ll or low_link(adj)
    d = {}
    for b in ll.bridges:
        d[("bridge", b)] = damage_bridge(ll, b)
    for x in ll.articulation:
        d[("cut", x)] = damage_articulation(ll, adj, x)
    ranking = sorted(d.items(), key=lambda kv: (-kv[1], kv[0][0], str(kv[0][1])))
    return d, ranking


def damage_bruteforce(adj, kind, element):
    """Referenz für die Tests: Element wirklich entfernen und die verbundenen Knotenpaare vorher und nachher zählen (bei einer Kreuzung ohne sie selbst)."""
    n = len(adj)

    def connected_pairs(skip_edge=None, skip_node=None, drop_node_from_count=None):
        seen = [False] * n
        if skip_node is not None:
            seen[skip_node] = True
        total = 0
        for s in range(n):
            if seen[s]:
                continue
            seen[s] = True
            queue = deque([s])
            size = 0
            has_dropped = False
            while queue:
                u = queue.popleft()
                size += 1
                if u == drop_node_from_count:
                    has_dropped = True
                for v in adj[u]:
                    if skip_edge is not None and _key(u, v) == skip_edge:
                        continue
                    if not seen[v]:
                        seen[v] = True
                        queue.append(v)
            total += _pairs(size - (1 if has_dropped else 0))
        return total

    if kind == "bridge":
        return connected_pairs() - connected_pairs(skip_edge=element)
    return connected_pairs(drop_node_from_count=element) - connected_pairs(skip_node=element)


def brute_force_augmentation(n, edges, limit=4):
    """Kleinste Zahl hinzuzufügender Straßen, damit der (zusammenhängende) Graph brückenfrei wird: Aufzählung aller Kantenmengen der Größe 0, 1, ... (nur für Tests, n <= 8)."""
    have = {_key(u, v) for u, v, *_ in edges}
    missing = [(a, b) for a in range(n) for b in range(a + 1, n) if (a, b) not in have]
    for k in range(limit + 1):
        for extra in itertools.combinations(missing, k):
            adj = adjacency(n, sorted(have) + list(extra))
            ll = low_link(adj)
            if not ll.bridges and len(ll.comp_size) == 1:
                return k
    return None
