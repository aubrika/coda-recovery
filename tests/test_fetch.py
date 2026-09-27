"""The source fetcher must reject unexpected input bytes before installing them."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("fetch", Path(__file__).parents[1] / "data/fetch.py")
fetch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch)


@pytest.fixture
def source(tmp_path, monkeypatch):
    (tmp_path / "data").mkdir()
    manifest = {"files": [{"dataset": "sharma", "path": "data/raw/sample",
                           "url": "https://example.invalid/input",
                           "sha256": hashlib.sha256(b"expected").hexdigest()}]}
    (tmp_path / "data/sources.json").write_text(json.dumps(manifest), encoding="utf-8")
    monkeypatch.setattr(fetch, "ROOT", tmp_path)
    monkeypatch.setattr("sys.argv", ["fetch.py", "sharma"])
    return tmp_path / "data/raw/sample"


def test_bad_download_is_not_installed(source, monkeypatch):
    monkeypatch.setattr(fetch, "urlopen", lambda *a, **k: io.BytesIO(b"changed upstream"))
    with pytest.raises(SystemExit, match="Checksum mismatch"):
        fetch.main()
    assert not source.exists()


def test_verified_download_and_offline_recheck(source, monkeypatch):
    monkeypatch.setattr(fetch, "urlopen", lambda *a, **k: io.BytesIO(b"expected"))
    fetch.main()
    assert source.read_bytes() == b"expected"
    monkeypatch.setattr("sys.argv", ["fetch.py", "all", "--verify"])
    fetch.main()
    source.write_bytes(b"local change")
    with pytest.raises(SystemExit, match="Checksum mismatch"):
        fetch.main()
    assert source.read_bytes() == b"local change"
