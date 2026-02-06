"""
ComfyUI workflow JSON generator.
Creates a reproducible ComfyUI workflow matching the project specification.
"""

import json
import os

import config


def build_comfyui_workflow(
    positive_prompt: str,
    negative_prompt: str = "",
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
    width: int | None = None,
    height: int | None = None,
) -> dict:
    """Build a ComfyUI-compatible workflow JSON dict."""
    ks = config.KSAMPLER
    seed = seed if seed is not None else ks["seed"]
    steps = steps if steps is not None else ks["steps"]
    cfg_scale = cfg_scale if cfg_scale is not None else ks["cfg_scale"]
    width = width if width is not None else ks["width"]
    height = height if height is not None else ks["height"]

    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg_scale,
                "sampler_name": ks["sampler"],
                "scheduler": ks["scheduler"],
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": config.CHECKPOINT_NAME,
            },
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1,
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_prompt,
                "clip": ["4", 1],
            },
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["4", 1],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            },
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "CoverArt",
                "images": ["8", 0],
            },
        },
    }
    return workflow


def export_workflow(
    positive_prompt: str,
    negative_prompt: str = "",
    filename: str = "workflow.json",
    **kwargs,
) -> str:
    """Export a ComfyUI workflow JSON to the workflows directory."""
    os.makedirs(config.WORKFLOW_DIR, exist_ok=True)
    workflow = build_comfyui_workflow(positive_prompt, negative_prompt, **kwargs)
    filepath = os.path.join(config.WORKFLOW_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(workflow, f, indent=2)
    return filepath


def export_all_presets() -> list[str]:
    """Export ComfyUI workflows for all default cover art presets."""
    paths = []
    for cover_type, preset in config.DEFAULT_PROMPTS.items():
        path = export_workflow(
            positive_prompt=preset["positive"],
            negative_prompt=preset["negative"],
            filename=f"workflow_{cover_type}.json",
        )
        paths.append(path)
    return paths
