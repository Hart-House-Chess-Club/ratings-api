#!/bin/sh
# filepath: /Users/victorzheng/Documents/fide-api/fide-api/deploy.sh
# Simple script to pull and deploy the FIDE API Docker image

# Pull the latest image
docker pull ghcr.io/vzcodes/fide-api/fide-api:latest

# Create or update docker-compose.yml
cat > ~/fide-api-docker-compose.yml << 'EOL'
services:
  fide-api:
    container_name: fide-api
    image: ghcr.io/vzcodes/fide-api/fide-api:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_DB=0
      - CACHE_EXPIRY=3600
      - MONGO_URI=mongodb://mongodb:27017/
      - MONGO_DB=fide_api
      - FIDE_DOWNLOAD_URL=https://ratings.fide.com/download/standard_rating_list_xml.zip
      - CFC_DOWNLOAD_URL=https://www.chess.ca/wp-content/uploads/tdlist.txt
    depends_on:
      - redis
      - mongodb
    
  redis:
    image: redis:7-alpine
    container_name: fide-redis
    restart: always
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1 --loglevel warning
    
  mongodb:
    image: mongo:6
    container_name: fide-mongodb
    restart: always
    volumes:
      - mongodb-data:/data/db
    command: mongod --quiet --logpath /dev/null

volumes:
  redis-data:
  mongodb-data:
EOL

# Run with docker-compose
docker-compose -f ~/fide-api-docker-compose.yml down
docker-compose -f ~/fide-api-docker-compose.yml up -d

# Initialize rating lists if needed (using sh for Alpine compatibility)
echo "Initializing rating lists (this may take a while if files need to be downloaded)..."
docker exec fide-api sh -c "chmod +x /app/initialize_rating_lists.sh && sh /app/initialize_rating_lists.sh"

# Start the updater service
echo "Starting the rating list updater service..."
docker exec -d fide-api sh -c "chmod +x /app/start_updater_service.sh && sh /app/start_updater_service.sh"

echo "FIDE API deployed successfully!"