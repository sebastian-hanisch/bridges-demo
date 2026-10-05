# Brücken und Artikulationspunkte – welche einzelne Straße darf nicht ausfallen? – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-bridges-demo.streamlit.app/)**

Zweites Stück der **Graphen-und-Netzwerke-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning", Kind der Durchmusterung ([bfs-dfs-demo](https://github.com/sebastian-hanisch/bfs-dfs-demo)). Dort wurde gemessen, wie ein Straßennetz beim Sperren zerfällt; als Grenze blieb, dass einzelne Straßen und Kreuzungen etwas anderes sind als zufällige Sperren: Manche Straße ist eine **Brücke** (ohne sie zerfällt das Netz), manche Kreuzung ein **Artikulationspunkt**. Der naive Weg, sie zu finden, entfernt jedes Element und zählt nach; **Tarjans Low-Link** braucht nur **eine** Tiefensuche und eine Zahl je Knoten. Die Demo misst vier Dinge: (1) **Low-Link in Aktion** – wie verrät low[u] > disc[p] eine Brücke? (2) **Kritische Straßen und Kreuzungen** – wie viele sind es, wie sehen Blöcke und Blockbaum aus? (3) **Ausfallschaden** – wie viele Knotenpaare verlieren beim Ausfall die Verbindung, und wie ungleich ist das verteilt? (4) **Aufwand und Verstärkung** – was spart Low-Link, und wie viele Straßen fehlen mindestens, damit keine Brücke bleibt?

**Einordnung in die Reihe:** die Reihe hat dreizehn Stücke (zwölf davon im Baum unten, dazu die Analyse-Karte `interne-verlinkung-demo`), dies ist das zweite des Baums (Details in `graphen-planung/PLAN.md` des Portfolio-Ordners):

```
1 BFS und DFS (Wurzel)                                                        [gebaut: bfs-dfs-demo]
 ├─ 2 Brücken und Artikulationspunkte ─ 4 Euler-Touren                        [DIESES STÜCK] [gebaut: euler-tour-demo]
 ├─ 3 Starke Zusammenhangskomponenten, topologische Sortierung                [gebaut: scc-demo]
 ├─ 5 Graphfärbung                                                            [gebaut: graph-coloring-demo]
 ├─ 6 Zentralität ─ 7 Strukturkennzahlen                                      [gebaut: centrality-demo, strukturkennzahlen-demo]
 │        ├─ 8 Robustheit ─ 9 Kaskaden und Ausbreitung                        [gebaut: robustheit-demo, kaskaden-demo]
 │        └─ 10 Kritische Knoten härten                                       [gebaut: haertung-demo]
 └─ 11 Bandbreite ─ 12 Bandbreite von G(n,k,b) und Cliquenüberdeckung         [gebaut: bandbreite-demo, cliquenbandbreite-demo]
```

Ergebnis in Kürze: **Der naive Ausfalltest kostet auf einem Straßennetz mit n Knoten das rund 2.3-Fache von n mal so viele Schritte wie eine Low-Link-Tiefensuche (n = 16: 34-fach, n = 196: 452-fach) – und die kritischen Elemente sind kein seltener Sonderfall: bei 30 % gesperrter Straßen sind 11 % der Straßen der größten Komponente Brücken und 14 % ihrer Kreuzungen Artikulationspunkte, bei 50 % gesperrt 44 % und 43 %.** Der Ausfallschaden ist nur nahe der Schwelle stark konzentriert (die schlimmsten 10 % der kritischen Elemente tragen bei 40 % gesperrt 61 % des Schadens, bei 20 % gesperrt 25 %; im Zufallsgraph 21 bis 33 %). Brückenfrei machen ließe sich das Netz mit **ceil(Blätter / 2)** neuen Straßen – ein Viertel bis die Hälfte so viele, wie es Brücken gibt.

## Warum dieses Problem

