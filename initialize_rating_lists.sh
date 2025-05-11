#!/bin/sh
# This script initializes both FIDE and CFC rating lists

echo "Starting rating lists initialization..."

# Make sure we're in the project directory
cd "$(dirname "$0")"

# Create a Python script to run the initialization
cat > ./init_ratings.py << 'EOL'
import os
import logging
from src.scraper.ratinglists.parsers import parse_fide_rating_list, parse_cfc_rating_list
from src.scraper.ratinglists.updater import update_cfc_rating_list, update_fide_rating_list
from src.scraper.ratinglists.db import reset_collections

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rating_list_init')

logger.info("Starting rating list initialization...")

# First reset collections to ensure clean state
logger.info("Resetting database collections...")
reset_result = reset_collections()
logger.info(f"Reset result: {'Successful' if reset_result else 'Failed'}")

# Step 1: Try to download the latest rating lists
logger.info("Downloading latest rating lists...")
# fide_download = update_fide_rating_list()
cfc_download = update_cfc_rating_list()

# logger.info(f"FIDE download: {'Successful' if fide_download else 'Failed'}")
logger.info(f"CFC download: {'Successful' if cfc_download else 'Failed'}")

# Step 2: Parse the rating lists
# logger.info("Parsing rating lists...")
# fide_result = parse_fide_rating_list()
# cfc_result = parse_cfc_rating_list()

# logger.info(f"FIDE parsing: {'Successful' if fide_result else 'Failed'}")
# logger.info(f"CFC parsing: {'Successful' if cfc_result else 'Failed'}")

# If either failed, try full update procedure
# if not fide_result or not cfc_result:
#     logger.warning("Some parsing failed. Attempting full update procedure...")
#     update_results = update_all_rating_lists()
#     logger.info(f"Update results: {update_results}")

logger.info("Rating list initialization completed!")
EOL

# Run the initialization script
python init_ratings.py

# Clean up
rm ./init_ratings.py

echo "Rating list initialization complete!"