"""
IntelliVault ~ Backend Application Entry Point
Starts the Flask development server on the configured host and port.
"""

import os
import sys

# Ensure repository root is in python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app
from backend.app.utils.logger import logger

app = create_app()

if __name__ == "__main__":
    host = app.config.get("HOST", "127.0.0.1")
    port = app.config.get("PORT", 5000)
    debug = app.config.get("DEBUG", True)

    logger.info(f"Starting IntelliVault Server at http://{host}:{port} (Debug: {debug})")
    app.run(host=host, port=port, debug=debug)
