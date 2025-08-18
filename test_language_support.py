#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import os
import sys
import locale
from dotenv import load_dotenv
from pilot.language.translation_handler import get_lang_text
from pilot.language.prompt_language import get_prompt_template
from pilot.configs.config import Config

# Set locale to UTF-8
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("test_language_support")

# Load environment variables
load_dotenv()

def test_ui_translations():
    """Test UI translations for different languages"""
    languages = ["en", "pt", "zh"]
    test_keys = [
        "sql_query_used", 
        "database_smart_assistant",
        "send",
        "regenerate"
    ]
    
    print("\n=== Testing UI Translations ===")
    for lang in languages:
        print(f"\nLanguage: {lang}")
        for key in test_keys:
            # Temporarily override the language
            os.environ["LANGUAGE"] = lang
            # Reload config to pick up the new language
            config = Config()
            # Get translation
            translation = get_lang_text(key)
            print(f"  {key}: {translation}")

def test_prompt_translations():
    """Test prompt template translations for different languages"""
    languages = ["en", "pt"]
    test_keys = [
        "sql_expert_role",
        "sql_limit_results",
        "scene_define"
    ]
    
    print("\n=== Testing Prompt Template Translations ===")
    for lang in languages:
        print(f"\nLanguage: {lang}")
        for key in test_keys:
            # Temporarily override the language
            os.environ["LANGUAGE"] = lang
            # Get translation
            translation = get_prompt_template(key, lang)
            # Show first 60 characters to avoid cluttering the output
            print(f"  {key}: {translation[:60]}...")

if __name__ == "__main__":
    # Save original language setting
    original_language = os.environ.get("LANGUAGE", "en")
    
    try:
        # Run tests
        test_ui_translations()
        test_prompt_translations()
    finally:
        # Restore original language setting
        os.environ["LANGUAGE"] = original_language
        print(f"\nRestored language to: {original_language}")
