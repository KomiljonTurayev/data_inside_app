"""
Image generation engine using ComfyUI API.
Sends workflow prompts to a running ComfyUI server and retrieves
the generated images. Uses the DreamShaper 8 model with KSampler
settings from the project specification.

Execution mode: CPU (ComfyUI started with --cpu flag).
"""

import io
import json
import os
import time
import uuid
import logging
import urllib.request
import urllib.parse
from datetime import datetime

import websocket
from PIL import Image

import config
from app.workflow import build_comfyui_workflow

logger = logging.getLogger(__name__)

# Timeout for HTTP requests to ComfyUI (seconds)
HTTP_TIMEOUT = 30


class CoverArtGenerator:
    """Generates alternative cover art via ComfyUI API.

    Connects to a running ComfyUI server, queues workflow prompts,
    waits for completion, and retrieves the generated images.
    """

    def __init__(self):
        self.comfyui_url = config.COMFYUI_URL
        self.client_id = str(uuid.uuid4())

    def check_connection(self) -> bool:
        """Check if ComfyUI server is reachable."""
        try:
            url = f"{self.comfyui_url}/system_stats"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    logger.info("ComfyUI server is reachable at %s", self.comfyui_url)
                    return True
        except Exception as e:
            logger.warning("ComfyUI server not reachable at %s: %s", self.comfyui_url, e)
        return False

    def _queue_prompt(self, workflow: dict) -> str:
        """Send a workflow prompt to ComfyUI and return the prompt_id."""
        payload = json.dumps({
            "prompt": workflow,
            "client_id": self.client_id,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.comfyui_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            result = json.loads(resp.read())

        # Check for ComfyUI validation errors
        if "error" in result:
            error_msg = result["error"].get("message", "Unknown workflow error")
            node_errors = result.get("node_errors", {})
            if node_errors:
                details = "; ".join(
                    f"node {nid}: {errs}" for nid, errs in node_errors.items()
                )
                error_msg = f"{error_msg} ({details})"
            raise RuntimeError(f"ComfyUI rejected the workflow: {error_msg}")

        prompt_id = result["prompt_id"]
        logger.info("Queued prompt: %s", prompt_id)
        return prompt_id

    def _wait_for_completion(self, prompt_id: str, ws: websocket.WebSocket) -> None:
        """Wait for a queued prompt to finish executing via an open WebSocket."""
        logger.info("Waiting for prompt %s to complete...", prompt_id)

        try:
            while True:
                message = ws.recv()
                if isinstance(message, str):
                    data = json.loads(message)
                    msg_type = data.get("type", "")

                    if msg_type == "executing":
                        exec_data = data.get("data", {})
                        if exec_data.get("prompt_id") == prompt_id:
                            if exec_data.get("node") is None:
                                logger.info("Prompt %s execution complete.", prompt_id)
                                return

                    elif msg_type == "execution_error":
                        err_data = data.get("data", {})
                        if err_data.get("prompt_id") == prompt_id:
                            exception_type = err_data.get("exception_type", "Unknown")
                            exception_msg = err_data.get("exception_message", "")
                            raise RuntimeError(
                                f"ComfyUI execution error ({exception_type}): {exception_msg}"
                            )

                    elif msg_type == "execution_interrupted":
                        err_data = data.get("data", {})
                        if err_data.get("prompt_id") == prompt_id:
                            raise RuntimeError("ComfyUI execution was interrupted.")

                    elif msg_type == "progress":
                        prog = data.get("data", {})
                        value = prog.get("value", 0)
                        max_val = prog.get("max", 0)
                        if max_val > 0:
                            logger.info("Progress: %d/%d", value, max_val)
        finally:
            ws.close()

    def _get_images(self, prompt_id: str) -> list[Image.Image]:
        """Retrieve generated images from ComfyUI history."""
        url = f"{self.comfyui_url}/history/{prompt_id}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            history = json.loads(resp.read())

        images = []
        prompt_history = history.get(prompt_id, {})
        outputs = prompt_history.get("outputs", {})

        if not outputs:
            raise RuntimeError(
                f"No outputs found in ComfyUI history for prompt {prompt_id}."
            )

        for node_id, node_output in outputs.items():
            if "images" not in node_output:
                continue
            for img_info in node_output["images"]:
                filename = img_info["filename"]
                subfolder = img_info.get("subfolder", "")
                img_type = img_info.get("type", "output")

                params = urllib.parse.urlencode({
                    "filename": filename,
                    "subfolder": subfolder,
                    "type": img_type,
                })
                img_url = f"{self.comfyui_url}/view?{params}"
                img_req = urllib.request.Request(img_url)
                with urllib.request.urlopen(img_req, timeout=HTTP_TIMEOUT) as img_resp:
                    img_data = img_resp.read()

                image = Image.open(io.BytesIO(img_data))
                images.append(image)

        return images

    def generate(
        self,
        positive_prompt: str,
        negative_prompt: str = "",
        seed: int | None = None,
        steps: int | None = None,
        cfg_scale: float | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> dict:
        """
        Generate an image by sending a workflow to ComfyUI.

        Returns a dict with image path, filename, and generation metadata.
        """
        # Apply defaults from KSampler config
        ks = config.KSAMPLER
        seed = seed if seed is not None else ks["seed"]
        steps = steps if steps is not None else ks["steps"]
        cfg_scale = cfg_scale if cfg_scale is not None else ks["cfg_scale"]
        width = width if width is not None else ks["width"]
        height = height if height is not None else ks["height"]

        # Build the ComfyUI workflow
        workflow = build_comfyui_workflow(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
        )

        logger.info(
            "Generating image: steps=%d, cfg=%.1f, seed=%d, size=%dx%d",
            steps, cfg_scale, seed, width, height,
        )
        start_time = time.time()

        # Connect WebSocket BEFORE queuing the prompt to avoid missing messages
        ws_url = f"ws://{config.COMFYUI_HOST}:{config.COMFYUI_PORT}/ws?clientId={self.client_id}"
        ws = websocket.WebSocket()
        ws.connect(ws_url)

        # Queue the prompt in ComfyUI
        prompt_id = self._queue_prompt(workflow)

        # Wait for generation to complete (closes WebSocket when done)
        self._wait_for_completion(prompt_id, ws)

        # Retrieve the generated images
        images = self._get_images(prompt_id)
        if not images:
            raise RuntimeError("ComfyUI returned no images for the prompt.")

        elapsed = time.time() - start_time
        image = images[0]

        # Save the image
        os.makedirs(config.GENERATED_IMAGES_DIR, exist_ok=True)
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cover_{timestamp}_{uuid.uuid4().hex[:8]}.png"

        # Save to static dir (for web serving)
        web_path = os.path.join(config.GENERATED_IMAGES_DIR, filename)
        image.save(web_path)

        # Also save to outputs dir (for export)
        output_path = os.path.join(config.OUTPUT_DIR, filename)
        image.save(output_path)

        logger.info("Image generated in %.1f seconds: %s", elapsed, filename)

        return {
            "filename": filename,
            "web_path": f"/static/images/generated/{filename}",
            "output_path": output_path,
            "seed": seed,
            "steps": steps,
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "generation_time": round(elapsed, 2),
            "timestamp": timestamp,
        }

    def generate_preset(self, cover_type: str) -> dict:
        """Generate a cover using one of the preset prompt configurations."""
        if cover_type not in config.DEFAULT_PROMPTS:
            raise ValueError(
                f"Unknown cover type '{cover_type}'. "
                f"Choose from: {list(config.DEFAULT_PROMPTS.keys())}"
            )

        preset = config.DEFAULT_PROMPTS[cover_type]
        result = self.generate(
            positive_prompt=preset["positive"],
            negative_prompt=preset["negative"],
        )
        result["cover_type"] = cover_type
        result["preset_name"] = preset["name"]
        return result
