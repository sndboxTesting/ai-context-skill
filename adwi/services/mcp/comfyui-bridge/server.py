"""
ComfyUI MCP Bridge Server
Connects to ComfyUI REST API (localhost:8188) for image generation.
ComfyUI must be running separately. Start it with: /generate-image or manually.
"""
import json
import urllib.request
import urllib.error
import uuid
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit("Run with: uv run --with mcp python3 server.py")

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR  = Path.home() / "SuneelWorkSpace" / "notes" / "generated-images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("comfyui")


def _comfy_available() -> bool:
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


@mcp.tool()
def generate_image(prompt: str, negative_prompt: str = "", steps: int = 20, width: int = 512, height: int = 512) -> str:
    """Generate an image using ComfyUI with a text prompt."""
    if not _comfy_available():
        return (
            "ComfyUI is not running. Start it first:\n"
            "  cd ~/ComfyUI && python3 main.py --listen 0.0.0.0\n"
            "Or download ComfyUI from https://github.com/comfyanonymous/ComfyUI"
        )

    # Minimal text-to-image workflow using default SD model
    workflow = {
        "3": {"class_type": "KSampler", "inputs": {
            "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0],
            "latent_image": ["5", 0], "seed": int(uuid.uuid4().int % 2**31),
            "steps": steps, "cfg": 7.0, "sampler_name": "euler",
            "scheduler": "normal", "denoise": 1.0
        }},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "v1-5-pruned-emaonly.ckpt"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["4", 1]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative_prompt or "bad quality, blurry", "clip": ["4", 1]}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"images": ["8", 0], "filename_prefix": "adwi_gen"}},
    }

    try:
        data = json.dumps({"prompt": workflow}).encode()
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            result = json.loads(r.read())
        prompt_id = result.get("prompt_id", "")
        return f"Image generation queued (prompt_id: {prompt_id}). Check ComfyUI at {COMFYUI_URL} or outputs in ~/ComfyUI/output/"
    except Exception as e:
        return f"ComfyUI error: {e}"


@mcp.tool()
def comfyui_status() -> str:
    """Check if ComfyUI is running and get system stats."""
    if not _comfy_available():
        return "ComfyUI is offline. Start it: cd ~/ComfyUI && python3 main.py"
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=5) as r:
            stats = json.loads(r.read())
        gpu = stats.get("system", {})
        return f"ComfyUI online ✓\n  RAM: {gpu.get('ram_free',0)//1024//1024}MB free\n  VRAM: {gpu.get('vram_free',0)//1024//1024}MB free"
    except Exception as e:
        return f"ComfyUI status error: {e}"


@mcp.tool()
def list_models() -> str:
    """List available SD models in ComfyUI."""
    if not _comfy_available():
        return "ComfyUI is offline"
    try:
        with urllib.request.urlopen(f"{COMFYUI_URL}/object_info", timeout=5) as r:
            info = json.loads(r.read())
        models = info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
        if models:
            return "Available models:\n" + "\n".join(f"  • {m}" for m in models)
        return "No models found in ComfyUI. Download a model to ~/ComfyUI/models/checkpoints/"
    except Exception as e:
        return f"Error listing models: {e}"


if __name__ == "__main__":
    mcp.run()
