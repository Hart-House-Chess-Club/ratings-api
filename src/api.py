import requests

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import ORJSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from src.scraper import fide_scraper
from src.scraper.ratinglists import db as ratings_db
from src.scraper.ratinglists.updater import update_all_rating_lists

app = FastAPI(default_response_class=ORJSONResponse)

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

@app.get("/top_players/")
async def top_players(limit: int = 100, history: bool = False):
  response = fide_scraper.get_top_players(limit=limit, history=history)
  return response

@app.get("/player_history/")
async def player_history(fide_id: str):
  response = fide_scraper.get_player_history(fide_id=fide_id)
  return response

@app.get("/player_info/")
async def player_info(fide_id: str, history: bool = False):
  response = fide_scraper.get_player_info(fide_id=fide_id, history=history)
  return response

# Rating list endpoints
@app.get("/ratinglist/fide/{player_id}", tags=["Rating Lists"])
async def get_fide_player_rating(player_id: str):
  """Get a FIDE player's rating data from the rating list database."""
  player = ratings_db.get_fide_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/ratinglist/cfc/{player_id}", tags=["Rating Lists"])
async def get_cfc_player_rating(player_id: str):
  """Get a CFC player's rating data from the rating list database."""
  player = ratings_db.get_cfc_player(player_id)
  if not player:
    raise HTTPException(status_code=404, detail="Player not found")
  return player

@app.get("/ratinglist/fide/top", tags=["Rating Lists"])
async def get_top_fide_players(limit: int = 100):
  """Get top rated FIDE players from the rating list database."""
  return ratings_db.get_top_rated_fide(limit)

@app.get("/ratinglist/cfc/top", tags=["Rating Lists"])
async def get_top_cfc_players(limit: int = 100):
  """Get top rated CFC players from the rating list database."""
  return ratings_db.get_top_rated_cfc(limit)

@app.get("/ratinglist/search", tags=["Rating Lists"])
async def search_players(query: str, list_type: str = "fide"):
  """Search for players by name in either FIDE or CFC rating lists."""
  if list_type.lower() not in ["fide", "cfc"]:
    raise HTTPException(status_code=400, detail="list_type must be 'fide' or 'cfc'")
  
  results = ratings_db.search_player(query, list_type)
  return results

@app.get("/ratinglist/metadata", tags=["Rating Lists"])
async def get_rating_lists_metadata():
  """Get metadata about the rating lists (last update, etc.)"""
  return ratings_db.get_rating_list_metadata()

@app.post("/ratinglist/update", tags=["Rating Lists"])
async def trigger_rating_lists_update(background_tasks: BackgroundTasks):
  """Trigger an update of the rating lists (admin only)"""
  # In a production environment, you would add authentication here
  
  # Run update in the background to avoid blocking the request
  background_tasks.add_task(update_all_rating_lists)
  
  return {"status": "update_started", "message": "Rating list update has been started in the background"}

@app.post("/ratinglist/reset", tags=["Rating Lists"])
async def reset_rating_lists_db(background_tasks: BackgroundTasks):
    """Reset the rating lists database collections (admin only)"""
    # In a production environment, you would add authentication here
    
    from src.scraper.ratinglists.db import reset_collections
    
    success = reset_collections()
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reset rating lists database")
    
    # Start a background task to reinitialize the database
    background_tasks.add_task(update_all_rating_lists)
    
    return {"status": "reset_completed", "message": "Rating lists database has been reset and reinitialization started"}
