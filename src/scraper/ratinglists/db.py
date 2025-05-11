"""MongoDB database connection and utility functions for rating lists."""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from typing import Optional, Dict, Any, List, Union

# MongoDB configuration - using environment variables with sensible defaults
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
MONGO_DB = os.environ.get('MONGO_DB', 'fide_api')
MONGO_FIDE_COLLECTION = os.environ.get('MONGO_FIDE_COLLECTION', 'fide_ratings')
MONGO_CFC_COLLECTION = os.environ.get('MONGO_CFC_COLLECTION', 'cfc_ratings')
MONGO_METADATA_COLLECTION = os.environ.get('MONGO_METADATA_COLLECTION', 'metadata')

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    fide_collection = db[MONGO_FIDE_COLLECTION]
    cfc_collection = db[MONGO_CFC_COLLECTION]
    metadata_collection = db[MONGO_METADATA_COLLECTION]
    
    # Create indexes for better query performance
    fide_collection.create_index([("id", ASCENDING)], unique=True)
    fide_collection.create_index([("fideid", ASCENDING)])
    fide_collection.create_index([("rating", DESCENDING)])
    fide_collection.create_index([("name", "text")])
    
    cfc_collection.create_index([("CFC#", ASCENDING)], unique=True)
    cfc_collection.create_index([("FIDE Number", ASCENDING)])
    cfc_collection.create_index([("Rating", DESCENDING)])
    cfc_collection.create_index([("Last", "text"), ("First", "text")])
    
    mongo_enabled = True
    print("MongoDB connection established successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}. Rating list features will be disabled.")
    mongo_enabled = False


def get_fide_player(player_id: str) -> Optional[Dict[str, Any]]:
    """Get FIDE player rating data by ID"""
    if not mongo_enabled:
        return None
    
    try:
        return fide_collection.find_one({"fideid": player_id})
    except Exception as e:
        print(f"Error retrieving FIDE player: {e}")
        return None


def get_cfc_player(cfc_id: str) -> Optional[Dict[str, Any]]:
    """Get CFC player rating data by ID"""
    if not mongo_enabled:
        return None
    
    try:
        return cfc_collection.find_one({"CFC#": cfc_id})
    except Exception as e:
        print(f"Error retrieving CFC player: {e}")
        return None


def get_top_rated_fide(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top rated FIDE players"""
    if not mongo_enabled:
        return []
    
    try:
        return list(fide_collection.find().sort("rating", DESCENDING).limit(limit))
    except Exception as e:
        print(f"Error retrieving top FIDE players: {e}")
        return []


def get_top_rated_cfc(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top rated CFC players"""
    if not mongo_enabled:
        return []
    
    try:
        return list(cfc_collection.find().sort("Rating", DESCENDING).limit(limit))
    except Exception as e:
        print(f"Error retrieving top CFC players: {e}")
        return []


def search_player(query: str, collection: str = "fide") -> List[Dict[str, Any]]:
    """Search for players by name"""
    if not mongo_enabled:
        return []
    
    try:
        if collection.lower() == "fide":
            return list(fide_collection.find({"$text": {"$search": query}}).limit(20))
        else:
            return list(cfc_collection.find({"$text": {"$search": query}}).limit(20))
    except Exception as e:
        print(f"Error searching for players: {e}")
        return []


def get_rating_list_metadata() -> Dict[str, Any]:
    """Get metadata about the rating lists (last update, etc.)"""
    if not mongo_enabled:
        return {}
    
    try:
        metadata = metadata_collection.find_one({"_id": "rating_lists"})
        return metadata if metadata else {}
    except Exception as e:
        print(f"Error retrieving metadata: {e}")
        return {}
