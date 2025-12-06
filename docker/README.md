# LoraForge Docker Setup

## Quick Start

```bash
# Start all services
cd docker
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| postgres | 5432 | PostgreSQL database |
| redis | 6379 | Redis cache |
| gateway | 8300 | Unified API Gateway |

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# PostgreSQL
POSTGRES_USER=civitai
POSTGRES_PASSWORD=civitai_secret
POSTGRES_DB=civitai_learning

# API Settings
LOG_LEVEL=INFO
```

## Health Checks

All services have health checks configured:

```bash
# Check postgres
docker-compose exec postgres pg_isready -U civitai

# Check redis
docker-compose exec redis redis-cli ping

# Check gateway
curl http://localhost:8300/health
```

## Database

The `init.sql` file automatically creates:
- Images table with full tracking
- Tag analysis table
- Rating events table
- Story collections tables
- User preferences tables
- Learning log table
- Dashboard stats view

## Connecting from Host

When services run in Docker, use these connection strings:

```python
# From host machine
DATABASE_URL = "postgresql://civitai:civitai_secret@localhost:5432/civitai_learning"
REDIS_URL = "redis://localhost:6379"
GATEWAY_URL = "http://localhost:8300"

# From inside Docker containers
DATABASE_URL = "postgresql://civitai:civitai_secret@postgres:5432/civitai_learning"
REDIS_URL = "redis://redis:6379"
```

## Volumes

Data is persisted in Docker volumes:
- `postgres_data` - Database files
- `redis_data` - Redis persistence
- `gateway_logs` - API logs

## Development

For development, scripts are mounted read-only:
```yaml
volumes:
  - ../scripts:/app/scripts:ro
  - ../data:/app/data
```

## Troubleshooting

### Docker Desktop not running
```powershell
# Start Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
# Wait for it to initialize (30-60 seconds)
```

### Check container status
```bash
docker-compose ps
docker-compose logs [service_name]
```

### Reset everything
```bash
docker-compose down -v  # Removes volumes too
docker-compose up -d --build
```
