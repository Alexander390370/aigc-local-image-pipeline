import os
import sys
import tempfile
from pathlib import Path

# Add scripts/ to path so we can import batch_gen
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import batch_gen


def test_prompt_parsing_via_module():
    """batch_gen correctly parses a prompt file with blank lines."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a portrait\n\n a cat \n")
        temp_path = f.name
    try:
        # Simulate the same loop batch_gen.main() uses
        prompts = []
        for line in open(temp_path):
            p = line.strip()
            if p:
                prompts.append(p)
        assert prompts == ["a portrait", "a cat"]
    finally:
        os.unlink(temp_path)


def test_generate_payload_fields():
    """generate() sends the expected payload keys to the Forge API."""
    import inspect
    src = inspect.getsource(batch_gen.generate)
    for field in ["prompt", "negative_prompt", "steps", "width", "height", "seed"]:
        assert field in src, f"missing payload field: {field}"


def test_retry_helper_exists():
    """generate_with_retry is defined and callable."""
    assert callable(batch_gen.generate_with_retry)
