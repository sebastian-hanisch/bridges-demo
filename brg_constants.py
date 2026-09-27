"""Regler-Grenzen, feste Annahmen, gemessene Werte und Presets."""

SPACING = 1.0                    # Abstand der Kreuzungen im Raster
JITTER = 0.18                    # Störung der Kreuzungslage (Anteil des Abstands)
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 4, 30, 12
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("city", "textbook")
KIND_LABELS = {"city": "Betriebsnetz (Karte)", "textbook": "Lehrbuchbeispiel: Brückenstadt (11 Knoten)"}
NETTYPES = ("grid", "random")
NETTYPE_LABELS = {"grid": "Raster (Straßennetz)", "random": "Zufallsgraph (gleiche Kantenzahl)"}
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7, 0.8, 0.9)
DEFAULT_BLOCKED = 0.3
ORDERS = ("fixed", "shuffled")
ORDER_LABELS = {"fixed": "feste Reihenfolge (nach Knotennummer)", "shuffled": "gemischt (nach Seed)"}
STEPS = {1: "1 · Low-Link in Aktion", 2: "2 · Kritische Straßen und Kreuzungen", 3: "3 · Ausfallschaden", 4: "4 · Aufwand und Verstärkung"}
SWEEP_SEEDS = tuple(range(100000, 100005))
CRIT_SIDE = 20                                              # Seitenlänge der Instanzen im Sweep der kritischen Anteile (400 Knoten)
COST_SIDES = (4, 6, 8, 10, 12, 14)                          # Seitenlängen im Aufwands-Sweep (16 bis 196 Knoten; der naive Test ist quadratisch teuer)
DENSITY_N, DENSITY_FACTORS = 144, (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0)
NAIVE_MAX_N = 400                                           # bis zu dieser Knotenzahl läuft der naive Test auch für die aktuelle Instanz

# --- Gemessene Werte (MEDIAN über 5 feste Instanzen, Seeds 100000-100004; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed und ändern sich nie mit einer
# --- Bibliotheksversion; 2026-09-27, alle Werte über ev.* nachgerechnet, s. tests/test_claims.py) ---
# KRITISCHE ANTEILE (Raster 20 x 20; Brücken an den Straßen, Artikulationspunkte an den Knoten der GRÖSSTEN Komponente): ungesperrt 0 / 0 %; bei 10/20/30/40/50 % gesperrt Brücken 1/4/11/24/44 % und Artikulationspunkte
#   2/6/14/26/43 %; beide steigen monoton (bis das Netz zerfallen ist: dann ist die größte Komponente ein kleiner Baum). Zufallsgraph gleicher Kantenzahl: schon ungesperrt 5 % Brücken (Stichstraßen) und 10 % Artikulationspunkte.
# DICHTE (Zufallsgraph, 144 Knoten): Brückenanteil bei 0.5/0.75/1.0/1.25/1.5/2.0/2.5/3.0 Straßen je Knoten 100/58/30/21/10/4/1/0 %.
# AUFWAND (30 % gesperrt): der naive Ausfalltest (jede Straße und jede Kreuzung entfernen, Komponenten neu zählen) braucht bei n = 16/36/64/100/144/196 Knoten das 34/79/143/227/330/452-Fache der Schritte einer Low-Link-Tiefensuche,
#   also rund das 2.3-Fache von n (naiv ~ m (n + m), Low-Link ~ n + m).
# SCHADEN: Anteil des Gesamtschadens (verlorene Knotenpaare), den die schlimmsten 10 % der kritischen Elemente tragen: Raster bei 20/30/40/50 % gesperrt 25/33/61/58 %, Zufallsgraph 21/23/28/33 % - eine starke Konzentration
#   (80/20) gibt es nur nahe der Schwelle. Artikulationspunkte, die kein Ende einer Brücke sind: höchstens 2 %.
# VERSTÄRKUNG (Raster 20 x 20, größte Komponente): fehlende Straßen ceil(Blätter / 2) bei 10/20/30/40/50 % gesperrt 3/9/21/30/26 gegen 6/23/56/100/106 Brücken: ein Viertel bis die Hälfte so viele neue Straßen wie Brücken.

