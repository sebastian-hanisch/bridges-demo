"""Brücken und Artikulationspunkte – welche einzelne Straße darf nicht ausfallen? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Zweites Stück der Graphen-und-Netzwerke-Reihe der "Konzepte"-Reihe. Kind der Durchmusterung (BFS und DFS): dieselbe Tiefensuche, ergänzt um eine Zahl je Knoten (low), verrät Brücken und Artikulationspunkte
in einem Durchgang. Gemessen wird, was das gegenüber dem naiven Ausfalltest spart, wie viele Straßen und Kreuzungen kritisch sind, wie ungleich der Ausfallschaden verteilt ist und wie viele Straßen fehlen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import brg_constants as C
import brg_evaluation as ev
from brg_evaluation import Settings, analyse
from brg_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from brg_visualization import (
    build_augmentation,
    build_block_tree,
    build_cost,
    build_crit_sweep,
    build_critical_map,
    build_damage_ranking,
    build_density,
    build_leaves_map,
    build_lowlink_map,
    build_pareto,
    build_split_map,
    element_label,
    lowlink_table,
)

st.set_page_config(page_title="Brücken und Artikulationspunkte – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings, naive):
    return analyse(settings, naive=naive)


@st.cache_data(show_spinner=False)
def _cost(settings):
    return ev.cost_sweep(settings, C.COST_SIDES)


@st.cache_data(show_spinner=False)
def _critical():
    return ev.critical_sweep(C.CRIT_SIDE)


@st.cache_data(show_spinner=False)
def _density():
    return ev.density_sweep(C.DENSITY_N, C.DENSITY_FACTORS)


@st.cache_data(show_spinner=False)
def _augmentation(nettype):
    return ev.augmentation_sweep(C.CRIT_SIDE, (0.1, 0.2, 0.3, 0.4, 0.5), nettype)


def _german(x):
    return f"{x:,}".replace(",", ".")


st.title("🌉 Brücken und Artikulationspunkte – welche einzelne Straße darf nicht ausfallen?")
st.markdown(
    """
**Zweites Stück der Graphen-und-Netzwerke-Reihe.** Fällt eine einzelne Straße aus, ist oft nichts weiter: es gibt einen Umweg. Manchmal aber zerfällt dadurch das Netz - die Straße ist eine **Brücke**. Fällt eine einzelne Kreuzung aus
und ihre Komponente zerfällt, ist sie ein **Artikulationspunkt**. Beide zu finden, ist die Frage nach den **kritischen** Elementen eines Netzes.

Der naive Weg: jede Straße und jede Kreuzung entfernen und nachzählen, ob das Netz zerfällt - das kostet je Element eine ganze Suche. **Tarjans Low-Link** braucht nur **eine** Tiefensuche aus der ersten Demo
und eine Zahl je Knoten. Gemessen wird, was das spart, wie viele Elemente kritisch sind, wie ungleich der Schaden eines Ausfalls verteilt ist und wie viele Straßen man mindestens bauen muss, damit keine Brücke mehr bleibt.
"""
)
st.caption(
    "Kind der BFS-und-DFS-Demo (zweites Stück der Graphen-und-Netzwerke-Reihe); Folgestücke: Euler-Touren (brauchen Brücken), Zentralität, Robustheit, Kaskaden, kritische Knoten härten, Bandbreite. "
    "Die MST-Sensitivität (Spannbaum-Reihe) misst Brücken nur am Spannbaum; hier sind es die des Netzes selbst."
)

with st.expander("So funktioniert Low-Link", expanded=True):
    st.markdown(
        """
