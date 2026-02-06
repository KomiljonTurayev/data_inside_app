"""
Flask application factory for the Alternative Cover Art Generator.
"""

from flask import Flask
import config


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.config["SECRET_KEY"] = config.SECRET_KEY

    from app.routes import main
    app.register_blueprint(main)

    return app
