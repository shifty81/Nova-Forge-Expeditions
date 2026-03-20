"""
NovaForge Dev AI — Stable Diffusion Interface
Stub integration layer for local Stable Diffusion / AUTOMATIC1111 WebUI.
"""
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class StableDiffusionInterface:
    """Stub interface to locally-running Stable Diffusion WebUI."""

    def __init__(self, api_url="http://127.0.0.1:7860", model="v1-5-pruned",
                 output_dir="ai_dev/workspace/sd_output"):
        self.api_url = api_url
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.api_url}/sdapi/v1/samplers", timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def txt2img(self, prompt, negative_prompt="", steps=20, width=512, height=512, seed=-1):
        out_path = str(self.output_dir / f"txt2img_{abs(seed)}.png")
        print(f"[SD] txt2img prompt={prompt!r} {width}x{height} -> {out_path} (stub)")
        return out_path

    def img2img(self, prompt, input_path, denoising_strength=0.75):
        input_stem = Path(input_path).stem
        out_path = str(self.output_dir / f"img2img_{input_stem}_out.png")
        print(f"[SD] img2img input={input_path!r} strength={denoising_strength} -> {out_path} (stub)")
        return out_path

    def inpaint(self, prompt, input_path, mask_path):
        input_stem = Path(input_path).stem
        out_path = str(self.output_dir / f"inpaint_{input_stem}_out.png")
        print(f"[SD] inpaint input={input_path!r} mask={mask_path!r} -> {out_path} (stub)")
        return out_path

    def controlnet(self, prompt, input_path, control_type="canny"):
        input_stem = Path(input_path).stem
        out_path = str(self.output_dir / f"controlnet_{control_type}_{input_stem}.png")
        print(f"[SD] controlnet type={control_type!r} -> {out_path} (stub)")
        return out_path
