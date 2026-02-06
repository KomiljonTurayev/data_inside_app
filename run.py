"""
Entry point for the Alternative Cover Art Generator web application.

Requires a running ComfyUI server (started separately with --cpu flag).

Usage:
    python run.py                    # Start web server
    python run.py --export-workflows # Export all preset ComfyUI workflows and exit
"""

import argparse
import logging
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from app import create_app


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()
    logger = logging.getLogger("run")

    parser = argparse.ArgumentParser(description="Alternative Cover Art Generator")
    parser.add_argument(
        "--export-workflows", action="store_true",
        help="Export all preset ComfyUI workflow JSONs and exit",
    )
    parser.add_argument("--host", default=config.HOST, help="Server host")
    parser.add_argument("--port", type=int, default=config.PORT, help="Server port")
    parser.add_argument("--debug", action="store_true", default=config.DEBUG)
    args = parser.parse_args()

    # Export workflows mode
    if args.export_workflows:
        from app.workflow import export_all_presets
        paths = export_all_presets()
        for p in paths:
            logger.info("Exported: %s", p)
        logger.info("All workflows exported to %s", config.WORKFLOW_DIR)
        return

    # Create Flask app
    app = create_app()

    # Check ComfyUI connection on startup
    from app.generator import CoverArtGenerator
    gen = CoverArtGenerator()
    if gen.check_connection():
        logger.info("ComfyUI is running at %s", config.COMFYUI_URL)
    else:
        logger.warning(
            "ComfyUI is NOT reachable at %s. "
            "Start it with: cd ComfyUI && python main.py --cpu",
            config.COMFYUI_URL,
        )

    logger.info("Starting server at http://%s:%d", args.host, args.port)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
