"""Plotly-Figuren: Karten (Low-Link-Wiedergabe, kritische Straßen und Kreuzungen, getrennte Teile, Blätter), Ranglisten und Kurven. Alle Achsen fest (fixedrange); Karten mit gleichem Maßstab nutzen
`scaleanchor` mit autorange und zwei unsichtbaren Eckpunkten."""

import plotly.graph_objects as go

import brg_algorithm as A

TEAL, ORANGE, BLUE, RED, PURPLE, GREY = "#2F6B65", "#f58518", "#4c78a8", "#e45756", "#7b3fbf", "#b7bec7"
PALETTE = (ORANGE, BLUE, PURPLE, "#54a24b", "#b279a2", "#9d755d", "#eeca3b", "#72b7b2", "#ff9da6")


def _lines(xy, pairs):
    xs, ys = [], []
    for u, v in pairs:
        xs += [xy[u][0], xy[v][0], None]
        ys += [xy[u][1], xy[v][1], None]
    return xs, ys


def _base_layout(fig, height=430, title=None):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=36 if title else 10, b=10), showlegend=False, title=dict(text=title, x=0.01, font=dict(size=14)) if title else None,
                      plot_bgcolor="white")
    fig.update_xaxes(visible=False, fixedrange=True, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False, fixedrange=True)
    return fig


