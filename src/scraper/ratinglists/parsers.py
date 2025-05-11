"""Parsers for the FIDE and CFC rating lists."""

import os
import csv
import xmltodict
import datetime
import pandas as pd
from typing import Dict, List, Any, Optional
from pymongo.collection import Collection

from src.scraper.ratinglists.db import (
    fide_collection,
    cfc_collection,
    metadata_collection,
    mongo_enabled
)


def extract_zip(zip_path: str, extract_dir: str) -> str:
    """Extract an XML file from a ZIP archive.
    
    Args:
        zip_path: Path to the ZIP file
        extract_dir: Directory to extract to
        
    Returns:
        str: Path to the extracted XML file, or None if extraction failed
    """
    try:
        import zipfile
        
        # Make sure the extract directory exists
        os.makedirs(extract_dir, exist_ok=True)
        
        # Extract the file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the ZIP
            file_list = zip_ref.namelist()
            print(f"ZIP contains: {file_list}")
            
            # Extract all files
            zip_ref.extractall(extract_dir)
            
            # Find XML files in the extracted content
            xml_files = [f for f in file_list if f.endswith('.xml')]
            if xml_files:
                return os.path.join(extract_dir, xml_files[0])
            else:
                print("No XML files found in ZIP archive")
                return None
    except Exception as e:
        print(f"Error extracting ZIP file {zip_path}: {e}")
        return None

def parse_fide_rating_list(file_path: str = "rating-lists/standard_rating_list_xml.zip") -> bool:
    """Parse the FIDE rating list XML file and store in MongoDB.
    
    Returns True if successful, False otherwise.
    """
    if not mongo_enabled:
        print("MongoDB not enabled, skipping FIDE rating list parsing")
        return False
    
    try:
        # Check if ZIP file exists
        if not os.path.exists(file_path):
            print(f"FIDE rating list file not found at {file_path}")
            return False
        
        # If file is a ZIP file, extract it first
        if file_path.endswith('.zip'):
            print(f"Extracting ZIP file: {file_path}")
            extract_dir = os.path.dirname(file_path)
            xml_path = extract_zip(file_path, extract_dir)
            if not xml_path:
                print("Failed to extract XML file from ZIP")
                return False
            file_path = xml_path
            print(f"Extracted XML file: {file_path}")
        
        # Check if the XML file exists now
        if not os.path.exists(file_path):
            print(f"FIDE rating list XML file not found at {file_path} after extraction")
            return False
        
        print(f"Starting to parse FIDE rating list from {file_path}...")
        
        # For large XML files, we use a streaming approach
        # Get file size for logging
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"FIDE XML file size: {file_size:.2f} MB")
        
        # Process in batches to avoid memory issues
        batch_size = 1000
        player_batch = []
        player_count = 0
        
        # Use a streaming XML parser for large files
        with open(file_path, 'rb') as file:
            def handle_player(_, player):
                nonlocal player_batch, player_count
                
                # Convert to a more MongoDB-friendly format
                processed_player = {
                    "fideid": player.get("fideid", ""),
                    "name": player.get("name", ""),
                    "country": player.get("country", ""),
                    "sex": player.get("sex", ""),
                    "title": player.get("title", ""),
                    "w_title": player.get("w_title", ""),
                    "o_title": player.get("o_title", ""),
                    "foa_title": player.get("foa_title", ""),
                    "rating": int(player.get("rating", "0") or "0"),
                    "games": int(player.get("games", "0") or "0"),
                    "birth_year": int(player.get("birthday", "0") or "0"),
                    "flag": player.get(("flag", "") or "i"),
                    "k_factor": player.get("k", ""),
                }
                
                player_batch.append(processed_player)
                player_count += 1
                
                # When batch is full, insert and clear
                if len(player_batch) >= batch_size:
                    try:
                        # Use upsert to update existing or insert new
                        for p in player_batch:
                            fide_collection.update_one(
                                {"fideid": p["fideid"]}, 
                                {"$set": p}, 
                                upsert=True
                            )
                        print(f"Processed {player_count} FIDE players...")
                        player_batch = []
                    except Exception as e:
                        print(f"Error inserting batch: {e}")
                
                return True
            
            # Custom parsing with callback for "player" elements
            # Use a simple streaming approach
            xmltodict.parse(file, item_depth=2, item_callback=handle_player)
            
            # Insert any remaining players
            if player_batch:
                for p in player_batch:
                    fide_collection.update_one(
                        {"fideid": p["fideid"]}, 
                        {"$set": p}, 
                        upsert=True
                    )
        
        # Update metadata
        metadata_collection.update_one(
            {"_id": "rating_lists"},
            {"$set": {
                "fide_last_updated": datetime.datetime.now(),
                "fide_player_count": player_count
            }},
            upsert=True
        )
        
        print(f"Successfully parsed FIDE rating list: {player_count} players")
        return True
        
    except Exception as e:
        print(f"Error parsing FIDE rating list: {e}")
        return False


def parse_cfc_rating_list(file_path: str = "rating-lists/tdlist.txt") -> bool:
    """Parse the CFC rating list text file and store in MongoDB.
    
    Returns True if successful, False otherwise.
    """
    if not mongo_enabled:
        print("MongoDB not enabled, skipping CFC rating list parsing")
        return False
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"CFC rating list file not found at {file_path}")
            return False
        
        print(f"Starting to parse CFC rating list from {file_path}...")
        
        # Use pandas to efficiently parse the CSV
        # The CFC list is a more manageable size than the FIDE XML
        df = pd.read_csv(file_path)
        
        # Clean column names
        df.columns = [col.strip('"') for col in df.columns]
        
        # Process in batches
        batch_size = 1000
        total_records = len(df)
        
        for i in range(0, total_records, batch_size):
            batch = df.iloc[i:i+batch_size]
            records = batch.to_dict('records')
            
            # Insert batch
            for record in records:
                # Clean the record by converting NaN values to None
                clean_record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
                
                # Use CFC# as the unique identifier
                cfc_collection.update_one(
                    {"CFC Number": clean_record["CFC#"]},
                    {"$set": clean_record},
                    upsert=True
                )
            
            print(f"Processed {i + len(batch)}/{total_records} CFC players...")
        
        # Update metadata
        metadata_collection.update_one(
            {"_id": "rating_lists"},
            {"$set": {
                "cfc_last_updated": datetime.datetime.now(),
                "cfc_player_count": total_records
            }},
            upsert=True
        )
        
        print(f"Successfully parsed CFC rating list: {total_records} players")
        return True
        
    except Exception as e:
        print(f"Error parsing CFC rating list: {e}")
        return False