1. **Tiefensuche mit Uhr:** jeder Knoten bekommt beim Entdecken eine Zeit **disc** (1, 2, 3, ...). Straßen zu bereits entdeckten Knoten sind Rückwärtskanten zu einem Vorfahren.
2. **low:** für jeden Knoten die kleinste Entdeckungszeit, die man von seinem Teilbaum aus über *höchstens eine* Rückwärtskante erreicht. Ein Knoten ohne Umweg nach oben hat low = disc.
3. **Brücke:** eine Baumkante (p, u) ist genau dann eine Brücke, wenn **low[u] > disc[p]**: der Teilbaum unter u kommt auch über Rückwärtskanten nicht an p vorbei.
4. **Artikulationspunkt:** ein Knoten p (nicht die Wurzel) ist es, wenn ein Kind u **low[u] ≥ disc[p]** hat - der Teilbaum unter u hängt nur an p. Die Wurzel ist es, wenn sie mindestens zwei Kinder hat.
5. **Blöcke:** die Straßen zwischen zwei Artikulationspunkten, in denen je zwei auf einem gemeinsamen Kreis liegen (zweifach zusammenhängend). Eine Brücke ist ein Block aus einer einzigen Straße.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:5], preset_names[5:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Die Brückenstadt hat 11 Kreuzungen (A bis K) mit 4 Brücken und 5 Artikulationspunkten, von Hand nachvollziehbar; das Betriebsnetz ist ein Raster mit gesperrten Straßen oder ein Zufallsgraph.")
    if kind == "city":
        side = st.slider("Kreuzungen je Seite", C.SIDE_MIN, C.SIDE_MAX, value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                         help="Seitenlänge des Rasters; n = Seitenlänge zum Quadrat Knoten (16 bis 900).")
        blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), format_func=lambda v: f"{v * 100:.0f} %", key="blocked_widget",
                                   on_change=store_from_widget, args=("blocked_select",),
                                   help="Zufällig gesperrte Straßen. Je mehr gesperrt, desto weniger Umwege gibt es und desto mehr Straßen und Kreuzungen sind kritisch.")
        nettype = st.radio("Netztyp", options=list(C.NETTYPES), format_func=lambda v: C.NETTYPE_LABELS[v], index=list(C.NETTYPES).index(ss["nettype_select"]), key="nettype_widget",
                           on_change=store_from_widget, args=("nettype_select",),
                           help="Raster: Straßen nur zwischen Nachbarn. Zufallsgraph: dieselbe Knoten- und Kantenzahl, aber die Kanten verbinden beliebige Paare (die Karte zeigt nur die Lage).")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        side, blocked, nettype, seed = C.DEFAULT_SIDE, 0.0, "grid", 0
    order = st.radio("Nachbarreihenfolge", options=list(C.ORDERS), format_func=lambda v: C.ORDER_LABELS[v], key="order_select",
                     help="In welcher Reihenfolge die Tiefensuche die Nachbarn ansieht. Ändert die Wiedergabe (Baum, Zeiten), nie die Ergebnisse: die Mengen der Brücken, Artikulationspunkte und Blöcke bleiben gleich.")

sync_query_params({"kind_select": kind, "side_slider": int(side), "blocked_select": float(blocked), "nettype_select": nettype, "order_select": order, "seed_input": int(seed), "brg_step": int(ss["brg_step"])})

settings = Settings(kind, int(side), float(blocked), nettype, int(seed), order)
with st.spinner("Rechne..."):
    a = _analysis(settings, False)
inst, ll, adj = a.inst, a.ll, a.adj
names = (lambda v: inst.labels[v]) if inst.labels else (lambda v: str(v))
n_events = len(ll.events)
naive_ok = inst.n <= C.NAIVE_MAX_N
if naive_ok:
    a_naive = _analysis(settings, True)

st.markdown("## 🎯 Das Netz und seine kritischen Elemente")
st.markdown(f"**{a.n} Kreuzungen, {_german(a.m)} Straßen** ({'Raster' if inst.nettype == 'grid' and kind == 'city' else ('Zufallsgraph' if kind == 'city' else 'Brückenstadt')}"
            + (f", {len(inst.blocked_edges)} gesperrt" if inst.blocked_edges else "") + f"), {a.c} Komponente{'n' if a.c != 1 else ''}; die größte hat {a.largest} Knoten.")
step = st.select_slider("Schritt", options=list(C.STEPS), key="brg_step", format_func=lambda s: C.STEPS[s])

