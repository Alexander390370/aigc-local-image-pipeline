# AIGC Local Image Pipeline

![Tests](https://github.com/Alexander390370/aigc-local-image-pipeline/actions/workflows/test.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Platform: WSL2](https://img.shields.io/badge/Platform-WSL2-blue)
![Python 3.10](https://img.shields.io/badge/Python-3.10-blue)

> **Status**: Working pipeline, tested on RTX 4060 Laptop 8GB under WSL2. This repository implements application-layer scripts on top of Stable Diffusion WebUI Forge. For base environment installation steps, refer to [sd-forge-8gb-vram-setup](https://github.com/Alexander390370/sd-forge-8gb-vram-setup). **Not polished production-grade code — expect manual adjustments for heavy-duty workloads.**

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Quick Start](#quick-start)
- [Scripts](#scripts)
- [Agent Integration](#agent-integration)
- [Model Selection](#model-selection)
- [Known Limitations](#known-limitations)
- [Related Work](#related-work)

## Overview

Most Stable Diffusion setups stop at "it generates images". This repo takes the next step: turning a local Forge instance into an **automatable system** for two real workflows:

1. **Batch generation** — read a prompt list, produce N images unattended, save with deterministic filenames.
2. **Agent integration** — expose Forge's API through a minimal Python client, so other tools (Agents, schedulers, your own code) can call it programmatically.

Everything runs offline after setup. No cloud API, no per-image cost.

## Architecture

```text
                    ┌──────────────────────────┐
                    │  Stable Diffusion Forge  │
                    │  (WSL2, port 7860)       │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  Forge REST API (/docs)  │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
                    ▼                         ▼
        ┌───────────────────┐     ┌────────────────────┐
        │  Batch Generation │     │  Reusable Client   │
        │  batch_gen.py     │     │  api_client.py     │
        └───────────────────┘     └────────────────────┘
```

## Repository Structure

```text
aigc-local-image-pipeline/
├── README.md
├── LICENSE
├── .gitignore
├── requirements.txt
├── run_pipeline.sh           # One-shot: waits for Forge, then runs batch_gen
├── scripts/
│   ├── batch_gen.py          # Batch generation from a prompt list
│   ├── api_client.py         # Reusable Python client for Forge API
│   └── model_downloader.sh   # Download community models from hf-mirror
├── prompts/
│   └── examples.txt          # Example prompt list (one per line)
├── tests/
│   └── test_batch_gen.py     # Unit tests (run via pytest)
└── config/
    └── config.example.yaml   # Base URL, default params
```

## Quick Start

### 1. Start Forge with API enabled

```bash
cd ~/stable-diffusion-webui-forge
conda activate sd-forge
# --disable-safe-unpickle: disables safety check for local trusted models.
# Do not use on public networks; only load model files from sources you trust.
python launch.py --api --listen --medvram --disable-safe-unpickle --port 7860
```

Wait until the terminal prints:
```
add APIs: 0.9s
```

Confirm the API is up:
```bash
curl http://127.0.0.1:7860/sdapi/v1/sd-models
```
Should return a JSON list of models. If empty or 502, Forge is not fully started yet.

### 2. Install dependencies

```bash
cd ~/aigc-local-image-pipeline
conda activate sd-forge
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Core dependencies: `requests`, `pyyaml`, `tqdm`.

### 3. Batch generate

```bash
python scripts/batch_gen.py \
  --prompts prompts/examples.txt \
  --output /mnt/c/Users/<YourName>/Desktop/aigc-output
```

On Windows + WSL2, `/mnt/c/Users/<YourName>/Desktop/...` maps directly to the Windows desktop.

> 💡 **WSL filesystem note**: writing to `/mnt/c/...` is convenient but slower than the native WSL filesystem. For high-throughput batches, write to `~/generated/` first and copy files to Windows afterward.

### 4. Run tests

```bash
pytest
```

Expected: `2 passed`. The same test suite runs automatically on every push via GitHub Actions.

## Windows One-Click Launchers (Optional)

Two `.bat` files for double-click convenience on Windows.

> These assume WSL2 with a `Ubuntu` distribution and Miniconda installed at `~/miniconda3`. Adjust the distribution name or paths if your setup differs.

**`1-start-forge.bat`**
```bat
@echo off
title Forge Server
wsl.exe -d Ubuntu -e bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate sd-forge && cd ~/stable-diffusion-webui-forge && python launch.py --api --listen --medvram --disable-safe-unpickle --port 7860"
pause
```

**`2-batch-generate.bat`**
```bat
@echo off
title AIGC Batch Generation
wsl.exe -d Ubuntu -e bash -c "source ~/miniconda3/etc/profile.d/conda.sh && conda activate sd-forge && ~/aigc-local-image-pipeline/run_pipeline.sh"
pause
```

The `source .../conda.sh &&` prefix is required — `wsl.exe -e bash -c` runs a non-interactive shell that does not read `.bashrc`, so `conda activate` would otherwise fail.

## Scripts

### `scripts/batch_gen.py`

Reads a prompt list (one per line), calls Forge's `/sdapi/v1/txt2img`, saves images with deterministic filenames.

| Argument | Default | Notes |
|----------|---------|-------|
| `--prompts` | required | Path to a text file, one prompt per line |
| `--output` | required | Output directory (WSL path or `/mnt/c/...`) |
| `--base-url` | `http://127.0.0.1:7860` | Forge API endpoint |
| `--negative` | `low quality, blurry, deformed` | Global negative prompt |
| `--steps` | `20` | Sampling steps |
| `--width` / `--height` | `512` / `768` | Image dimensions |
| `--seed` | `-1` | `-1` = random |

### `scripts/api_client.py`

Minimal Python wrapper around Forge's REST API. Import into your own code to script generation:

```python
from scripts.api_client import ForgeClient

client = ForgeClient(base_url="http://127.0.0.1:7860")
client.txt2img(prompt="a cat", steps=20, width=512, height=512, save_to="cat.png")
```

### `scripts/model_downloader.sh`

Downloads community models from `hf-mirror.com` via `aria2c`.

> Requires `aria2c` installed inside WSL:
> ```bash
> sudo apt update && sudo apt install aria2 -y
> ```

## Prompt List Format

`prompts/examples.txt` is plain text, one prompt per line. Empty lines are skipped.

```text
a portrait of a woman, natural lighting, photorealistic
a cat sitting on a windowsill, morning light, soft focus
a cyberpunk street scene, neon reflections, cinematic
```

Each line becomes one image. To use your own list, edit this file (or point `--prompts` at any text file).

## Agent Integration

The Forge API can be called as a tool by any Agent that supports custom HTTP tools.

Example: register Forge as a tool in Hermes Agent's `config.yaml`:

```yaml
tools:
  - name: generate_image
    type: http
    base_url: http://127.0.0.1:7860
    endpoint: /sdapi/v1/txt2img
    method: POST
    params:
      prompt: "{prompt}"
      steps: 20
      width: 512
      height: 512
```

If you don't use Hermes, you can call the same endpoint directly from Python:

```python
import requests, base64

r = requests.post("http://127.0.0.1:7860/sdapi/v1/txt2img", json={
    "prompt": "a cat on a windowsill",
    "steps": 20, "width": 512, "height": 512,
})
img_b64 = r.json()["images"][0]
with open("cat.png", "wb") as f:
    f.write(base64.b64decode(img_b64.split(",", 1)[-1]))
```

Useful for:

- Auto-generating illustrations for reports
- Producing mock product images for e-commerce drafts
- Generating assets for local Agent demos

## Model Selection

For 8GB VRAM, stick with SD 1.5 models for batch generation:

| Model | Use Case | Size |
|-------|----------|------|
| Realistic Vision V5.1 | Photorealistic portraits | ~4.2GB |
| DreamShaper 8 | Stylized / painterly | ~4.2GB |
| AnythingV5 | Anime / illustration | ~4.2GB |

SDXL models (6.5–7GB) work for single-image generation but will OOM during batches.

## Known Limitations

- **Batch size is 1.** The Forge API processes one image per request. Higher concurrency will trigger VRAM OOM on 8GB GPUs.
- **No ControlNet integration yet.** ControlNet would require a Forge extension and additional API parameters.
- **Prompt input is plain-text only.** CSV input with per-prompt overrides is not implemented; can be extended as required.
- **Forge API version sensitivity.** The `/sdapi/v1/` endpoints are stable across Forge releases, but extension APIs (ControlNet, ADetailer) may change between versions.
- **Not production-grade.** Single-card edge pipeline, not a scaled cluster. Expect manual tuning for heavy workloads.

**Possible future extensions**: CSV prompt input with per-line overrides, ControlNet support, progress persistence for resumable batches.

## Related Work

The same 8GB RTX 4060, running different workloads:

- **[sd-forge-8gb-vram-setup](https://github.com/Alexander390370/sd-forge-8gb-vram-setup)** — setup and installation log for running Forge on 8GB VRAM. **Start here if you don't have Forge running yet.**
- **[Bonsai-27B-8GB-VRAM-Setup](https://github.com/Alexander390370/Bonsai-27B-8GB-VRAM-Setup)** — the same 8GB card, running an LLM instead of a diffusion model.
- **[esp32-edge-ai-security](https://github.com/Alexander390370/esp32-edge-ai-security)** — edge-side AI, the hardware counterpart to this software pipeline.
- **[esp32-pwm-fan-controller](https://github.com/Alexander390370/esp32-pwm-fan-controller)** — low-level firmware project on the same hardware stack.

## License

Distributed under the MIT License. See [LICENSE](./LICENSE) for details.
