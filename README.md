# Thumbnailify
Service for creating thumbnails from photos

## Tech Stalk
- Web Server
  - Python
  - aiohttp
  - aioamqp
  - aiocassandra
- Datastore
  - cassandra
- Worker
  - Python
- Queue
  - Rabit MQ

### Testing
- Integration Tests
  - Pytest
- Stress Tests
  - Locust

### Deployment
- Docker-compose
- k8s deployments (deployed on MiniKube with scaling)
