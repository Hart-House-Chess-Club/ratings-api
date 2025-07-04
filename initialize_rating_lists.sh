#!/bin/sh
# This script initializes both FIDE and CFC rating lists
# to run this script, make sure you have Python 3 and pip installed
# and that you have the required packages installed in your Python environment
# Usage: ./initialize_rating_lists.sh [--no-download]

# Parse command line arguments
DOWNLOAD_LATEST=True

while [[ $# -gt 0 ]]; do
    case $1 in
        --no-download)
            DOWNLOAD_LATEST=False
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--no-download]"
            echo "  --no-download    Skip downloading latest rating lists, use existing data"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Starting rating lists initialization..."
if [ "$DOWNLOAD_LATEST" = True ]; then
    echo "Will download latest rating lists..."
else
    echo "Skipping download, using existing rating lists..."
fi

# Make sure we're in the project directory
cd "$(dirname "$0")"

# Create a Python script to run the initialization
cat > ./init_ratings.py << EOL
import os
import sys
import logging
from src.scraper.ratinglists.parsers import parse_fide_rating_list, parse_cfc_rating_list, parse_uscf_rating_list
from src.scraper.ratinglists.updater import update_cfc_rating_list, update_fide_rating_list, update_uscf_rating_list
from src.scraper.ratinglists.db import reset_collections

# Get download flag from command line argument
DOWNLOAD_LATEST = ${DOWNLOAD_LATEST}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rating_list_init')

try:
    logger.info("Starting rating list initialization...")
    logger.info(f"Download latest ratings: {DOWNLOAD_LATEST}")

    # First reset collections to ensure clean state
    logger.info("Resetting database collections...")
    reset_result = reset_collections()
    logger.info(f"Reset result: {'Successful' if reset_result else 'Failed'}")

    if DOWNLOAD_LATEST:
        # Download and parse the latest rating lists
        logger.info("Downloading and parsing latest rating lists...")
        cfc_update = update_cfc_rating_list()
        fide_update = update_fide_rating_list()
        uscf_update = update_uscf_rating_list()
        
        logger.info(f"FIDE update: {'Successful' if fide_update else 'Failed'}")
        logger.info(f"CFC update: {'Successful' if cfc_update else 'Failed'}")
        logger.info(f"USCF update: {'Successful' if uscf_update else 'Failed'}")
        
        # Check if at least one update was successful
        if not any([cfc_update, fide_update, uscf_update]):
            logger.error("All rating list updates failed!")
            sys.exit(1)
    else:
        # Parse existing rating list files without downloading
        logger.info("Parsing existing rating list files...")
        fide_result = parse_fide_rating_list()
        cfc_result = parse_cfc_rating_list()
        uscf_result = parse_uscf_rating_list()
        
        logger.info(f"FIDE parsing: {'Successful' if fide_result else 'Failed'}")
        logger.info(f"CFC parsing: {'Successful' if cfc_result else 'Failed'}")
        logger.info(f"USCF parsing: {'Successful' if uscf_result else 'Failed'}")
        
        # Check if at least one parsing was successful
        if not any([fide_result, cfc_result, uscf_result]):
            logger.error("All rating list parsing failed! Make sure rating list files exist.")
            sys.exit(1)

    logger.info("Rating list initialization completed!")

except Exception as e:
    logger.error(f"Fatal error during initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOL

# Run the initialization script
echo "Running Python initialization script..."
if python3 init_ratings.py; then
    echo "Python script completed successfully"
else
    echo "Python script failed with exit code $?"
    rm -f ./init_ratings.py
    exit 1
fi

# Clean up
rm -f ./init_ratings.py

echo "Rating list initialization complete!"