#!/usr/bin/env python3
"""
PetLog main application entry point.
Starts the FastAPI server with uvicorn.
"""

import logging
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Start the PetLog FastAPI application."""
    logger.info("🐾 Starting PetLog application...")

    # Load configuration from environment variables
    host = os.getenv("SERVER_HOST", "0.0.0.0")  # Default to all interfaces
    port = int(os.getenv("SERVER_PORT", "8000"))  # Default to port 8000
    reload = os.getenv("RELOAD", "true").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info").lower()

    logger.info(f"🌐 Server will start on {host}:{port}")

    # Ensure log file directory exists
    log_dir = Path.cwd()
    log_dir.mkdir(exist_ok=True)

    try:
        # Start uvicorn server
        uvicorn.run(
            "src.api:app",
            host=host,
            port=port,
            reload=reload,
            log_level=log_level,
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("👋 PetLog application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start PetLog application: {e}")
        raise


if __name__ == "__main__":
    main()