def _corners(fig, xy):
    pad = 0.4
    fig.add_trace(go.Scatter(x=[xy[:, 0].min() - pad, xy[:, 0].max() + pad], y=[xy[:, 1].min() - pad, xy[:, 1].max() + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip"))


def _pairs(inst):
    return [(u, v) for u, v, _ in inst.edges]


def _name(inst, v):
    return inst.labels[v] if inst.labels else str(v)


def _edge_name(inst, e):
    return f"{_name(inst, e[0])}–{_name(inst, e[1])}"


def _node_trace(inst, nodes, color, size, symbol="circle", line_color="white", line_width=1, hover=None):
    xy = inst.xy
    text = [_name(inst, v) for v in nodes] if inst.labels else None
    return go.Scatter(x=xy[nodes, 0], y=xy[nodes, 1], mode="markers+text" if inst.labels else "markers", text=text, textposition="top center",
                      marker=dict(size=size, color=color, symbol=symbol, line=dict(color=line_color, width=line_width)), hovertext=hover, hoverinfo="text" if hover else "skip")


# --- Low-Link in Aktion --------------------------------------------------------------------------------------------------------------------------


def replay(ll, k):
    """Zustand nach den ersten k Ereignissen der Low-Link-Suche: entdeckte Knoten, Baumkanten, Rückwärtskanten, gefundene Brücken und Artikulationspunkte."""
    found, tree, back, bridges, artic = [], [], [], [], set()
    cur = None
    for ev in ll.events[:k]:
        if ev[0] == "root":
            found.append(ev[1])
            cur = ev[1]
        elif ev[0] == "discover":
            found.append(ev[1])
            tree.append((ev[2], ev[1]))
            cur = ev[1]
        elif ev[0] == "back":
            back.append((ev[1], ev[2]))
            cur = ev[1]
        else:
            _, u, p, low_u, bridge_flag, artic_flag = ev
            cur = u
            if bridge_flag:
                bridges.append((min(p, u), max(p, u)))
            if artic_flag:
                artic.add(p)
    return found, tree, back, bridges, artic, cur


def build_lowlink_map(inst, ll, k):
    """Die Suche nach k Ereignissen: Wurzel und entdeckte Knoten (Farbe = Entdeckungszeit), Baumkanten grün, Rückwärtskanten rot gestrichelt, gefundene Brücken dick rot, Artikulationspunkte blau umrandet."""
    xy = inst.xy
    found, tree, back, bridges, artic, cur = replay(ll, k)
    seen = list(found)
    fig = go.Figure()
    ex, ey = _lines(xy, _pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.2), hoverinfo="skip"))
    if tree:
        tx, ty = _lines(xy, tree)
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines", line=dict(color=TEAL, width=3.2), hoverinfo="skip"))
    if back:
        bx, by = _lines(xy, back)
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=RED, width=1.8, dash="dash"), hoverinfo="skip"))
    if bridges:
        gx, gy = _lines(xy, bridges)
        fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", line=dict(color=RED, width=6), hoverinfo="skip"))
    rest = [v for v in range(inst.n) if v not in set(seen)]
    if rest:
        fig.add_trace(go.Scatter(x=xy[rest, 0], y=xy[rest, 1], mode="markers", marker=dict(size=9 if inst.labels else 5, color="#cfd4da"), hoverinfo="skip"))
    fig.add_trace(_node_trace(inst, seen, list(range(1, len(seen) + 1)), 15 if inst.labels else 8, hover=[f"Knoten {_name(inst, v)}: disc = {ll.disc[v]}, low = {ll.low[v]}" for v in seen]))
    fig.data[-1].marker.update(colorscale="Viridis", cmin=1, cmax=max(2, inst.n))
    if artic:
        a = sorted(artic)
        fig.add_trace(go.Scatter(x=xy[a, 0], y=xy[a, 1], mode="markers", marker=dict(size=21 if inst.labels else 13, color="rgba(0,0,0,0)", line=dict(color=BLUE, width=3)), hoverinfo="skip"))
    if cur is not None:
        fig.add_trace(go.Scatter(x=[xy[cur, 0]], y=[xy[cur, 1]], mode="markers", marker=dict(size=25 if inst.labels else 17, color="rgba(0,0,0,0)", line=dict(color=ORANGE, width=3)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 430)


def lowlink_table(inst, ll, k):
    """Zeilen (Knoten, disc, low, Status, Befund) der bis k Ereignisse entdeckten Knoten: der Befund steht erst, wenn der Knoten abgeschlossen ist."""
    found = replay(ll, k)[0]
    flags = {ev[1]: (ev[4], ev[5]) for ev in ll.events[:k] if ev[0] == "finish"}
    rows = []
    for v in found:
        note = ""
        if v in flags:
            bridge_flag, artic_flag = flags[v]
            parts = []
            if bridge_flag:
                parts.append("Straße zum Elternknoten ist eine Brücke")
            if artic_flag:
                parts.append("der Elternknoten trennt diesen Teilbaum ab")
            note = "; ".join(parts)
        rows.append({"Knoten": _name(inst, v), "disc": ll.disc[v], "low (Endwert)": ll.low[v], "Status": "abgeschlossen" if v in flags else "offen", "Befund": note})
    return rows


# --- Kritische Straßen und Kreuzungen ------------------------------------------------------------------------------------------------------------


def build_critical_map(inst, ll, highlight=None):
    """Brücken rot und dick, Straßen in Blöcken (zwei oder mehr Straßen) nach Block gefärbt (der größte Block in Teal), Artikulationspunkte als blaue Rauten; `highlight` = Element, das schwarz umrandet wird."""
    xy = inst.xy
    fig = go.Figure()
    multi = sorted((b for b in ll.blocks if len(b) >= 2), key=lambda b: (-len(b), sorted(b)[0]))
    for i, blk in enumerate(multi):
        col = TEAL if i == 0 else PALETTE[(i - 1) % len(PALETTE)]
        bx, by = _lines(xy, sorted(blk))
        fig.add_trace(go.Scatter(x=bx, y=by, mode="lines", line=dict(color=col, width=2.4), hoverinfo="skip"))
    if ll.bridges:
        gx, gy = _lines(xy, ll.bridges)
        fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", line=dict(color=RED, width=5), hoverinfo="skip"))
    others = [v for v in range(inst.n) if v not in ll.articulation]
    fig.add_trace(_node_trace(inst, others, "#9aa3ad", 9 if inst.labels else 4))
    a = sorted(ll.articulation)
    if a:
        fig.add_trace(_node_trace(inst, a, BLUE, 15 if inst.labels else 8, symbol="diamond", hover=[f"Artikulationspunkt {_name(inst, v)}" for v in a]))
    if highlight is not None:
        kind, el = highlight
        if kind == "bridge":
            hx, hy = _lines(xy, [el])
            fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color="black", width=8), opacity=0.35, hoverinfo="skip"))
        else:
            fig.add_trace(go.Scatter(x=[xy[el, 0]], y=[xy[el, 1]], mode="markers", marker=dict(size=24 if inst.labels else 16, color="rgba(0,0,0,0)", line=dict(color="black", width=3)), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 430)


def build_block_tree(inst, ll, max_blocks=80):
    """Blockbaum auf der Karte: Blöcke als Quadrate am Schwerpunkt ihrer Knoten (Größe = Straßenzahl), Artikulationspunkte als Rauten, Linien verbinden jeden Artikulationspunkt mit seinen Blöcken."""
    if len(ll.blocks) > max_blocks:
        return None
    xy = inst.xy
    fig = go.Figure()
    cent = {}
    for i, blk in enumerate(ll.blocks):
        nodes = A.block_nodes(blk)
        cent[i] = (float(sum(xy[v][0] for v in nodes) / len(nodes)), float(sum(xy[v][1] for v in nodes) / len(nodes)))
    xs, ys = [], []
    for (_, i), (_, v) in A.block_cut_tree(ll):
        xs += [cent[i][0], xy[v][0], None]
        ys += [cent[i][1], xy[v][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=GREY, width=1.6), hoverinfo="skip"))
    sizes = [10 + 3 * min(len(b), 12) for b in ll.blocks]
    cols = [RED if len(b) == 1 else TEAL for b in ll.blocks]
    fig.add_trace(go.Scatter(x=[cent[i][0] for i in range(len(ll.blocks))], y=[cent[i][1] for i in range(len(ll.blocks))], mode="markers", marker=dict(size=sizes, color=cols, symbol="square", line=dict(color="white", width=1)),
                             hovertext=[f"Block {i + 1}: {len(b)} Straße{'n' if len(b) != 1 else ''}" for i, b in enumerate(ll.blocks)], hoverinfo="text"))
    a = sorted(ll.articulation)
    if a:
        fig.add_trace(_node_trace(inst, a, BLUE, 12, symbol="diamond", hover=[f"Artikulationspunkt {_name(inst, v)}" for v in a]))
    _corners(fig, xy)
    return _base_layout(fig, 360)


