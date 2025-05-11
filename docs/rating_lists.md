# FIDE API Rating Lists Feature

This document describes the new rating list feature added to FIDE API.

## About Rating Lists

The FIDE API now supports two rating lists:

1. **FIDE Standard Rating List**: The official FIDE rating list for standard chess
2. **CFC Rating List**: The Canadian Chess Federation rating list

## Data Sources

- FIDE Rating List: Downloaded from `https://ratings.fide.com/download/standard_rating_list_xml.zip`
- CFC Rating List: Downloaded from `https://www.chess.ca/wp-content/uploads/tdlist.txt`

## How It Works

1. The system downloads the rating lists from the official sources
2. For FIDE ratings, it extracts the XML file from the ZIP archive
3. Data is parsed and stored in a MongoDB database
4. Updates are scheduled automatically (monthly for FIDE, weekly for CFC)
5. Users can query data through the API endpoints

## API Endpoints

### FIDE Rating List Endpoints

- `GET /ratinglist/fide/{player_id}`: Get a FIDE player's rating data
- `GET /ratinglist/fide/top`: Get top rated FIDE players

### CFC Rating List Endpoints

- `GET /ratinglist/cfc/{player_id}`: Get a CFC player's rating data
- `GET /ratinglist/cfc/top`: Get top rated CFC players

### Common Endpoints

- `GET /ratinglist/search`: Search for players by name
- `GET /ratinglist/metadata`: Get rating lists metadata
- `POST /ratinglist/update`: Manually trigger a rating list update

## Configuration

Set these environment variables to configure the rating list functionality:

- `MONGO_URI`: MongoDB connection URI (default: `mongodb://localhost:27017/`)
- `MONGO_DB`: MongoDB database name (default: `fide_api`)
- `FIDE_DOWNLOAD_URL`: URL to download FIDE rating list (default: `https://ratings.fide.com/download/standard_rating_list_xml.zip`)
- `CFC_DOWNLOAD_URL`: URL to download CFC rating list (default: `https://www.chess.ca/wp-content/uploads/tdlist.txt`)
