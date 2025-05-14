# Monitoring and Operations Guide

This document provides guidance for monitoring and operating the FIDE API in a production environment.

## Monitoring Strategy

### Health Checks

The API provides a `/health` endpoint that returns comprehensive information about the system health:

```
GET /health
```

This endpoint checks:
1. Redis connection and status
2. MongoDB connection and database statistics
3. External FIDE website accessibility

Example response:
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

### Recommended Tools

1. **Container-level Monitoring**:
   - Docker stats
   - Container health checks in docker-compose.yml
   - Example command: `docker stats fide-api redis mongodb`

2. **External Monitoring**:
   - Set up Uptime Robot, Pingdom, or similar
   - Configure to check the `/health` endpoint every 5 minutes
   - Set up alerts for failures

3. **Log Monitoring**:
   - Use Docker's built-in logging: `docker logs -f fide-api`
   - Consider implementing ELK stack (Elasticsearch, Logstash, Kibana) for more advanced monitoring

## Data Updates

### Rating List Update Schedule

- **FIDE Rating List**: Updates monthly (typically on the 1st of each month)
- **CFC Rating List**: Updates weekly

### Monitoring Updates

1. **Check Update Status**:
   ```
   GET /ratinglist/metadata
   ```
   This returns the last update timestamp and player counts.

2. **Verify Updater Process**:
   ```bash
   docker exec fide-api ps aux | grep updater
   ```
   You should see a Python process running for the updater service.

3. **Manual Updates**:
   If automatic updates are failing, use the command-line approach:
   ```bash
   # For FIDE updates
   docker exec fide-api python -c "from src.scraper.ratinglists.updater import update_fide_rating_list; update_fide_rating_list()"
   
   # For CFC updates
   docker exec fide-api python -c "from src.scraper.ratinglists.updater import update_cfc_rating_list; update_cfc_rating_list()"
   ```
   
   Note: The API endpoints for manual updates (`POST /update` and `POST /ratinglist/reset`) are currently disabled.

## Troubleshooting

### Common Issues

1. **API not responding**:
   - Check container status: `docker ps`
   - Check container logs: `docker logs fide-api`
   - Restart container if needed: `docker restart fide-api`

2. **Data not updating**:
   - Verify updater service is running
   - Check MongoDB connectivity in the `/health` endpoint
   - Check for errors in logs: `docker logs fide-api | grep ERROR`
   - Try a manual update via the API endpoint

3. **Memory issues**:
   - Check container resource usage: `docker stats`
   - Consider increasing memory limits in docker-compose.yml
   - Optimize MongoDB queries and indexes if needed

4. **High response times**:
   - Check Redis connectivity
   - Ensure Redis cache is being utilized
   - Monitor CPU usage with `docker stats`

## Backup Procedures

### MongoDB Backups

1. **Regular Backups**:
   ```bash
   docker exec mongodb mongodump --out /backup/$(date +%Y-%m-%d)
   docker cp mongodb:/backup ./backup
   ```

2. **Restore from Backup**:
   ```bash
   docker cp ./backup/2025-05-01 mongodb:/backup
   docker exec mongodb mongorestore /backup/2025-05-01
   ```

### Environment Configuration Backup

Keep a backup of your environment variables and configuration files:
```bash
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

## Scaling Considerations

### Horizontal Scaling

1. **API Service**:
   - Deploy multiple instances behind a load balancer
   - Ensure Redis is shared between instances for cache consistency

2. **MongoDB Scaling**:
   - Consider a replica set for higher availability
   - Implement sharding for very large datasets

### Vertical Scaling

1. **Memory Optimization**:
   - Increase container memory limits in docker-compose.yml
   - Optimize MongoDB indexes for common queries

2. **CPU Optimization**:
   - Profile API endpoints to identify bottlenecks
   - Consider dedicated servers for high-traffic deployments

## Regular Maintenance Tasks

1. **Weekly Tasks**:
   - Check logs for errors and warnings
   - Verify rating list updates are occurring
   - Monitor disk space usage

2. **Monthly Tasks**:
   - Review MongoDB indexes and optimize if needed
   - Test backup and restore procedures
   - Check for security updates to Docker images

3. **Quarterly Tasks**:
   - Performance review and optimization
   - Full system testing including failover scenarios
   - Update documentation with any operational changes
