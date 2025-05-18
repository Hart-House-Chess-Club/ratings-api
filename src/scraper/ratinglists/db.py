"""MongoDB database connection and utility functions for rating lists."""

import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from typing import Optional, Dict, Any, List, Union

# MongoDB configuration - using environment variables with sensible defaults
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB = os.environ.get('MONGO_DB', 'fide_api')
MONGO_FIDE_COLLECTION = os.environ.get('MONGO_FIDE_COLLECTION', 'fide_ratings')
MONGO_CFC_COLLECTION = os.environ.get('MONGO_CFC_COLLECTION', 'cfc_ratings')
MONGO_USCF_COLLECTION = os.environ.get('MONGO_USCF_COLLECTION', 'uscf_ratings')
MONGO_METADATA_COLLECTION = os.environ.get('MONGO_METADATA_COLLECTION', 'metadata')

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    fide_collection = db[MONGO_FIDE_COLLECTION]
    cfc_collection = db[MONGO_CFC_COLLECTION]
    uscf_collection = db[MONGO_USCF_COLLECTION]
    metadata_collection = db[MONGO_METADATA_COLLECTION]
    
    # Create indexes for better query performance
    # Use fideid as the unique identifier
    fide_collection.create_index([("fideid", ASCENDING)], unique=True)
    fide_collection.create_index([("rating", DESCENDING)])
    fide_collection.create_index([("name", "text")])
    
    cfc_collection.create_index([("CFC Number", ASCENDING)], unique=True)
    cfc_collection.create_index([("FIDE Number", ASCENDING)])
    cfc_collection.create_index([("Rating", DESCENDING)])
    cfc_collection.create_index([("Last", "text"), ("First", "text")])

    uscf_collection.create_index([("USCF Number", ASCENDING)], unique=True)
    uscf_collection.create_index([("FIDE Number", ASCENDING)])
    uscf_collection.create_index([("Rating", DESCENDING)])
    uscf_collection.create_index([("Last", "text"), ("First", "text")])
    
    mongo_enabled = True
    print("MongoDB connection established successfully")
except Exception as e:
    print(f"MongoDB connection failed: {e}. Rating list features will be disabled.")
    mongo_enabled = False


def make_json_serializable(doc):
    """Convert MongoDB document to be JSON serializable by converting ObjectId to string."""
    if not doc:
        return doc
        
    if isinstance(doc, list):
        return [make_json_serializable(item) for item in doc]
    
    if isinstance(doc, dict):
        for key, value in doc.items():
            # ObjectId typically has an attribute called "_type" with value "ObjectId"
            # and will always have the "_id" field
            if key == "_id" and hasattr(value, "__str__"):
                doc[key] = str(value)
            elif isinstance(value, dict):
                doc[key] = make_json_serializable(value)
            elif isinstance(value, list):
                doc[key] = make_json_serializable(value)
    
    return doc


def get_fide_player(player_id: str) -> Optional[Dict[str, Any]]:
    """Get FIDE player rating data by ID"""
    if not mongo_enabled:
        return None
    
    try:
        player_data = fide_collection.find_one({"fideid": player_id})
        return make_json_serializable(player_data)
    except Exception as e:
        print(f"Error retrieving FIDE player: {e}")
        return None


def get_cfc_player(cfc_id: str) -> Optional[Dict[str, Any]]:
    """Get CFC player rating data by ID"""
    if not mongo_enabled:
        return None
    
    try:
        player_data = cfc_collection.find_one({"CFC Number": cfc_id})
        return make_json_serializable(player_data)
    except Exception as e:
        print(f"Error retrieving CFC player: {e}")
        return None

def get_uscf_player(uscf_id: int) -> Optional[Dict[str, Any]]:
    """Get USCF player rating data by ID"""
    if not mongo_enabled:
        return None
    
    try:
        player_data = uscf_collection.find_one({"mem_id": uscf_id})
        return make_json_serializable(player_data)
    except Exception as e:
        print(f"Error retrieving USCF player: {e}")
        return None


def get_top_rated_fide(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top rated FIDE players"""
    if not mongo_enabled:
        return []
    
    try:
        players = list(fide_collection.find().sort("rating", DESCENDING).limit(limit))
        return make_json_serializable(players)
    except Exception as e:
        print(f"Error retrieving top FIDE players: {e}")
        return []


def get_top_rated_cfc(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top rated CFC players"""
    if not mongo_enabled:
        return []
    
    try:
        # Convert Rating to integer for proper numerical sorting
        pipeline = [
            {"$addFields": {"RatingNum": {"$toInt": "$Rating"}}},
            {"$sort": {"RatingNum": -1}},
            {"$limit": limit}
        ]
        players = list(cfc_collection.aggregate(pipeline))
        return make_json_serializable(players)
    except Exception as e:
        print(f"Error retrieving top CFC players: {e}")
        return []

def get_top_rated_uscf(limit: int = 100) -> List[Dict[str, Any]]:
    """Get top rated USCF players"""
    if not mongo_enabled:
        return []
    
    try:
        players = list(uscf_collection.find().sort("rating", DESCENDING).limit(limit))
        return make_json_serializable(players)
    except Exception as e:
        print(f"Error retrieving top USCF players: {e}")
        return []


def search_player(query: str, collection: str = "fide") -> List[Dict[str, Any]]:
    """Search for players by name"""
    if not mongo_enabled:
        return []
    
    try:
        if collection.lower() == "fide":
            players = list(fide_collection.find({"$text": {"$search": query}}).limit(20))
        elif collection.lower() == "cfc":
            players = list(cfc_collection.find({"$text": {"$search": query}}).limit(20))
        else:
            players = list(uscf_collection.find({"$text": {"$search": query}}).limit(20))
            
        return make_json_serializable(players)
    except Exception as e:
        print(f"Error searching for players: {e}")
        return []


def get_rating_list_metadata() -> Dict[str, Any]:
    """Get metadata about the rating lists (last update, etc.)"""
    if not mongo_enabled:
        return {}
    
    try:
        metadata = metadata_collection.find_one({"_id": "rating_lists"})
        return make_json_serializable(metadata) if metadata else {}
    except Exception as e:
        print(f"Error retrieving metadata: {e}")
        return {}


def reset_collections():
    """Reset (drop and recreate) all collections.
    Use this when there are issues with indexes or corrupted data.
    """
    if not mongo_enabled:
        print("MongoDB not enabled, cannot reset collections")
        return False
    
    try:
        # Drop collections
        fide_collection.drop()
        cfc_collection.drop()
        metadata_collection.drop()
        
        # Recreate indexes
        # fide_collection.create_index([("fideid", ASCENDING)], unique=True)
        # fide_collection.create_index([("rating", DESCENDING)])
        # fide_collection.create_index([("name", "text")])
        
        # cfc_collection.create_index([("CFC Number", ASCENDING)], unique=True)
        # cfc_collection.create_index([("FIDE Number", ASCENDING)])
        # cfc_collection.create_index([("Rating", DESCENDING)])
        # cfc_collection.create_index([("Last", "text"), ("First", "text")])
        
        print("Collections reset successfully")
        return True
    except Exception as e:
        print(f"Error resetting collections: {e}")
        return False
