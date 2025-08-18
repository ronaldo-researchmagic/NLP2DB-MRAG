#!/usr/bin/env python3
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from pilot.web.app import main as start_webserver
from pilot.utils import build_logger

logger = build_logger("main", "main.log")

def main():
    """Main entry point for DB-GPT TELA Edition."""
    logger.info("Starting DB-GPT TELA Edition with NiceGUI...")
    start_webserver()

if __name__ in {'__main__', '__mp_main__'}:
    main()