# --- Ausfallschaden ------------------------------------------------------------------------------------------------------------------------------


def element_label(inst, key):
    kind, el = key
    return f"Brücke {_edge_name(inst, el)}" if kind == "bridge" else f"Kreuzung {_name(inst, el)}"


def build_damage_ranking(inst, ranking, top=15):
    """Die schlimmsten kritischen Elemente nach verlorenen Knotenpaaren (Balken)."""
    shown = ranking[:top]
    labels = [element_label(inst, k) for k, _ in shown][::-1]
    vals = [v for _, v in shown][::-1]
    cols = [RED if k[0] == "bridge" else BLUE for k, _ in shown][::-1]
    fig = go.Figure(go.Bar(x=vals, y=labels, orientation="h", marker_color=cols, text=[f"{v:,}".replace(",", ".") for v in vals], textposition="outside"))
    fig.update_layout(height=max(220, 26 * len(shown) + 60), margin=dict(l=10, r=40, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="verlorene Knotenpaare", fixedrange=True, range=[0, (max(vals) if vals else 1) * 1.22])
    fig.update_yaxes(fixedrange=True)
    return fig


def build_pareto(ranking):
    """Kumulierter Anteil des Gesamtschadens über den Anteil der kritischen Elemente (schlimmste zuerst); Diagonale = gleichmäßig verteilter Schaden."""
    vals = [v for _, v in ranking]
    total = sum(vals) or 1
    xs = [0.0] + [(i + 1) / len(vals) for i in range(len(vals))]
    ys = [0.0]
    acc = 0
    for v in vals:
        acc += v
        ys.append(acc / total)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", line=dict(color=GREY, width=1.5, dash="dash")))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=RED, width=2.6)))
    fig.add_vline(x=0.1, line=dict(color=ORANGE, width=1.4, dash="dot"))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="Anteil der kritischen Elemente", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(title="Anteil am Gesamtschaden", tickformat=".0%", range=[0, 1.02], fixedrange=True)
    return fig


def build_split_map(inst, adj, ll, key):
    """Das Netz nach dem Ausfall des Elements: die entstehenden Teile in eigenen Farben (die größte in Teal), das Element selbst schwarz."""
    kind, el = key
    n = len(adj)
    label = [-1] * n
    skip_node = el if kind == "cut" else None
    skip_edge = el if kind == "bridge" else None
    parts = 0
    from collections import deque
    for s in range(n):
        if label[s] >= 0 or s == skip_node:
            continue
        label[s] = parts
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v == skip_node or (skip_edge is not None and (min(u, v), max(u, v)) == skip_edge):
                    continue
                if label[v] < 0:
                    label[v] = parts
                    q.append(v)
        parts += 1
    sizes = [label.count(i) for i in range(parts)]
    order = sorted(range(parts), key=lambda i: (-sizes[i], i))
    color_of = {}
    j = 0
    for rank, i in enumerate(order):
        if rank == 0:
            color_of[i] = TEAL
        elif sizes[i] == 1:
            color_of[i] = "#9aa3ad"
        else:
            color_of[i] = PALETTE[j % len(PALETTE)]
            j += 1
    xy = inst.xy
    fig = go.Figure()
    kept = [(u, v) for u, v in _pairs(inst) if u != skip_node and v != skip_node and (min(u, v), max(u, v)) != skip_edge]
    ex, ey = _lines(xy, kept)
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color=GREY, width=1.4), hoverinfo="skip"))
    nodes = [v for v in range(n) if v != skip_node]
    fig.add_trace(_node_trace(inst, nodes, [color_of[label[v]] for v in nodes], 13 if inst.labels else 6))
    if kind == "bridge":
        hx, hy = _lines(xy, [el])
        fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color="black", width=3, dash="dot"), hoverinfo="skip"))
    else:
        fig.add_trace(go.Scatter(x=[xy[el, 0]], y=[xy[el, 1]], mode="markers", marker=dict(size=20 if inst.labels else 12, color="black", symbol="x"), hoverinfo="skip"))
    _corners(fig, xy)
    return _base_layout(fig, 400), sizes