Fällt eine einzelne Straße aus, gibt es meist einen Umweg – manchmal nicht. Die Brücken und Artikulationspunkte eines Netzes sind die Stellen, an denen ein *einzelner* Ausfall etwas trennt: die erste, billigste Antwort auf "wo ist mein Netz verwundbar?". Die Demo zeigt, wie man sie in einem Durchgang findet, wie viele es auf einem realistisch gestörten Straßennetz gibt und wie ungleich der Schaden ist. Sie ist zugleich der Baustein für die Folgestücke: Euler-Touren brauchen den Brückentest (Fleury), Zentralität und Robustheit vergleichen die gefundenen kritischen Elemente mit Kennzahlen.

Abgrenzung: die **MST-Sensitivität** (Spannbaum-Reihe) misst Brücken nur am *Spannbaum* ("keine Ersatzkante" für eine Baumkante, k-nächste-Nachbarn-Graphen); hier sind es die Brücken des *Netzes selbst* auf einem gesperrten Raster und einem Zufallsgraph, dazu Artikulationspunkte, Blöcke, Schaden und Verstärkung.

## Vorab-Hypothesen (vor der Messung notiert, hier geprüft)

| Hypothese (aus dem Plan) | Ergebnis |
|---|---|
| **H1** Low-Link und der naive Test finden dieselben Brücken und Artikulationspunkte. | ✅ Bestätigt (Satz, im Test auf 169 Instanzen gegen networkx, dazu Blöcke gegen `biconnected_component_edges`). |
| **H2** Der naive Aufwand wächst wie m · (n + m), Low-Link linear: das Verhältnis wächst etwa mit n. | ✅ Bestätigt: Verhältnis 34 / 79 / 143 / 227 / 330 / 452 bei n = 16 / 36 / 64 / 100 / 144 / 196, also rund das 2.3-Fache von n. |
| **H3** Der Anteil der Artikulationspunkte hat ein Maximum nahe der Perkolationsschwelle, der der Brücken steigt monoton. | ❌ **Widerlegt:** beide Anteile steigen bis zur Schwelle monoton (Brücken 1/4/11/24/44 %, Artikulationspunkte 2/6/14/26/43 % bei 10/20/30/40/50 % gesperrt); jenseits der Schwelle ist die größte Komponente nur noch ein kleiner Baum (jede Straße eine Brücke), dort schwanken die Zahlen mit den winzigen Instanzen und zeigen kein verlässliches Maximum. |
| **H4** Im Zufallsgraph verschwinden die Brücken mit wachsender Dichte schnell. | ✅ Bestätigt: bei 0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 2.0 / 2.5 / 3.0 Straßen je Knoten 100 / 58 / 30 / 21 / 10 / 4 / 1 / 0 % (144 Knoten). Auch bei hoher Dichte bleiben Stichstraßen zu Knoten mit einer einzigen Straße. |
| **H5** Der Ausfallschaden ist schief verteilt: wenige Elemente tragen den Großteil. | ⚠ **Nur teilweise:** die schlimmsten 10 % der kritischen Elemente tragen im Raster 25 / 33 / 61 / 58 % des Gesamtschadens bei 20 / 30 / 40 / 50 % gesperrt (Zufallsgraph 21 / 23 / 28 / 33 %); eine starke Konzentration (Pareto) gibt es nur nahe der Schwelle. |
| **H6** ceil(L / 2) stimmt mit der exakt kleinsten Zahl überein und ist klein gegenüber der Zahl der Brücken. | ✅ Bestätigt: 70 zufällige verbundene Graphen mit 3 bis 7 Knoten gegen Aufzählung aller Kantenmengen; gemessen 3 / 9 / 21 / 30 / 26 fehlende Straßen gegen 6 / 23 / 56 / 100 / 106 Brücken bei 10 / 20 / 30 / 40 / 50 % gesperrt (ein Viertel bis die Hälfte). |
| **H7** Ein Teil der Artikulationspunkte ist kein Ende einer Brücke. | ❌ **Kaum:** höchstens 2 % (Median) der Artikulationspunkte sind keine Brückenenden; auf Straßennetzen ist eine Kreuzung fast nur dort kritisch, wo eine Brücke anschließt. |

## Befunde (gemessen, keine Behauptungen)

