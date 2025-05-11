# Rating Lists Documentation

This document describes the rating list functionality in the FIDE API project, which integrates both FIDE and CFC chess rating lists into a searchable database.

## Overview

The rating lists module provides:

1. Automated downloading and parsing of official rating lists
2. MongoDB storage for efficient querying
3. API endpoints for accessing player data
4. Scheduled updates to keep data current

### Architecture Diagram

See [architecture_diagram.txt](architecture_diagram.txt) for a visual representation of the system components.

```
+-----------------------+     +-------------------------+
|                       |     |                         |
|  FIDE Rating List     |     |  CFC Rating List        |
|  (Monthly ZIP/XML)    |     |  (Weekly CSV)           |
|                       |     |                         |
+-----------+-----------+     +-----------+-------------+
            |                             |
            v                             v
    +-------+--------------------------+--+-------+
    |       Automated Updater Service           |
    |   (Scheduled Downloads & Processing)      |
    |                                           |
    +-------------------+---------------------+-+
                        |
                        v
            +-----------+-----------+
            |                       |
            |  MongoDB Database     |
            |                       |
            +-------+---------------+
                    |
                    v
    +---------------+----------------+
    |                                |
    |  FastAPI Endpoints             |
    |                                |
    +-----+------------------------+-+
          |                        |
          v                        v
+----------+-------------+ +-------+--------------+
|                        | |                      |
| Player Lookup Queries  | |  Search Queries      |
|                        | |                      |
+------------------------+ +----------------------+
```

## Data Sources

### FIDE Rating List
- **Source URL**: https://ratings.fide.com/download/standard_rating_list_xml.zip
- **Format**: ZIP file containing XML data
- **Update Frequency**: Monthly (typically on the 1st of each month)
- **Data Structure**: Contains player information including:
  - FIDE ID
  - Name
  - Federation
  - Gender
  - Title
  - Standard, Rapid, and Blitz ratings
  - Number of games

### CFC Rating List
- **Source URL**: https://www.chess.ca/wp-content/uploads/tdlist.txt
- **Format**: CSV file (tab-delimited)
- **Update Frequency**: Weekly
- **Data Structure**: Contains Canadian chess player information including:
  - CFC ID
  - Name
  - Expiry date
  - Rating
  - Quick rating
  - Province

## Database Structure

### FIDE Collection

```
{
  "fideid": "5011906",     // Unique index
  "name": "Carlsen, Magnus",
  "fed": "NOR",
  "sex": "M",
  "title": "g",
  "rating": 2830,
  "games": 0,
  "birthday": "1990/11/30",
  "flag": "i",
  "rapid_rating": 2880,
  "rapid_games": 0,
  "blitz_rating": 2878,
  "blitz_games": 0
}
```

### CFC Collection

```
{
  "id": "134893",          // Unique index
  "expiry": "2025-03-31",
  "name": "SMITH, JOHN",
  "rating": 1845,
  "quick": 1820,
  "province": "ON",
  "gender": "M"
}
```

### Metadata Collection

```
{
  "source": "fide",
  "last_update": "2023-08-01T00:00:00Z",
  "player_count": 357421,
  "download_url": "https://ratings.fide.com/download/standard_rating_list_xml.zip"
}
```

## Update Process

1. **Download**: Rating lists are downloaded from their respective sources
2. **Extract**: For FIDE, the ZIP file is extracted to access the XML file
3. **Parse**: Data is parsed into structured format
4. **Store**: Data is inserted into MongoDB with unique indexes
5. **Metadata**: Update timestamps and counts are recorded

## Scheduling

The updater service runs in the background and:

1. Checks for new FIDE data on the 1st of each month
2. Checks for new CFC data every Monday
3. Updates the database when new data is available
4. Records metadata about the update process

## API Endpoints

### Get FIDE Player
- **Endpoint**: `/ratinglist/fide/{player_id}`
- **Method**: GET
- **Response**: Single player object from FIDE list

### Get CFC Player
- **Endpoint**: `/ratinglist/cfc/{player_id}`
- **Method**: GET
- **Response**: Single player object from CFC list

### Get Top Players
- **Endpoint**: `/ratinglist/fide/top` or `/ratinglist/cfc/top`
- **Method**: GET
- **Query Parameters**: 
  - `limit`: Number of players to return (default: 100)
  - `category`: For FIDE, one of "standard", "rapid", "blitz" (default: "standard")
- **Response**: List of top rated players

### Search Players
- **Endpoint**: `/ratinglist/search`
- **Method**: GET
- **Query Parameters**:
  - `name`: Player name to search (required)
  - `source`: "fide", "cfc", or "all" (default: "all")
  - `limit`: Maximum number of results (default: 20)
- **Response**: List of matching players

### Get Metadata
- **Endpoint**: `/ratinglist/metadata`
- **Method**: GET
- **Response**: Information about last updates and player counts

### Manual Update
- **Endpoint**: `/ratinglist/update`
- **Method**: POST
- **Query Parameters**:
  - `source`: "fide", "cfc", or "all" (default: "all")
- **Response**: Status of update process

### Reset Database
- **Endpoint**: `/ratinglist/reset`
- **Method**: POST
- **Response**: Status of reset operation

### Health Check
- **Endpoint**: `/health`
- **Method**: GET
- **Response**: Health status information about the API and its dependencies
  ```json
  {
    "status": "ok",
    "timestamp": "2025-05-11T10:15:30.123456",
    "version": "1.0.0",
    "services": {
      "redis": {
        "status": "ok",
        "version": "7.0.5"
      },
      "mongodb": {
        "status": "ok",
        "version": "6.0.0",
        "fide_players": 357421,
        "cfc_players": 9845
      },
      "fide_website": {
        "status": "ok",
        "status_code": 200
      }
    }
  }
  ```

## Monitoring

The health check endpoint can be used for:
1. **Uptime Monitoring**: Tools like Uptime Robot, Pingdom, or AWS CloudWatch can periodically call the `/health` endpoint
2. **Container Orchestration**: Docker health checks or Kubernetes liveness/readiness probes
3. **Metrics Collection**: Extract metrics like player counts for dashboards

## Troubleshooting

### Common Issues

1. **Failed FIDE Download**:
   - Check if FIDE has changed the download URL format
   - Verify server connectivity to ratings.fide.com

2. **MongoDB Connection Issues**:
   - Check MongoDB container status with `docker ps`
   - Verify connection string in environment variables
   - Check MongoDB logs with `docker logs mongodb`

3. **Parser Errors**:
   - If data format has changed, parsers may need updates
   - Check logs for specific parsing errors

### Monitoring

- All operations are logged with timestamps and error information
- Check application logs with `docker logs fide-api`
- Database statistics available via the metadata endpoint

## Future Enhancements

1. **Additional Rating Lists**:
   - USCF (United States Chess Federation)
   - ECF (English Chess Federation)

2. **Advanced Search Features**:
   - Search by rating range
   - Filter by title, country, age

3. **Historical Data**:
   - Store historical ratings over time
   - Generate rating trends and graphs
