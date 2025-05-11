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
cfc_update = update_cfc_rating_list()
fide_update = update_fide_rating_list()

logger.info(f"FIDE parsing: {'Successful' if fide_update else 'Failed'}")
logger.info(f"CFC parsing: {'Successful' if cfc_update else 'Failed'}")

logger.info("Rating list initialization completed!")
