#!/bin/bash
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
    depends_on:
      - redis
    
  redis:
    image: redis:7-alpine
    container_name: fide-redis
    restart: always
    volumes:
      - redis-data:/data
    command: redis-server --save 60 1 --loglevel warning

volumes:
  redis-data:
EOL

# Run with docker-compose
docker-compose -f ~/fide-api-docker-compose.yml down
docker-compose -f ~/fide-api-docker-compose.yml up -d

echo "FIDE API deployed successfully!"
