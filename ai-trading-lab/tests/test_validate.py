"""Testy labeling + validační smyčky."""
import os
import tempfile

from ai_trading.events import write_events
from ai_trading.feed_synthetic import synthetic_session
from ai_trading.labels import Label, append_label, read_labels
from ai_trading.validate import validate, run_engine


def _make_feed(path: str) -> None:
    write_events(path, synthetic_session())


def test_label_roundtrip(tmp_path):
    path = str(tmp_path / "labels.ndjson")
    lab = Label(t=123, pattern="absorption", side="ask", price=5100.0, note="x")
    append_label(path, lab)
    assert read_labels(path) == [lab]


def test_validate_matches_engine_absorptions(tmp_path):
    feed = str(tmp_path / "feed.ndjson")
    _make_feed(feed)
    _, absorptions = run_engine(feed)
    assert absorptions, "syntetika má mít absorpce"

    # labely vyrobené z reálných detekcí (posun 3 s) → mají se napárovat
    labels = [Label(t=a.t + 3 * 10**9, pattern="absorption", side=a.side, price=a.price)
              for a in absorptions]
    rep = validate(feed, labels, tol_s=20)
    assert rep.recall == 1.0
    assert not rep.missed


def test_validate_misses_far_labels(tmp_path):
    feed = str(tmp_path / "feed.ndjson")
    _make_feed(feed)
    _, absorptions = run_engine(feed)
    # label hodně mimo čas → engine ho nemá potvrdit
    far = [Label(t=absorptions[0].t + 10**12, pattern="absorption")]
    rep = validate(feed, far, tol_s=20)
    assert rep.recall == 0.0
    assert len(rep.missed) == 1
