"""
Configuration for the Alternative Cover Art Generation project.
All project constants and KSampler settings are defined here.
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- ComfyUI Configuration ---
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", 8188))
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

# --- Model Configuration ---
CHECKPOINT_NAME = "dreamshaper_8.safetensors"

# --- KSampler Settings (from project spec) ---
KSAMPLER = {
    "seed": 8845206238271,
    "steps": 20,
    "cfg_scale": 8,
    "sampler": "euler",
    "scheduler": "simple",
    "width": 512,
    "height": 512,
}

# --- Output Configuration ---
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
GENERATED_IMAGES_DIR = os.path.join(BASE_DIR, "app", "static", "images", "generated")

# --- Flask Configuration ---
SECRET_KEY = os.environ.get("SECRET_KEY", "capstone-cover-art-2025")
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
HOST = os.environ.get("FLASK_HOST", "localhost")
PORT = int(os.environ.get("FLASK_PORT", 8080))

# --- Default Prompts ---
DEFAULT_PROMPTS = {
    "book": {
        "name": "Crime and Punishment",
        "author": "Fyodor Dostoevsky",
        "positive": (
            "book cover design, title 'CRIME AND PUNISHMENT', "
            "dark city background, dramatic lighting, professional typography"
        ),
        "negative": "blurry, low quality, deformed, misspelled text",
    },
    "movie": {
        "name": "Interstellar",
        "positive": (
            "movie poster design, title 'INTERSTELLAR', "
            "cinematic sci-fi design, deep space background, wormhole, "
            "astronaut silhouette, dramatic lighting, professional typography"
        ),
        "negative": "blurry, low quality, deformed, misspelled text, cartoon",
    },
    "music": {
        "name": "Abstract Electronic Album",
        "positive": (
            "music album cover art, abstract electronic ambient vinyl artwork, "
            "vibrant colors, geometric shapes, futuristic design, "
            "professional graphic design, high contrast"
        ),
        "negative": "blurry, low quality, deformed, text, words, letters",
    },
}

# --- Workflow Export ---
WORKFLOW_DIR = os.path.join(BASE_DIR, "workflows")
