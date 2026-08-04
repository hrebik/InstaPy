"""Testy pipeline: eventy → engine → snapshoty."""
from ai_trading.engine import Engine
from ai_trading.events import Trade, to_json, from_json
from ai_trading.feed_synthetic import synthetic_session
from ai_trading.replay import ordered


def test_event_roundtrip():
    tr = Trade(t=123, price=5000.25, size=10, aggressor="buy")
    assert from_json(to_json(tr)) == tr


def test_replay_is_chronological():
    evs = list(ordered(synthetic_session(n_trades=500)))
    times = [e.t for e in evs]
    assert times == sorted(times)


def test_engine_produces_snapshots_and_detects_trends():
    engine = Engine()
    snaps = []
    n = engine.run(ordered(synthetic_session(n_trades=4000)), snaps.append)
    assert n == len(snaps) > 0
    trends = {s.trend for s in snaps}
    # syntetická session jde up → absorpce → down, takže oba trendy nastanou
    assert "up" in trends and "down" in trends


def test_absorption_detected():
    engine = Engine()
    snaps = []
    engine.run(ordered(synthetic_session(n_trades=4000)), snaps.append)
    assert engine.of.absorptions, "absorpce v absorpčním pásmu se má detekovat"


def test_volume_profile_has_poc():
    engine = Engine()
    engine.run(ordered(synthetic_session(n_trades=2000)), lambda s: None)
    assert engine.vp.poc is not None
    assert engine.vp.value_area() is not None
