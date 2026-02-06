"""
Flask routes for the Cover Art Generator web application.
"""

import logging
import os
import threading

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)
from werkzeug.utils import secure_filename

import config
from app.generator import CoverArtGenerator
from app.workflow import build_comfyui_workflow, export_workflow

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

# Global generator instance (lazy singleton)
_generator: CoverArtGenerator | None = None
_generator_lock = threading.Lock()
_generation_status = {"busy": False, "message": ""}


def get_generator() -> CoverArtGenerator:
    """Get or create the singleton generator instance."""
    global _generator
    with _generator_lock:
        if _generator is None:
            _generator = CoverArtGenerator()
    return _generator


@main.route("/")
def index():
    """Main page with cover art generation UI."""
    return render_template(
        "index.html",
        presets=config.DEFAULT_PROMPTS,
        ksampler=config.KSAMPLER,
    )


@main.route("/gallery")
def gallery():
    """Gallery page showing all generated images."""
    return render_template("gallery.html", images=_list_images())


def _list_images() -> list[dict]:
    """List generated images from the static directory."""
    images = []
    gen_dir = config.GENERATED_IMAGES_DIR
    if os.path.exists(gen_dir):
        for fname in sorted(os.listdir(gen_dir), reverse=True):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                images.append({
                    "filename": fname,
                    "path": f"/static/images/generated/{fname}",
                })
    return images


@main.route("/api/generate", methods=["POST"])
def api_generate():
    """API endpoint to generate a cover art image via ComfyUI."""
    global _generation_status

    if _generation_status["busy"]:
        return jsonify({"error": "Generation already in progress. Please wait."}), 429

    data = request.get_json(force=True)
    if data is None:
        return jsonify({"error": "Invalid JSON in request body."}), 400

    cover_type = data.get("cover_type")
    positive_prompt = data.get("positive_prompt", "")
    negative_prompt = data.get("negative_prompt", "")

    # Optional overrides with validation
    try:
        seed = int(data["seed"]) if data.get("seed") is not None else None
        steps = int(data["steps"]) if data.get("steps") is not None else None
        cfg_scale = float(data["cfg_scale"]) if data.get("cfg_scale") is not None else None
        width = int(data["width"]) if data.get("width") is not None else None
        height = int(data["height"]) if data.get("height") is not None else None
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric parameter: {e}"}), 400

    _generation_status = {"busy": True, "message": "Connecting to ComfyUI..."}

    try:
        gen = get_generator()

        if not gen.check_connection():
            _generation_status = {"busy": False, "message": ""}
            return jsonify({
                "error": (
                    "ComfyUI is not running. "
                    "Start it with: cd ComfyUI && python main.py --cpu"
                )
            }), 503

        _generation_status["message"] = "Generating image..."

        if cover_type and cover_type in config.DEFAULT_PROMPTS:
            # Use preset but allow overrides
            preset = config.DEFAULT_PROMPTS[cover_type]
            pos = positive_prompt if positive_prompt else preset["positive"]
            neg = negative_prompt if negative_prompt else preset["negative"]
        else:
            pos = positive_prompt
            neg = negative_prompt

        if not pos:
            _generation_status = {"busy": False, "message": ""}
            return jsonify({"error": "Positive prompt is required."}), 400

        result = gen.generate(
            positive_prompt=pos,
            negative_prompt=neg,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
        )
        result["cover_type"] = cover_type or "custom"

        _generation_status = {"busy": False, "message": "Done"}
        return jsonify(result)

    except Exception as e:
        logger.exception("Generation failed")
        _generation_status = {"busy": False, "message": ""}
        return jsonify({"error": str(e)}), 500


@main.route("/api/status")
def api_status():
    """Check generation status."""
    return jsonify({
        "busy": _generation_status["busy"],
        "message": _generation_status["message"],
    })


@main.route("/api/presets")
def api_presets():
    """Return available preset configurations."""
    return jsonify(config.DEFAULT_PROMPTS)


@main.route("/api/workflow", methods=["POST"])
def api_workflow():
    """Generate and return a ComfyUI workflow JSON."""
    data = request.get_json(force=True)
    if data is None:
        return jsonify({"error": "Invalid JSON in request body."}), 400

    positive_prompt = data.get("positive_prompt", "")
    negative_prompt = data.get("negative_prompt", "")

    if not positive_prompt:
        return jsonify({"error": "Positive prompt is required."}), 400

    workflow = build_comfyui_workflow(
        positive_prompt=positive_prompt,
        negative_prompt=negative_prompt,
        seed=data.get("seed"),
        steps=data.get("steps"),
        cfg_scale=data.get("cfg_scale"),
        width=data.get("width"),
        height=data.get("height"),
    )
    return jsonify(workflow)


@main.route("/api/workflow/export", methods=["POST"])
def api_workflow_export():
    """Export a ComfyUI workflow JSON file to disk."""
    data = request.get_json(force=True)
    if data is None:
        return jsonify({"error": "Invalid JSON in request body."}), 400

    positive_prompt = data.get("positive_prompt", "")
    negative_prompt = data.get("negative_prompt", "")
    raw_filename = data.get("filename", "workflow.json")

    if not positive_prompt:
        return jsonify({"error": "Positive prompt is required."}), 400

    # Sanitize filename to prevent path traversal
    filename = secure_filename(raw_filename)
    if not filename:
        filename = "workflow.json"

    try:
        path = export_workflow(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            filename=filename,
        )
        return jsonify({"path": path, "filename": filename})
    except Exception as e:
        logger.exception("Workflow export failed")
        return jsonify({"error": str(e)}), 500


@main.route("/api/gallery")
def api_gallery():
    """Return list of generated images."""
    return jsonify(_list_images())
