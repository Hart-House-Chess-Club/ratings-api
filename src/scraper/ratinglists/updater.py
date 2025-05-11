"""Updates for the FIDE and CFC rating lists.

This module handles downloading and updating the rating list files.
It can be run as a scheduled task to keep the data up-to-date.
"""

import os
import requests
import schedule
import time
import datetime
import logging
from typing import Optional, Dict, Any

from src.scraper.ratinglists.parsers import parse_fide_rating_list, parse_cfc_rating_list
from src.scraper.ratinglists.db import metadata_collection, mongo_enabled

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("rating_list_updater")

# File paths
RATING_LIST_DIR = "rating-lists"
FIDE_ZIP_PATH = os.path.join(RATING_LIST_DIR, "standard_rating_list_xml.zip")
FIDE_FILE_PATH = os.path.join(RATING_LIST_DIR, "standard_rating_list.xml")
CFC_FILE_PATH = os.path.join(RATING_LIST_DIR, "tdlist.txt")

# URLs - these will need to be updated with the correct sources
FIDE_DOWNLOAD_URL = os.environ.get(
    "FIDE_DOWNLOAD_URL", 
    "https://ratings.fide.com/download/standard_rating_list_xml.zip"
)
CFC_DOWNLOAD_URL = os.environ.get(
    "CFC_DOWNLOAD_URL",
    "https://www.chess.ca/wp-content/uploads/tdlist.txt"
)


def download_file(url: str, file_path: str) -> bool:
    """Download a file from a URL and save it locally.
    
    Args:
        url: The URL to download from
        file_path: Where to save the file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Make sure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Download with streaming to handle potentially large files
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False


def extract_zip(zip_path: str, extract_path: str) -> bool:
    """Extract a ZIP file.
    
    Args:
        zip_path: Path to the ZIP file
        extract_path: Directory to extract to
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import zipfile
        
        # Make sure the extract directory exists
        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
        
        # Extract the file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the ZIP
            file_list = zip_ref.namelist()
            logger.info(f"ZIP contains: {file_list}")
            
            # Extract all files
            zip_ref.extractall(os.path.dirname(extract_path))
            
            # If we know the exact filename in the ZIP, we can also extract just that file
            # For example: zip_ref.extract('standard_rating_list.xml', os.path.dirname(extract_path))
            
        return True
    except Exception as e:
        logger.error(f"Error extracting ZIP file {zip_path}: {e}")
        return False

def update_fide_rating_list() -> bool:
    """Update the FIDE rating list.
    
    1. Download the latest ZIP file
    2. Extract the XML file
    3. Parse and update the database
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting FIDE rating list update...")
    
    # Download the zip file
    if not download_file(FIDE_DOWNLOAD_URL, FIDE_ZIP_PATH):
        logger.error("Failed to download FIDE rating list ZIP file")
        return False
    
    # Extract the XML file from the ZIP
    logger.info(f"Extracting FIDE rating list from {FIDE_ZIP_PATH}...")
    if not extract_zip(FIDE_ZIP_PATH, FIDE_FILE_PATH):
        logger.error("Failed to extract FIDE rating list from ZIP")
        return False
    
    # Check if the XML file was properly extracted
    if not os.path.exists(FIDE_FILE_PATH):
        # Try to find the file - it might have a different name
        rating_dir = os.path.dirname(FIDE_FILE_PATH)
        files = os.listdir(rating_dir)
        xml_files = [f for f in files if f.endswith('.xml')]
        
        if xml_files:
            logger.info(f"Found XML files in the extract: {xml_files}")
            # Use the first XML file found
            extracted_path = os.path.join(rating_dir, xml_files[0])
            os.rename(extracted_path, FIDE_FILE_PATH)
        else:
            logger.error(f"No XML files found in the extract. Files found: {files}")
            return False
    
    # Parse and update database
    success = parse_fide_rating_list(FIDE_FILE_PATH)
    
    if success:
        logger.info("FIDE rating list update completed successfully")
    else:
        logger.error("Failed to parse FIDE rating list")
    
    return success


def update_cfc_rating_list() -> bool:
    """Update the CFC rating list.
    
    1. Download the latest file
    2. Parse and update the database
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info("Starting CFC rating list update...")
    
    # Download the file
    if not download_file(CFC_DOWNLOAD_URL, CFC_FILE_PATH):
        logger.error("Failed to download CFC rating list")
        return False
    
    # Parse and update database
    success = parse_cfc_rating_list(CFC_FILE_PATH)
    
    if success:
        logger.info("CFC rating list update completed successfully")
    else:
        logger.error("Failed to parse CFC rating list")
    
    return success


def schedule_updates():
    """Schedule regular updates for the rating lists."""
    if not mongo_enabled:
        logger.error("MongoDB not enabled, skipping scheduling of updates")
        return
    
    # Schedule FIDE updates monthly (on the 1st of each month)
    schedule.every().month.at("00:00").do(update_fide_rating_list)
    
    # Schedule CFC updates weekly (every Monday)
    schedule.every().monday.at("00:00").do(update_cfc_rating_list)
    
    logger.info("Rating list updates scheduled")
    
    # Run the scheduler
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour


def update_all_rating_lists() -> Dict[str, bool]:
    """Update all rating lists now.
    
    Returns:
        dict: Status of each update operation
    """
    results = {
        "fide": update_fide_rating_list(),
        "cfc": update_cfc_rating_list()
    }
    return results


if __name__ == "__main__":
    # When run directly, update all rating lists first, then start the scheduler
    logger.info("Running initial rating list updates...")
    update_all_rating_lists()
    
    logger.info("Starting rating list update scheduler...")
    schedule_updates()
