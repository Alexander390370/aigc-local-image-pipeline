#!/usr/bin/env python3
"""Batch generate images via Forge's txt2img API."""
import argparse
import base64
import time
from pathlib import Path

import requests
import yaml
from tqdm import tqdm


def generate(base_url, prompt, negative, steps, width, height, seed, save_to):
    payload = {
        "prompt": prompt,
        "negative_prompt": negative,
        "steps": steps,
        "width": width,
        "height": height,
        "seed": seed,
    }
    r = requests.post(f"{base_url}/sdapi/v1/txt2img",
                      json=payload, timeout=300)
    r.raise_for_status()
    for i, img_b64 in enumerate(r.json()["images"]):
        out = Path(save_to) / f"{int(time.time() * 1000)}_{seed}_{i}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as f:
            f.write(base64.b64decode(img_b64.split(",", 1)[-1]))
        print(f"saved {out}")


def generate_with_retry(base_url, prompt, negative, steps, width, height,
                        seed, save_to, max_retries=3):
    for attempt in range(max_retries):
        try:
            return generate(base_url, prompt, negative, steps, width, height,
                            seed, save_to)
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            print(f"Retry {attempt + 1}/{max_retries} in {wait}s: {e}")
            time.sleep(wait)


def load_config(config_path):
    """Load defaults from a YAML config. Returns {} if the path is None."""
    if not config_path:
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def read_prompts(prompt_file):
    """Read one prompt per line, skipping blank lines."""
    with open(prompt_file) as f:
        return [line.strip() for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default=None,
                    help="Optional YAML config file for defaults")
    ap.add_argument("--base-url", default=None)
    ap.add_argument("--negative", default=None)
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--height", type=int, default=None)
    ap.add_argument("--seed", type=int, default=-1)
    args = ap.parse_args()

    cfg = load_config(args.config)
    defaults = cfg.get("defaults", {})
    base_url = args.base_url or cfg.get("base_url") or "http://127.0.0.1:7860"
    negative = args.negative or "low quality, blurry, deformed"
    steps  = args.steps  if args.steps  is not None else defaults.get("steps", 20)
    width  = args.width  if args.width  is not None else defaults.get("width", 512)
    height = args.height if args.height is not None else defaults.get("height", 768)

    prompts = read_prompts(args.prompts)
    for prompt in tqdm(prompts, desc="Generating"):
        print(f"generating: {prompt}")
        generate_with_retry(base_url, prompt, negative,
                            steps, width, height,
                            args.seed, args.output)


if __name__ == "__main__":
    main()