if step == 1:
    if n_events > 1:
        ss["search_k"] = n_events if "search_k" not in ss else min(max(1, int(ss["search_k"])), n_events)
        k = st.slider("Ereignis der Tiefensuche", 1, n_events, key="search_k", help="Die Tiefensuche ereignisweise: Wurzel, Knoten entdeckt, Rückwärtskante gesehen, Knoten abgeschlossen (dann steht sein low-Wert fest).")
    else:
        k = 1
    st.plotly_chart(build_lowlink_map(inst, ll, k), width="stretch", key=f"s1_map_{k}")
    ev_k = ll.events[k - 1]
    if ev_k[0] == "root":
        st.markdown(f"**Ereignis {k} von {n_events}:** die Suche beginnt bei Knoten {names(ev_k[1])} (disc = {ll.disc[ev_k[1]]}).")
    elif ev_k[0] == "discover":
        st.markdown(f"**Ereignis {k} von {n_events}:** von {names(ev_k[2])} aus wird Knoten {names(ev_k[1])} neu entdeckt (disc = {ll.disc[ev_k[1]]}); die Straße wird Baumkante.")
    elif ev_k[0] == "back":
        st.markdown(f"**Ereignis {k} von {n_events}:** von {names(ev_k[1])} führt eine Straße zum schon entdeckten Vorfahren {names(ev_k[2])} (disc = {ll.disc[ev_k[2]]}): Rückwärtskante, low von {names(ev_k[1])} sinkt höchstens auf diesen Wert.")
    else:
        _, u, p, low_u, bf, af = ev_k
        if p == -1:
            st.markdown(f"**Ereignis {k} von {n_events}:** Knoten {names(u)} ist die Wurzel und ist abgeschlossen (low = {low_u}).")
        else:
            verdict = f"**low[{names(u)}] = {low_u} > disc[{names(p)}] = {ll.disc[p]}: die Straße {names(p)}–{names(u)} ist eine Brücke.**" if bf else f"low[{names(u)}] = {low_u} ≤ disc[{names(p)}] = {ll.disc[p]}: es gibt einen Umweg um {names(p)}–{names(u)}, keine Brücke."
            extra = f" Und low[{names(u)}] ≥ disc[{names(p)}]: {names(p)} trennt den Teilbaum unter {names(u)} ab, Artikulationspunkt." if af else ""
            st.markdown(f"**Ereignis {k} von {n_events}:** Knoten {names(u)} ist abgeschlossen. {verdict}{extra}")
    if inst.n <= 40:
        st.dataframe(lowlink_table(inst, ll, k), hide_index=True, width="stretch")
    st.caption("Farbe = Entdeckungszeit, grün = Baumkanten, rot gestrichelt = Rückwärtskanten, dick rot = gefundene Brücken, blau umrandet = gefundene Artikulationspunkte, oranger Ring = aktuelles Ereignis.")
elif step == 2:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Brücken", len(ll.bridges), delta=f"{a.bridge_share * 100:.1f} % im Kern", delta_color="off")
    c2.metric("Artikulationspunkte", len(ll.articulation), delta=f"{a.artic_share * 100:.1f} % im Kern", delta_color="off")
    c3.metric("Blöcke", len(ll.blocks), delta=f"{a.big_blocks} mit ≥ 3", delta_color="off")
    c4.metric("Größter Block", a.largest_block_edges, delta="Straßen", delta_color="off")
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("**Kritische Elemente**")
        st.plotly_chart(build_critical_map(inst, ll), width="stretch", key="s2_map")
        st.caption("Rot: Brücken. Blaue Rauten: Artikulationspunkte. Die übrigen Straßen liegen in Blöcken (größter Block teal, weitere Blöcke bunt). „Kern“ = größte Komponente.")
    with cc2:
        st.markdown("**Blockbaum**")
        fig_bt = build_block_tree(inst, ll)
        if fig_bt is None:
            st.info(f"Mit {len(ll.blocks)} Blöcken wird der Blockbaum unübersichtlich; er wird nur bis 80 Blöcke gezeichnet.")
        else:
            st.plotly_chart(fig_bt, width="stretch", key="s2_bct")
            st.caption("Quadrate: Blöcke (rot = eine Brücke, teal = zwei oder mehr Straßen, Größe = Straßenzahl); Rauten: Artikulationspunkte. Zwei Blöcke teilen höchstens einen Artikulationspunkt: der Blockbaum ist ein Wald.")
    st.markdown("#### 🔬 Wie viele Straßen und Kreuzungen sind kritisch?")
    if st.button("Anteile über den Sperranteil berechnen (kann einen Moment dauern)", key="crit_start"):
        ss["crit_done"] = True
    if ss.get("crit_done"):
        with st.spinner("Rechne..."):
            rows_c = _critical()
        tabs = st.tabs([C.NETTYPE_LABELS[nt] for nt in C.NETTYPES])
        for tab, nt in zip(tabs, C.NETTYPES):
            with tab:
                st.plotly_chart(build_crit_sweep(rows_c, nt), width="stretch", key=f"s2_crit_{nt}")
        st.caption(f"Median über 5 feste Instanzen mit {C.CRIT_SIDE} × {C.CRIT_SIDE} Knoten; Anteile an der größten Komponente. Beide Anteile steigen mit dem Sperranteil; jenseits der Schwelle ist die größte Komponente nur noch ein kleiner Baum (jede Straße eine Brücke).")
    if st.button("Brückenanteil im Zufallsgraph über die Dichte berechnen", key="dens_start"):
        ss["dens_done"] = True
    if ss.get("dens_done"):
        st.plotly_chart(build_density(_density()), width="stretch", key="s2_density")
        st.caption(f"Zufallsgraph mit {C.DENSITY_N} Knoten und dem angegebenen Verhältnis Straßen zu Knoten (Median über 5 feste Zufallsgraphen). Ab etwa 2 Straßen je Knoten gibt es kaum noch Brücken (bei 3.0: keine).")
