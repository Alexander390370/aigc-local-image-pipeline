"""Minimal Python client for Forge's REST API."""
import base64
import requests
from pathlib import Path


class ForgeClient:
    def __init__(self, base_url="http://127.0.0.1:7860"):
        self.base_url = base_url.rstrip("/")

    def txt2img(self, prompt, negative="", steps=20, width=512, height=512,
                seed=-1, save_to=None):
        payload = {
            "prompt": prompt,
            "negative_prompt": negative,
            "steps": steps,
            "width": width,
            "height": height,
            "seed": seed,
        }
        r = requests.post(f"{self.base_url}/sdapi/v1/txt2img",
                          json=payload, timeout=300)
        r.raise_for_status()
        img_b64 = r.json()["images"][0]
        if save_to:
            Path(save_to).write_bytes(
                base64.b64decode(img_b64.split(",", 1)[-1])
            )
        return img_b64