# --- Aufwand, Verstärkung, Sweeps ---------------------------------------------------------------------------------------------------------------


def build_cost(rows):
    """Schritte des naiven Ausfalltests gegen Low-Link über die Knotenzahl (log-y)."""
    ns = [r["n"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[r["naive"] for r in rows], mode="lines+markers", line=dict(color=RED, width=2.6), name="naiver Ausfalltest (Straßen und Kreuzungen)"))
    fig.add_trace(go.Scatter(x=ns, y=[r["low"] for r in rows], mode="lines+markers", line=dict(color=TEAL, width=2.6), name="Low-Link (eine Tiefensuche)"))
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(title="Knotenzahl n", fixedrange=True)
    fig.update_yaxes(title="Elementarschritte", type="log", fixedrange=True)
    return fig


def build_leaves_map(inst, ll, adj, leaf_nodes):
    """Brücken rot, die Blattkomponenten des Brückenbaums (zwei-kantenzusammenhängende Teile mit genau einer Brücke) orange: je zwei davon lassen sich durch eine neue Straße verbinden."""
    xy = inst.xy
    label, c = A.two_edge_components(adj, ll.bridges)
    leaf_labels = {label[v] for v in leaf_nodes}
    fig = go.Figure()
    ex, ey = _lines(xy, _pairs(inst))
    fig.add_trace(go.Scatter(x=ex, y=ey, mode="lines", line=dict(color="#dfe3e8", width=1.4), hoverinfo="skip"))
    if ll.bridges:
        gx, gy = _lines(xy, ll.bridges)
        fig.add_trace(go.Scatter(x=gx, y=gy, mode="lines", line=dict(color=RED, width=4.5), hoverinfo="skip"))
    leaf_v = [v for v in range(inst.n) if label[v] in leaf_labels]
    other = [v for v in range(inst.n) if label[v] not in leaf_labels]
    fig.add_trace(_node_trace(inst, other, "#9aa3ad", 9 if inst.labels else 4))
    if leaf_v:
        fig.add_trace(_node_trace(inst, leaf_v, ORANGE, 15 if inst.labels else 8, hover=[f"Blattkomponente, Knoten {_name(inst, v)}" for v in leaf_v]))
    _corners(fig, xy)
    return _base_layout(fig, 400)


def build_crit_sweep(rows, nettype):
    """Anteil der Brücken (an den Straßen) und der Artikulationspunkte (an den Knoten) der größten Komponente über den gesperrten Anteil; gepunktet: Größe der größten Komponente."""
    xs = [r["blocked"] for r in rows]
    fig = go.Figure()
    for key, name, col in (("bridge", "Brücken (Anteil der Straßen)", RED), ("artic", "Artikulationspunkte (Anteil der Knoten)", BLUE), ("giant", "größte Komponente (Anteil der Knoten)", GREY)):
        med = [r[(nettype, key)][0] for r in rows]
        lo = [r[(nettype, key)][1] for r in rows]
        hi = [r[(nettype, key)][2] for r in rows]
        if key != "giant":
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], fill="toself", fillcolor=col, opacity=0.15, line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=xs, y=med, mode="lines+markers", line=dict(color=col, width=2.4, dash="dot" if key == "giant" else "solid"), marker=dict(size=5), name=name))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=1.14), plot_bgcolor="white")
    fig.update_xaxes(title="gesperrter Anteil der Straßen", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(tickformat=".0%", range=[0, 1.03], fixedrange=True)
    return fig


def build_density(rows):
    fig = go.Figure(go.Scatter(x=[r["factor"] for r in rows], y=[r["bridge_share"] for r in rows], mode="lines+markers", line=dict(color=RED, width=2.6), marker=dict(size=7)))
    fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), plot_bgcolor="white", showlegend=False)
    fig.update_xaxes(title="Straßen je Knoten (m / n)", fixedrange=True)
    fig.update_yaxes(title="Anteil der Brücken", tickformat=".0%", range=[0, 1.05], fixedrange=True)
    return fig


def build_augmentation(rows):
    xs = [r["blocked"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=xs, y=[r["bridges"] for r in rows], name="Brücken", marker_color=RED, width=0.03))
    fig.add_trace(go.Bar(x=xs, y=[r["need"] for r in rows], name="fehlende Straßen (ceil(Blätter / 2))", marker_color=ORANGE, width=0.03))
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10), plot_bgcolor="white", barmode="group", legend=dict(orientation="h", y=1.14))
    fig.update_xaxes(title="gesperrter Anteil der Straßen", tickformat=".0%", fixedrange=True)
    fig.update_yaxes(title="Zahl (größte Komponente)", fixedrange=True, rangemode="tozero")
    return fig
