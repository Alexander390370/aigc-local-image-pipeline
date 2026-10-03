#!/usr/bin/env python3
"""Dataset augmentation via img2img. Preserves spatial layout for label safety."""
import argparse
import base64
import io
from pathlib import Path
import requests
from PIL import Image


def augment(base_url, img_path, out_dir, variations, denoising, prompt_suffix):
    img = Image.open(img_path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode()

    for i in range(variations):
        payload = {
            "init_images": [img_b64],
            "prompt": prompt_suffix or "same scene, natural variation",
            "negative_prompt": "low quality, blurry, deformed",
            "denoising_strength": denoising,
            "steps": 20,
        }
        r = requests.post(f"{base_url}/sdapi/v1/img2img",
                          json=payload, timeout=300)
        r.raise_for_status()
        out = Path(out_dir) / f"{img_path.stem}_aug{i}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "wb") as f:
            f.write(base64.b64decode(
                r.json()["images"][0].split(",", 1)[-1]
            ))
        print(f"saved {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--base-url", default="http://127.0.0.1:7860")
    ap.add_argument("--variations", type=int, default=5)
    ap.add_argument("--denoising", type=float, default=0.4)
    ap.add_argument("--prompt-suffix", default="")
    args = ap.parse_args()

    for img_path in Path(args.input_dir).glob("*.png"):
        print(f"augmenting {img_path.name}")
        augment(args.base_url, img_path, args.output_dir,
                args.variations, args.denoising, args.prompt_suffix)


if __name__ == "__main__":
    main()