Median über 5 feste Instanzen (Seeds 100000–100004), Raster mit 20 × 20 Knoten in den Sweeps; alle Verfahren sind deterministisch, die Instanzen kommen aus Python-`random` mit festem Seed (die Zahlen ändern sich nie mit einer Bibliotheksversion). Anteile beziehen sich auf die **größte Komponente**.

| Frage | Ergebnis |
|---|---|
| **Stimmt das Verfahren?** | ✅ Brücken == networkx.bridges, Artikulationspunkte == networkx.articulation_points, Blöcke == networkx.biconnected_component_edges auf 169 Instanzen (Raster und Zufallsgraph, Sperranteil 0 bis 100 %, n = 1 und 2, Baum, Kreis, Stern, vollständiger Graph, mehrere Komponenten) und in beiden Nachbarreihenfolgen; naiver Test == Low-Link; die Blöcke partitionieren die Straßen, zwei Blöcke teilen höchstens einen Artikulationspunkt, der Blockbaum ist ein Wald; Schaden gegen wirkliches Entfernen auf über 100 kritischen Elementen; Verstärkung gegen Aufzählung |
| **Kritische Anteile (Raster)** | Brücken **0 / 1 / 4 / 11 / 24 / 44 %** und Artikulationspunkte **0 / 2 / 6 / 14 / 26 / 43 %** bei 0 / 10 / 20 / 30 / 40 / 50 % gesperrt; Zufallsgraph gleicher Kantenzahl schon ungesperrt 5 % Brücken und 10 % Artikulationspunkte |
| **Dichte (Zufallsgraph, 144 Knoten)** | Brückenanteil **100 / 58 / 30 / 21 / 10 / 4 / 1 / 0 %** bei 0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 2.0 / 2.5 / 3.0 Straßen je Knoten |
| **Aufwand (30 % gesperrt)** | naiver Ausfalltest gegen Low-Link **34 / 79 / 143 / 227 / 330 / 452**-fach bei n = 16 / 36 / 64 / 100 / 144 / 196; Low-Link zählt n + 2 m Elementarschritte |
| **Schadenskonzentration** | schlimmste 10 % der kritischen Elemente tragen im Raster **25 / 33 / 61 / 58 %** des Gesamtschadens bei 20 / 30 / 40 / 50 % gesperrt, im Zufallsgraph **21 / 23 / 28 / 33 %** |
| **Verstärkung** | fehlende Straßen ceil(Blätter / 2): **3 / 9 / 21 / 30 / 26** gegen **6 / 23 / 56 / 100 / 106** Brücken (10 bis 50 % gesperrt) |

Presets (9), alle mit den Zahlen in ihren Hilfetexten (`tests/test_presets.py`):

| Preset | Was es zeigt |
|---|---|
| Brückenstadt (Lehrbuch) | 11 Kreuzungen A bis K, 13 Straßen: 4 Brücken (D-E, G-I, I-J, A-K), 5 Artikulationspunkte (A, D, E, G, I); die Wiedergabe zeigt, wann low[u] > disc[p] eine Brücke verrät |
| Standardfall (Voreinstellung) | 12 × 12, 30 % gesperrt (Seed 35): 185 Straßen, 4 Komponenten, 21 Brücken, 17 Artikulationspunkte, 20 Brücken unter den 184 Straßen der größten Komponente (10.9 %); ein Block mit 164 Straßen, 22 Blöcke insgesamt |
| Kaum gesperrt | 12 × 12, 10 % gesperrt: 238 Straßen, nur 4 Brücken und 3 Artikulationspunkte, ein Block mit 234 Straßen; eine neue Straße genügt |
| Nahe der Schwelle | 20 × 20, 50 % gesperrt (Seed 27): größte Komponente 237 Knoten, 58.8 % Brücken, 55.7 % Artikulationspunkte; Kreuzung 151 trennt allein 18378 Knotenpaare; 27 neue Straßen fehlen |
| Zufallsgraph, dicht | 144 Knoten, 264 Straßen: 19 Brücken (16 Stichstraßen), 17 Artikulationspunkte, Block mit 245 Straßen |
| Zufallsgraph, dünn | 132 Straßen: 31 Komponenten, größte 105 Knoten mit 38.2 % Brücken (47 von 123); 20 neue Straßen fehlen insgesamt |
| Der Schaden ist schief verteilt | 20 × 20, 40 % gesperrt: 136 Brücken, 123 Artikulationspunkte; die schlimmsten 10 % tragen 71 % des Schadens; die schlimmste Brücke (146-166) trennt 26404 Knotenpaare |
| Aufwand: naiv gegen Low-Link | Standardfall: 169620 gegen 514 Elementarschritte (330-fach) |
| Verstärkung: wie viele Straßen fehlen? | Brückenstadt: die Blätter J und K, eine neue Straße J-K macht sie brückenfrei |

