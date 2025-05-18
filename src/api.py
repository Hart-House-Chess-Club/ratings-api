import requests
import datetime
import os
import pymongo

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import ORJSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.scraper import fide_scraper
from src.scraper.ratinglists import db as ratings_db
from src.scraper.ratinglists.updater import update_all_rating_lists, update_cfc_rating_list, update_fide_rating_list

app = FastAPI(
    title="Chess Ratings API",
    version="2.0.0",
    description="Highly reliable, free, chess ratings API for FIDE, CFC, and other rating systems.",
    default_response_class=ORJSONResponse
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

# default endpoints -> redirect to docs
@app.get("/")
def home():
  return RedirectResponse('/docs')

@app.get("/fide/top_active/", tags=["FIDE"])
async def top_players(limit: int = 100, history: bool = False):
  response = fide_scraper.get_top_players(limit=limit, history=history)
  return response

# FIDE endpoints
@app.get("/fide/top_by_rating", tags=["FIDE"])
async def get_top_fide_players(limit: int = 100):
  """Get top rated FIDE players from the rating list database."""
  return ratings_db.get_top_rated_fide(limit)

@app.get("/fide/player_history/", tags=["FIDE"])
async def player_history(fide_id: str):
  response = fide_scraper.get_player_history(fide_id=fide_id)
  return response

@app.get("/fide/{player_id}", tags=["FIDE"])
async def get_fide_player_rating(player_id: str):
  """Get a FIDE player's rating data from the rating list database."""
  player = ratings_db.get_fide_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player


@app.get("/fide/player_info/", tags=["FIDE"])
async def player_info(fide_id: str, history: bool = False):
  response = fide_scraper.get_player_info(fide_id=fide_id, history=history)
  return response

@app.get("/cfc/top_by_rating", tags=["CFC"])
async def get_top_cfc_players(limit: int = 100):
  """Get top rated CFC players from the rating list database."""
  return ratings_db.get_top_rated_cfc(limit)

@app.get("/cfc/{player_id}", tags=["CFC"])
async def get_cfc_player_rating(player_id: str):
  """Get a CFC player's rating data from the rating list database."""
  player = ratings_db.get_cfc_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/uscf/top_by_rating", tags=["USCF"])
async def get_top_uscf_players(limit: int = 100):
  """Get top rated USCF players from the rating list database."""
  return ratings_db.get_top_rated_uscf(limit)

@app.get("/uscf/{player_id}", tags=["USCF"])
async def get_uscf_player_rating(player_id: str):
  """Get a USCF player's rating data from the rating list database."""
  player = ratings_db.get_uscf_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/ratinglist/search", tags=["All"])
async def search_players(query: str, list_type: str = "fide"):
  """Search for players by name in either FIDE or CFC rating lists."""
  if list_type.lower() not in ["fide", "cfc"]:
    raise HTTPException(status_code=400, detail="list_type must be 'fide' or 'cfc'")
  
  results = ratings_db.search_player(query, list_type)
  return results

@app.get("/ratinglist/metadata", tags=["All"])
async def get_rating_lists_metadata():
  """Get metadata about the rating lists (last update, etc.)"""
  return ratings_db.get_rating_list_metadata()

# @app.post("/update", tags=["System"])
# async def trigger_rating_lists_update(background_tasks: BackgroundTasks):
#   """Trigger an update of the rating lists (admin only)"""
#   # In a production environment, you would add authentication here
  
#   # Run update in the background to avoid blocking the request
#   background_tasks.add_task(update_all_rating_lists)
  
#   return {"status": "update_started", "message": "Rating list update has been started in the background"}

# @app.post("/ratinglist/reset", tags=["System"])
# async def reset_rating_lists_db(background_tasks: BackgroundTasks):
#     """Reset the rating lists database collections (admin only)"""
#     # In a production environment, you would add authentication here
    
#     from src.scraper.ratinglists.db import reset_collections
    
#     success = reset_collections()
#     if not success:
#         raise HTTPException(status_code=500, detail="Failed to reset rating lists database")
    
#     # Start a background task to reinitialize the database
#     background_tasks.add_task(update_all_rating_lists)
    
#     return {"status": "reset_completed", "message": "Rating lists database has been reset and reinitialization started"}

@app.get("/health", tags=["All"])
async def health_check():
    """Health check endpoint for monitoring the API status"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Redis connection
    try:
        from src.scraper.cache import redis_client
        redis_info = redis_client.info()
        health_status["services"]["redis"] = {
            "status": "ok",
            "version": redis_info.get("redis_version", "unknown")
        }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check MongoDB connection
    try:
        mongo_uri = os.environ.get("MONGO_URI", "MONGO_TOKEN")
        mongo_client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        server_info = mongo_client.server_info()
        fide_count = ratings_db.fide_collection.count_documents({})
        cfc_count = ratings_db.cfc_collection.count_documents({})
        
        health_status["services"]["mongodb"] = {
            "status": "ok",
            "version": server_info.get("version", "unknown"),
            "fide_players": fide_count,
            "cfc_players": cfc_count
        }
    except Exception as e:
        health_status["services"]["mongodb"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check FIDE website accessibility
    try:
        fide_response = requests.get("https://ratings.fide.com", timeout=5)
        health_status["services"]["fide_website"] = {
            "status": "ok" if fide_response.status_code == 200 else "error",
            "status_code": fide_response.status_code
        }
    except Exception as e:
        health_status["services"]["fide_website"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status
