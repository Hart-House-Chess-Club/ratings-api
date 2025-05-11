#!/usr/bin/env python
# filepath: /Users/victorzheng/Documents/fide-api/fide-api/reset_mongodb.py
"""
Reset MongoDB collections for FIDE API.
This script drops all collections and recreates the indexes.
Use it when you encounter database issues like duplicate key errors.
"""

from src.scraper.ratinglists.db import reset_collections
import sys

if __name__ == "__main__":
    print("Resetting MongoDB collections...")
    if reset_collections():
        print("Reset completed successfully. You can now run the initialization script.")
        sys.exit(0)
    else:
        print("Failed to reset collections. Check the error messages above.")
        sys.exit(1)
