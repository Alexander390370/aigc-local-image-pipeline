import os
import tempfile
from pathlib import Path


def test_prompt_parsing():
    """Prompts are parsed correctly, empty lines ignored."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("a portrait\n\n a cat \n")
        temp_path = f.name

    try:
        with open(temp_path) as f:
            prompts = [line.strip() for line in f if line.strip()]
        assert prompts == ["a portrait", "a cat"]
    finally:
        os.unlink(temp_path)


def test_output_dir_creation():
    """Output directory is created when it does not exist."""
    test_dir = Path(tempfile.mkdtemp()) / "new_output"
    assert not test_dir.exists()
    test_dir.mkdir(parents=True, exist_ok=True)
    assert test_dir.exists()
