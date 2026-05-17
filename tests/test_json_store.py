from __future__ import annotations

from pathlib import Path

from vibecode.storage.json_store import JsonStore


def test_json_store_save_and_load(temp_base: Path) -> None:
    store = JsonStore(temp_base / "test_entities")
    store.save("abc", {"name": "hello"})
    loaded = store.load("abc")
    assert loaded == {"name": "hello"}


def test_json_store_load_all(temp_base: Path) -> None:
    store = JsonStore(temp_base / "test_entities")
    store.save("a", {"x": 1})
    store.save("b", {"x": 2})
    all_items = store.load_all()
    assert len(all_items) == 2


def test_json_store_exists_and_delete(temp_base: Path) -> None:
    store = JsonStore(temp_base / "test_entities")
    store.save("del", {"ok": True})
    assert store.exists("del")
    assert store.delete("del")
    assert not store.exists("del")
    assert not store.delete("del")