## Modell und Verfahren

- **Instanz** (`brg_scenario.py`): gestörtes Raster mit gesperrten Straßen (das Netz darf zerfallen) oder Zufallsgraph mit derselben Knoten- und Kantenzahl, aus der BFS-und-DFS-Demo übernommen; Lehrbuchbeispiel *Brückenstadt* von Hand nachrechenbar.
- **Low-Link** (`brg_algorithm.low_link`): iterative Tiefensuche mit Entdeckungszeit disc und low; Baumkante (p, u) ist Brücke, wenn low[u] > disc[p]; p ist Artikulationspunkt, wenn ein Kind u low[u] ≥ disc[p] hat (Wurzel: mindestens zwei Kinder); Blöcke über einen Kantenstapel (Hopcroft und Tarjan 1973). Die Ereignisse (Wurzel, entdeckt, Rückwärtskante, abgeschlossen) speisen die Wiedergabe.
- **Naiver Test** (`bridges_naive`, `articulation_naive`): je Straße bzw. Kreuzung entfernen, Komponenten neu zählen; Aufwand ~ m · (n + m).
- **Schaden** (`damages`): verlorene Knotenpaare – bei einer Brücke a · (S − a), bei einem Artikulationspunkt die Paare der Restkomponente minus die Paare innerhalb der entstehenden Teile; aus den Teilbaumgrößen berechnet, gegen wirkliches Entfernen geprüft.
- **Verstärkung** (`augmentation_need`): Brückenbaum aus den zwei-kantenzusammenhängenden Komponenten; ceil(Blätter / 2) je Komponente (Eswaran und Tarjan 1976), **nur gezählt, nicht konstruiert**.
- **Elementarschritte:** jeder abgearbeitete Knoten und jede von einem Ende angesehene Kante zählt 1; ein Näherungsmaß, keine Laufzeit.

## Was die App zeigt

1. **Vier Schritte** (Schritt-Regler): **Low-Link in Aktion** (Regler über die Ereignisse der Tiefensuche, Tabelle mit disc und low je Knoten, gefundene Brücken und Artikulationspunkte) → **Kritische Straßen und Kreuzungen** (Karte mit Brücken rot und Artikulationspunkten als Rauten, Blockbaum; auf Abruf: Anteile über den Sperranteil für beide Netztypen, Brückenanteil über die Dichte) → **Ausfallschaden** (Rangliste, Pareto-Kurve, Auswahl eines Ausfalls mit den entstehenden Teilen) → **Aufwand und Verstärkung** (naiv gegen Low-Link, auf Abruf über die Größe; ceil(Blätter / 2) mit markierten Blattkomponenten, auf Abruf über den Sperranteil).
2. Regler: Instanz, Kreuzungen je Seite (4 bis 30), gesperrter Anteil (0 bis 90 %), Netztyp, Nachbarreihenfolge, Seed (+🎲); Permalink in der Adresszeile.

## Was nicht funktioniert hat / Grenzen

