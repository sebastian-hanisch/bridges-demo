"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt für jede Instanz und jeden Netztyp, Schritt-Regler, Ausfall-Auswahl, Randwerte, Permalink-Grenzen, bedingte Regler, Berechnungen auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import brg_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=300)
    state.setdefault("brg_step", step)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _click(at, key):
    next(b for b in at.button if b.key == key).click().run()


def test_default_run_shows_the_summary():
    at = _run()
    _ok(at)
    assert {"Kritische Straßen", "Kritische Kreuzungen", "Schlimmster Ausfall", "Fehlende Straßen"} <= {m.label for m in at.metric}
    assert any("Kreuzungen" in md.value and "Straßen" in md.value for md in at.markdown)


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run(kind_select="textbook")
    _click(at, f"preset_{name}")
    _ok(at)
    p, ss = C.PRESETS[name], at.session_state
    assert ss["kind_select"] == p["kind"] and ss["brg_step"] == p["step"]
    for key, state_key in (("side", "side_slider"), ("blocked", "blocked_select"), ("nettype", "nettype_select"), ("seed", "seed_input"), ("order", "order_select")):
        if key in p:
            assert ss[state_key] == p[key], (name, key)
    if p["kind"] == "city":
        assert ss["side_widget"] == p["side"] and ss["blocked_widget"] == p["blocked"] and ss["nettype_widget"] == p["nettype"] and ss["seed_widget"] == p["seed"]


@pytest.mark.parametrize("step", [1, 2, 3, 4])
@pytest.mark.parametrize("kind", ["city", "textbook"])
@pytest.mark.parametrize("nettype", ["grid", "random"])
def test_every_step_runs_for_every_kind_and_nettype(step, kind, nettype):
    at = _run(step=step, kind_select=kind, nettype_select=nettype, side_slider=6, blocked_select=0.4)
    _ok(at)
    assert at.session_state["brg_step"] == step


def test_search_slider_every_position_on_the_textbook_and_a_small_grid():
    for state in (dict(kind_select="textbook"), dict(kind_select="city", side_slider=4, blocked_select=0.3)):
        at = _run(step=1, **state)
        _ok(at)
        n_events = at.session_state["search_k"]                       # Voreinstellung: der ganze Lauf
        for k in sorted({1, 2, n_events // 2, n_events}):
            at2 = _run(step=1, search_k=k, **state)
            _ok(at2)
            assert at2.session_state["search_k"] == k


def test_damage_selection_every_top_element_and_stale_selection():
    at = _run(step=3, kind_select="textbook")
    _ok(at)
    for i in range(9):
        at.session_state["dmg_pick"] = i
        at.run()
        _ok(at)
    at2 = _run(step=3, kind_select="city", side_slider=8, blocked_select=0.3, dmg_pick=0)
    _ok(at2)
    at3 = _run(step=3, kind_select="city", side_slider=4, blocked_select=0.9)          # kaum kritische Elemente: keine Auswahl nötig
    _ok(at3)


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="nope", side="999", blocked="0.33", net="wheel", order="sorted", seed="-4", step="9").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["kind_select"], ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["order_select"], ss["seed_input"], ss["brg_step"]) == ("city", C.SIDE_MAX, C.DEFAULT_BLOCKED, "grid", "fixed", 0, 1)


def test_permalink_accepts_valid_values_and_writes_them_back():
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in dict(kind="city", side="9", blocked="0.5", net="random", order="shuffled", seed="7", step="3").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["side_slider"], ss["blocked_select"], ss["nettype_select"], ss["order_select"], ss["seed_input"], ss["brg_step"]) == (9, 0.5, "random", "shuffled", 7, 3)
    assert at.query_params["net"] == ["random"] and at.query_params["blocked"] == ["0.5"] and at.query_params["step"] == ["3"]
    assert ss["side_widget"] == 9 and ss["seed_widget"] == 7


def test_sidebar_shows_the_controls_that_belong_to_the_instance():
    city = _run(kind_select="city")
    assert any(w.key == "side_widget" for w in city.slider) and any(s.key == "blocked_widget" for s in city.select_slider) and any(r.key == "nettype_widget" for r in city.radio)
    book = _run(kind_select="textbook")
    assert not any(w.key == "side_widget" for w in book.slider) and not any(s.key == "blocked_widget" for s in book.select_slider) and any(r.key == "order_select" for r in book.radio)


def test_switching_kind_back_and_forth_keeps_the_stored_values():
    at = _run(kind_select="city", side_slider=9, blocked_select=0.5, seed_input=11)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    at.session_state["kind_select"] = "city"
    at.run()
    _ok(at)
    assert at.session_state["side_widget"] == 9 and at.session_state["blocked_widget"] == 0.5 and at.session_state["seed_widget"] == 11


def test_dice_button_changes_the_seed_and_the_visible_widget():
    at = _run(kind_select="city")
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old and at.session_state["seed_widget"] == at.session_state["seed_input"]


def test_on_demand_experiments():
    two = _run(step=2)
    for key in ("crit_start", "dens_start"):
        _click(two, key)
        _ok(two)
    assert len(two.get("plotly_chart")) >= 4
    four = _run(step=4)
    for key in ("cost_start", "aug_start"):
        _click(four, key)
        _ok(four)
    assert len(four.get("plotly_chart")) >= 3


def test_naive_test_is_skipped_for_large_networks():
    big = _run(step=4, kind_select="city", side_slider=25, blocked_select=0.3)
    _ok(big)
    assert any("nicht mitgerechnet" in i.value for i in big.info)
    small = _run(step=4, kind_select="city", side_slider=6, blocked_select=0.3)
    _ok(small)
    assert any(m.label == "Naiv" for m in small.metric)


@pytest.mark.parametrize("kw", [dict(side_slider=C.SIDE_MIN, blocked_select=0.0), dict(side_slider=C.SIDE_MAX, blocked_select=0.9), dict(side_slider=C.SIDE_MIN, blocked_select=0.9, nettype_select="random"),
                                dict(side_slider=10, blocked_select=0.5, nettype_select="random", order_select="shuffled"), dict(side_slider=C.SIDE_MAX, blocked_select=0.0, order_select="shuffled")])
def test_extreme_settings_run_on_every_step(kw):
    for step in (1, 2, 3, 4):
        _ok(_run(step=step, kind_select="city", **kw))


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Eswaran" in m.value and "Hopcroft" in m.value for e in at.expander for m in e.markdown)
