"""
MongoDB document serialization helper for FastAPI.
"""
import json
from datetime import datetime
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from typing import Any

class MongoJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB documents"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class MongoJSONResponse(JSONResponse):
    """Custom JSONResponse that handles MongoDB ObjectId and datetime serialization"""
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=MongoJSONEncoder,
        ).encode("utf-8")


def serialize_mongo_doc(obj):
    """Helper function to serialize MongoDB documents to JSON-compatible format.
    This can be used in the FastAPI app as a dependency.
    """
    if isinstance(obj, list):
        return [serialize_mongo_doc(item) for item in obj]
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, ObjectId):
                obj[key] = str(value)
            elif isinstance(value, datetime):
                obj[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                obj[key] = serialize_mongo_doc(value)
    
    return obj