elif step == 3:
    if not a.ranking:
        st.info("Dieses Netz hat weder Brücken noch Artikulationspunkte: kein einzelner Ausfall trennt etwas.")
    else:
        d1, d2, d3 = st.columns(3)
        d1.metric("Gesamtschaden", _german(a.total_damage), delta="verlorene Paare", delta_color="off")
        d2.metric("Schlimmstes Element", _german(a.ranking[0][1]), delta=element_label(inst, a.ranking[0][0]), delta_color="off")
        d3.metric("Schlimmste 10 %", f"{a.pareto * 100:.0f} %", delta="des Gesamtschadens", delta_color="off")
        cc1, cc2 = st.columns([3, 2])
        with cc1:
            st.plotly_chart(build_damage_ranking(inst, a.ranking), width="stretch", key="s3_rank")
            st.caption("Die 15 schlimmsten kritischen Elemente nach verlorenen Knotenpaaren (rot: Brücke, blau: Artikulationspunkt). Eine Brücke und ihr Ende sind oft beide kritisch und werden je für sich gezählt.")
        with cc2:
            st.plotly_chart(build_pareto(a.ranking), width="stretch", key="s3_pareto")
            st.caption("Kumulierter Anteil des Gesamtschadens; gestrichelt: gleichmäßig verteilt, gepunktet: die schlimmsten 10 %.")
        top_n = min(len(a.ranking), 40)
        pick = st.selectbox("Ausfall ansehen", options=list(range(top_n)), format_func=lambda i: f"{element_label(inst, a.ranking[i][0])} - {_german(a.ranking[i][1])} Paare", key="dmg_pick")
        key, val = a.ranking[pick]
        fig_split, sizes = build_split_map(inst, adj, ll, key)
        st.plotly_chart(fig_split, width="stretch", key=f"s3_split_{pick}")
        big = sorted(sizes, reverse=True)
        st.caption(f"{element_label(inst, key)} fällt aus: das Netz zerfällt in Teile von {', '.join(str(s) for s in big[:6])}{' ...' if len(big) > 6 else ''} Knoten, {_german(val)} Knotenpaare verlieren die Verbindung (größter Teil teal, einzelne Knoten grau).")