- **Ein einzelner Ausfall.** Brücken und Artikulationspunkte beantworten nur "was trennt *ein* Ausfall". Fallen zwei Straßen zugleich aus, sind Paare kritisch, die einzeln harmlos sind (Schnitte der Größe 2): Zusammenhangs- und Flussrechnung (Netzwerkfluss-Linie).
- **H3 und H7 widerlegt:** kein Maximum des Artikulationsanteils nahe der Schwelle; Artikulationspunkte sind auf Straßennetzen fast nur dort kritisch, wo eine Brücke anschließt.
- **Der Schaden ist nur nahe der Schwelle stark konzentriert** (bei 20 % gesperrt tragen die schlimmsten 10 % nur ein Viertel); die Zahl kritischer Elemente sagt wenig über den Schaden. Eine Brücke und ihr Ende werden in der Rangliste je für sich gezählt.
- **Die Verstärkung ist nur gezählt.** Welche Blattpaare man verbindet und ob diese Straßen gebaut werden können (Kosten, Gelände), ist ein eigenes Problem (Netzwerkdesign); die Demo rechnet die kleinste Zahl fehlender Straßen für einfache Graphen, geprüft gegen Aufzählung bis 7 Knoten.
- **Zufällige Sperren und synthetische Netze.** Ein gestörtes Raster und ein Zufallsgraph, gleichverteilte Sperren; echte Ausfälle sind gehäuft und gezielt; keine Einbahnstraßen (starke Zusammenhangskomponenten sind ein Folgestück). Der naive Test wird nur bis 400 Knoten für die aktuelle Instanz mitgerechnet.
- **Elementarschritte statt Laufzeit:** die Verhältnisse (bis 452-fach) gelten für das Zählmaß, echte Laufzeiten hängen an der Implementierung.

## Tests

`tests/test_algorithm.py` (15: Brücken, Artikulationspunkte und Blöcke gegen networkx in beiden Nachbarreihenfolgen, Sonderfälle, naiv == Low-Link, Blockbaum, Schaden gegen wirkliches Entfernen, Verstärkung gegen Aufzählung, Buchführung, Brückenstadt von Hand), `tests/test_scenario.py` (5), `tests/test_evaluation.py` (5), `tests/test_presets.py` (jede Zahl der Hilfetexte), `tests/test_claims.py` (jede README-Zahl über die echten Auswertungsfunktionen), `tests/test_app.py` (AppTest: Voreinstellung, jedes Preset, jeder Schritt für beide Instanzen und Netztypen, jede Position des Ereignis-Reglers, Ausfall-Auswahl, Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer).

```
python -m pytest tests/ -v
```

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-App |
| `brg_algorithm.py` | Low-Link, naive Referenzen, Blöcke, Blockbaum, Schaden, Verstärkung |
| `brg_scenario.py` | Raster, Zufallsgraph, Brückenstadt |
| `brg_evaluation.py` | Analyse, Sweeps (Aufwand, kritische Anteile, Dichte, Schaden, Verstärkung) |
| `brg_visualization.py` | Plotly-Figuren |
| `brg_presets.py`, `brg_constants.py` | Permalink, Presets, gemessene Werte |
| `tests/` | Tests |

## Bewusst nicht umgesetzt

Konstruktion der verstärkenden Straßen, Knoten-Verstärkung (Artikulationspunkte beseitigen), gerichtete Netze und starke Zusammenhangskomponenten, Euler-Touren, Zentralität und gezielte Angriffe, Kaskaden – eigene Stücke der Reihe.

## Lokal ausführen

```
python -m venv venv
venv\Scripts\pip install -r requirements-dev.txt
venv\Scripts\streamlit run app.py
```

## Literatur

- Tarjan, R. E. (1972). *Depth-first search and linear graph algorithms.* SIAM Journal on Computing 1(2), 146–160.
- Hopcroft, J., & Tarjan, R. (1973). *Algorithm 447: efficient algorithms for graph manipulation.* Communications of the ACM 16(6), 372–378.
- Eswaran, K. P., & Tarjan, R. E. (1976). *Augmentation problems.* SIAM Journal on Computing 5(4), 653–665.

Gebaut mit Streamlit, Plotly, NumPy und pandas.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Graphen und Netzwerke: BFS bis Cliquenbandbreite](https://sebastianhanisch.net/konzepte-graphen-netzwerke.html).