PRESETS = {
    "Brückenstadt (Lehrbuch)": {"kind": "textbook", "step": 1},
    "Standardfall (Voreinstellung)": {"kind": "city", "side": 12, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
    "Kaum gesperrt": {"kind": "city", "side": 12, "blocked": 0.1, "nettype": "grid", "seed": 35, "order": "fixed", "step": 2},
    "Nahe der Schwelle": {"kind": "city", "side": 20, "blocked": 0.5, "nettype": "grid", "seed": 27, "order": "fixed", "step": 3},
    "Zufallsgraph, dicht": {"kind": "city", "side": 12, "blocked": 0.0, "nettype": "random", "seed": 35, "order": "fixed", "step": 2},
    "Zufallsgraph, dünn": {"kind": "city", "side": 12, "blocked": 0.5, "nettype": "random", "seed": 35, "order": "fixed", "step": 2},
    "Der Schaden ist schief verteilt": {"kind": "city", "side": 20, "blocked": 0.4, "nettype": "grid", "seed": 35, "order": "fixed", "step": 3},
    "Aufwand: naiv gegen Low-Link": {"kind": "city", "side": 12, "blocked": 0.3, "nettype": "grid", "seed": 35, "order": "fixed", "step": 4},
    "Verstärkung: wie viele Straßen fehlen?": {"kind": "textbook", "step": 4},
}
PRESET_HELP = {
    "Brückenstadt (Lehrbuch)": "11 Kreuzungen A bis K, 13 Straßen: ein Block links, ein Rundweg rechts, dazwischen D-E, dazu ein Stichweg G-I-J und die Stichstraße A-K. Von Hand: 4 Brücken (D-E, G-I, I-J, A-K), "
                               "5 Artikulationspunkte (A, D, E, G, I). Die Wiedergabe zeigt Schritt für Schritt, wann low[u] > disc[p] eine Brücke verrät.",
    "Standardfall (Voreinstellung)": "12 × 12 Kreuzungen (144 Knoten), 30 % der Straßen gesperrt (185 Straßen, 4 Komponenten): 21 Brücken und 17 Artikulationspunkte; von den 184 Straßen der größten Komponente sind 20 Brücken (10.9 %). "
                                     "Ein einziger großer Block enthält 164 Straßen, dazu kommen 22 Blöcke insgesamt.",
    "Kaum gesperrt": "Dasselbe Raster, nur 10 % gesperrt: 238 Straßen, ein zusammenhängendes Netz mit nur 4 Brücken und 3 Artikulationspunkten; der große Block enthält 234 von 238 Straßen. Eine einzige neue Straße würde das Netz brückenfrei machen.",
    "Nahe der Schwelle": "20 × 20 Kreuzungen, die Hälfte der Straßen gesperrt: die größte Komponente hat 237 Knoten und besteht zu 58.8 % aus Brücken (153 von 260 Straßen) und zu 55.7 % aus Artikulationspunkten (132 Kreuzungen). "
                         "Die Kreuzung 151 allein trennt 18378 Knotenpaare; brückenfrei würde die Komponente erst mit 27 neuen Straßen.",
    "Zufallsgraph, dicht": "Zufallsgraph mit 144 Knoten und 264 Straßen (1.8 je Knoten): auch hier gibt es 19 Brücken (7.2 %), davon 16 Stichstraßen zu Knoten mit nur einer Straße, und 17 Artikulationspunkte; der große Block enthält 245 von 264 Straßen.",
    "Zufallsgraph, dünn": "Zufallsgraph mit derselben Knotenzahl, aber nur 132 Straßen (0.9 je Knoten): 31 Komponenten, die größte hat 105 Knoten und besteht zu 38.2 % aus Brücken (47 von 123 Straßen); 20 neue Straßen fehlen insgesamt für Brückenfreiheit.",
    "Der Schaden ist schief verteilt": "20 × 20 Kreuzungen, 40 % gesperrt: 136 Brücken und 123 Artikulationspunkte, aber die schlimmsten 10 % der kritischen Elemente tragen 71 % des gesamten Ausfallschadens; die schlimmste Brücke (Straße 146-166) trennt allein 26404 Knotenpaare.",
    "Aufwand: naiv gegen Low-Link": "Derselbe Standardfall: der naive Ausfalltest (jede Straße und jede Kreuzung entfernen und neu zählen) braucht 169620 Elementarschritte, Tarjans Low-Link 514, also das 330-Fache.",
    "Verstärkung: wie viele Straßen fehlen?": "Die Brückenstadt hat zwei Blattkomponenten im Brückenbaum (J und K): eine einzige neue Straße J-K schließt einen Ring über alle vier Brücken, danach bleibt keine Brücke. Allgemein: ceil(Blätter / 2) Straßen.",
}