else:
    st.markdown("#### Aufwand: naiver Ausfalltest gegen Low-Link")
    if naive_ok:
        w1, w2, w3 = st.columns(3)
        w1.metric("Naiv", _german(a_naive.naive_steps), delta="Elementarschritte", delta_color="off")
        w2.metric("Low-Link", _german(a.low_steps), delta="Elementarschritte", delta_color="off")
        w3.metric("Verhältnis", f"{a_naive.naive_steps / max(1, a.low_steps):.0f}", delta="naiv / Low-Link", delta_color="off")
    else:
        st.info(f"Der naive Test wird für diese Instanz nicht mitgerechnet (n = {a.n} > {C.NAIVE_MAX_N}); Low-Link braucht {_german(a.low_steps)} Schritte.")
    if kind == "city":
        if st.button("Aufwand über die Größe messen (kann einen Moment dauern)", key="cost_start"):
            ss["cost_done"] = ss.get("cost_done", set()) | {(settings.blocked, settings.nettype, settings.order)}
        if (settings.blocked, settings.nettype, settings.order) in ss.get("cost_done", set()):
            with st.spinner("Rechne..."):
                rows_cost = _cost(Settings("city", C.DEFAULT_SIDE, settings.blocked, settings.nettype, 0, settings.order))
            st.plotly_chart(build_cost(rows_cost), width="stretch", key="s4_cost")
            st.caption(f"Median über 5 feste Instanzen je Größe. Beim größten Netz (n = {rows_cost[-1]['n']}): naiv {_german(int(rows_cost[-1]['naive']))}, Low-Link {_german(int(rows_cost[-1]['low']))}, Faktor {rows_cost[-1]['ratio']:.0f}. "
                       "Der naive Test wächst wie m · (n + m), Low-Link wie n + m: das Verhältnis wächst etwa mit n. Ein Näherungsmaß in Elementarschritten, keine Laufzeit.")
    st.markdown("#### Verstärkung: wie viele Straßen fehlen?")
    need = a.aug_lc
    v1, v2, v3 = st.columns(3)
    v1.metric("Fehlende Straßen (Kern)", need, delta="ceil(Blätter / 2)", delta_color="off")
    v2.metric("Brücken (Kern)", a.lc_bridges, delta="zu beseitigen", delta_color="off")
    v3.metric("Fehlende Straßen (alle)", a.augmentation, delta="Summe je Komponente", delta_color="off")
    if a.lc_bridges:
        st.plotly_chart(build_leaves_map(inst, ll, adj, a.leaf_nodes), width="stretch", key="s4_leaves")
        st.caption("Rot: Brücken. Orange: Blattkomponenten des Brückenbaums (Teile, die nur über eine einzige Brücke am Rest hängen). Je zwei davon lassen sich mit einer neuen Straße zu einem Ring schließen: "
                   "mindestens ceil(Blätter / 2) neue Straßen machen die Komponente brückenfrei (Eswaran und Tarjan 1976; hier nur gezählt, nicht konstruiert).")
    else:
        st.success("Die größte Komponente hat keine Brücke: keine neue Straße nötig.")
    if kind == "city":
        if st.button("Verstärkungsbedarf über den Sperranteil berechnen", key="aug_start"):
            ss["aug_done"] = ss.get("aug_done", set()) | {settings.nettype}
        if settings.nettype in ss.get("aug_done", set()):
            st.plotly_chart(build_augmentation(_augmentation(settings.nettype)), width="stretch", key="s4_aug")
            st.caption(f"Median über 5 feste Instanzen mit {C.CRIT_SIDE} × {C.CRIT_SIDE} Knoten ({C.NETTYPE_LABELS[settings.nettype]}): es fehlen ein Viertel bis die Hälfte so viele Straßen, wie es Brücken gibt.")

st.markdown("---")

st.markdown("## 🎯 Was das Netz verrät")
st.caption("**Brücken und Artikulationspunkte** beziehen sich auf die größte Komponente (der Kern des Netzes). **Schaden:** Knotenpaare, die durch einen Ausfall die Verbindung verlieren.")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Kritische Straßen", len(ll.bridges), delta=f"{a.lc_bridges} im Kern", delta_color="off")
r2.metric("Kritische Kreuzungen", len(ll.articulation), delta=f"{a.lc_artic} im Kern", delta_color="off")
r3.metric("Schlimmster Ausfall", _german(a.ranking[0][1]) if a.ranking else "0", delta="Knotenpaare", delta_color="off")
r4.metric("Fehlende Straßen", a.aug_lc, delta="bis brückenfrei", delta_color="off")

