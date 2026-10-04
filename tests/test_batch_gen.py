import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import batch_gen


def test_read_prompts_skips_blanks():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a portrait\n\n a cat \n")
        temp_path = f.name
    try:
        prompts = batch_gen.read_prompts(temp_path)
        assert prompts == ["a portrait", "a cat"]
    finally:
        os.unlink(temp_path)


def test_payload_sent_to_api(monkeypatch, tmp_path):
    """generate() must send the expected payload fields."""
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"images": ["data:image/png;base64,AAAA"]}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return FakeResp()

    monkeypatch.setattr(batch_gen.requests, "post", fake_post)
    batch_gen.generate("http://example", "a cat", "low quality",
                       20, 512, 768, -1, tmp_path)

    payload = captured["payload"]
    assert captured["url"] == "http://example/sdapi/v1/txt2img"
    assert payload["prompt"] == "a cat"
    assert payload["negative_prompt"] == "low quality"
    assert payload["steps"] == 20
    assert payload["width"] == 512
    assert payload["height"] == 768
    assert payload["seed"] == -1


def test_generate_writes_file(monkeypatch, tmp_path):
    """generate() writes the returned base64 image to disk."""
    import base64 as b64

    class FakeResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"images": ["data:image/png;base64," + b64.b64encode(b"fake").decode()]}

    monkeypatch.setattr(batch_gen.requests, "post", lambda *a, **kw: FakeResp())
    batch_gen.generate("http://example", "p", "n", 20, 512, 768, -1, tmp_path)
    files = list(Path(tmp_path).glob("*.png"))
    assert len(files) == 1
    assert files[0].read_bytes() == b"fake"


def test_retry_raises_after_max_attempts(monkeypatch, tmp_path):
    """generate_with_retry re-raises after exhausting retries."""
    calls = {"n": 0}

    def always_fail(*a, **kw):
        calls["n"] += 1
        raise batch_gen.requests.exceptions.ConnectionError("boom")

    monkeypatch.setattr(batch_gen.requests, "post", always_fail)
    monkeypatch.setattr(batch_gen.time, "sleep", lambda s: None)

    with pytest.raises(batch_gen.requests.exceptions.ConnectionError):
        batch_gen.generate_with_retry("http://x", "p", "n", 20, 512, 768, -1, tmp_path)
    assert calls["n"] == 3


def test_retry_succeeds_on_second_attempt(monkeypatch, tmp_path):
    """generate_with_retry succeeds if a later attempt works."""
    calls = {"n": 0}

    class FakeResp:
        def raise_for_status(self):
            pass
        def json(self):
            return {"images": ["data:image/png;base64,AAAA"]}

    def fail_then_ok(*a, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            raise batch_gen.requests.exceptions.ConnectionError("first fails")
        return FakeResp()

    monkeypatch.setattr(batch_gen.requests, "post", fail_then_ok)
    monkeypatch.setattr(batch_gen.time, "sleep", lambda s: None)
    batch_gen.generate_with_retry("http://x", "p", "n", 20, 512, 768, -1, tmp_path)
    assert calls["n"] == 2


def test_load_config(tmp_path):
    """load_config reads YAML; returns {} when path is None."""
    assert batch_gen.load_config(None) == {}

    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text("base_url: http://test\ndefaults:\n  steps: 30\n")
    cfg = batch_gen.load_config(str(cfg_file))
    assert cfg["base_url"] == "http://test"
    assert cfg["defaults"]["steps"] == 30
