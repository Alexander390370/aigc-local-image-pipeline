#!/usr/bin/env python3
"""Batch generate images via Forge's txt2img API."""
import argparse
import base64
import sys
import time
from pathlib import Path
import requests


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
        out = Path(save_to) / f"{int(time.time())}_{seed}_{i}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as f:
            f.write(base64.b64decode(img_b64.split(",", 1)[-1]))
        print(f"saved {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:7860")
    ap.add_argument("--negative", default="low quality, blurry, deformed")
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--width", type=int, default=512)
    ap.add_argument("--height", type=int, default=768)
    ap.add_argument("--seed", type=int, default=-1)
    args = ap.parse_args()

    for line in open(args.prompts):
        prompt = line.strip()
        if not prompt:
            continue
        print(f"generating: {prompt}")
        generate(args.base_url, prompt, args.negative,
                 args.steps, args.width, args.height,
                 args.seed, args.output)


if __name__ == "__main__":
    main()