st.markdown("---")

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ein Ausfall betrifft ein einzelnes Element** | Brücken und Artikulationspunkte sind die Antwort für *einen* Ausfall. Fallen zwei Straßen zugleich aus, können Paare von Straßen kritisch sein, die einzeln harmlos sind (Schnitte der Größe 2); das ist Zusammenhangs- und Flussrechnung. | Netzwerkfluss-Linie (Gomory-Hu, Menger) |
| **Alle Ausfälle sind gleich schlimm** | Die Zahl der kritischen Elemente sagt nichts über den Schaden: nahe der Schwelle (Raster bei 40 bis 50 % gesperrt) tragen die schlimmsten 10 % rund 60 % des Gesamtschadens, weiter davon entfernt (Raster bei 20 bis 30 %, Zufallsgraph) nur ein Fünftel bis ein Drittel. | Zentralität und Robustheit (Folgestücke) |
| **Zufällige Sperren** | Die Sperren sind gleichverteilt zufällig; echte Ausfälle sind gehäuft (Hochwasser, Streik) und gezielt. | Robustheit und Kaskaden (Folgestücke) |
| **Die Verstärkung ist konstruiert** | Hier wird nur die kleinste Zahl fehlender Straßen ceil(Blätter / 2) gezählt; welche Paare man verbinden muss und ob diese Straßen gebaut werden können, ist eine eigene Aufgabe (und sie ignoriert Kosten und Geländemöglichkeiten). | Netzwerkdesign, Steiner-Bäume |
| **Elementarschritte zeigen den Aufwand** | Sie zählen Knoten- und Kantenbesuche, keine Rechenzeit. | - |
| **Ungerichtet, synthetische Netze** | Ein gestörtes Raster und ein Zufallsgraph, keine echten Straßennetze, keine Einbahnstraßen. | Starke Zusammenhangskomponenten (Folgestück) |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Graph.** $G=(V,E)$ ungerichtet, $n=|V|$, $m=|E|$. Eine **Brücke** ist eine Kante $e$ mit $c(G-e)>c(G)$ (Komponentenzahl wächst), ein **Artikulationspunkt** ein Knoten $v$, bei dessen Entfernen die Komponente von $v$ in mehr als
eine Teil zerfällt. Ein **Block** ist eine maximale zweifach zusammenhängende Kantenmenge (oder eine einzelne Brücke).

**Low-Link.** Tiefensuche mit Entdeckungszeit $d(v)$; $\mathrm{low}(v)=\min\{d(v),\ d(w)\ \text{für Rückwärtskanten}\ (x,w)\ \text{mit}\ x\ \text{im Teilbaum von}\ v,\ \mathrm{low}(u)\ \text{für Kinder}\ u\}$.
Eine Baumkante $(p,u)$ ist genau dann eine Brücke, wenn $\mathrm{low}(u)>d(p)$; ein Nicht-Wurzelknoten $p$ ist genau dann ein Artikulationspunkt, wenn ein Kind $u$ $\mathrm{low}(u)\ge d(p)$ hat; die Wurzel, wenn sie mindestens
zwei Kinder hat. Aufwand $O(n+m)$.

**Schaden.** Trennt ein Element eine Komponente der Größe $S$ in Teile der Größen $s_1,\dots$, verlieren $\sum_{i<j}s_is_j$ Knotenpaare (bei einer Brücke $a(S-a)$) die Verbindung; bei einem Artikulationspunkt zählen die Paare ohne ihn.

**Verstärkung.** Fasst man die zweifach kantenzusammenhängenden Komponenten zu Knoten zusammen, bilden die Brücken einen Baum (den Brückenbaum). Ist $L$ die Zahl seiner Blätter, sind $\lceil L/2\rceil$ neue Kanten nötig und
ausreichend, damit der Graph brückenfrei wird (Eswaran und Tarjan 1976).

**Literatur.** Tarjan, R. E. (1972). *Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146-160. Hopcroft, J., & Tarjan, R. (1973). *Algorithm 447: efficient algorithms for graph manipulation.*
Communications of the ACM 16(6), 372-378. Eswaran, K. P., & Tarjan, R. E. (1976). *Augmentation problems.* SIAM Journal on Computing 5(4), 653-665.

Implementiert in `brg_algorithm.py` (Low-Link, naive Referenzen, Blöcke, Schaden, Verstärkung), `brg_scenario.py` (Instanzen), `brg_evaluation.py` (Kennzahlen, Sweeps).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html)."
)
