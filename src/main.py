#!/usr/bin/env python3
"""
PetLog main application entry point.
Starts the FastAPI server with uvicorn.
"""

import uvicorn
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Start the PetLog FastAPI application."""
    logger.info("🐾 Starting PetLog application...")
    
    # Ensure log file directory exists
    log_dir = Path.cwd()
    log_dir.mkdir(exist_ok=True)
    
    try:
        # Start uvicorn server
        uvicorn.run(
            "src.api:app",
            host="192.168.1.74",  # Listen on all interfaces
            port=8000,
            reload=True,     # Auto-reload on code changes
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("👋 PetLog application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to start PetLog application: {e}")
        raise

if __name__ == "__main__":
    main()
