# FlipSync Docker Deployment Guide
<!-- AGENT_CONTEXT: Step-by-step deployment for unified Docker architecture -->
<!-- AGENT_PRIORITY: Hybrid architecture deployment in docker-desktop WSL distro -->
<!-- AGENT_PATTERN: Core services centralization with proper networking -->

## 🚀 **UNIFIED DOCKER DEPLOYMENT**

### **ARCHITECTURE OVERVIEW**
The unified configuration deploys **ALL core services** in the `docker-desktop` WSL distro, following our hybrid architecture principles:

```
docker-desktop WSL distro (ALL SERVICES)
├── Tier 1: Core Infrastructure
│   ├── PostgreSQL (port 1432)
│   ├── Redis (port 1379)
│   └── Ollama (port 11434)
├── Tier 2: AI/ML Support
│   └── Qdrant Vector DB (ports 6333, 6334)
├── Tier 3: Development Tools
│   ├── Adminer (port 1080)
│   ├── Redis Commander (port 1081)
│   ├── Jupyter (port 1888)
│   └── Chrome (ports 1222, 1223)
├── Tier 4: Support Services
│   ├── MailHog (ports 1025, 1825)
│   └── MinIO (ports 1900, 1901)
└── Tier 5: Monitoring
    ├── Prometheus (port 1090)
    └── Grafana (port 1300)
```

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### **1. Verify Docker Desktop Status**
```bash
# Check Docker Desktop is running
docker version
docker info

# Verify WSL2 integration
wsl --list --verbose
# Should show: docker-desktop, docker-desktop-data
```

### **2. Preserve Existing Ollama Data**
```bash
# Check if fs_main_ollama_data volume exists
docker volume ls | grep fs_main_ollama_data

# If it doesn't exist, create it
docker volume create fs_main_ollama_data
```

### **3. Create Required Directories**
```bash
cd /root/projects/flipsync/fs_clean

# Create monitoring directory if it doesn't exist
mkdir -p monitoring

# Create notebooks directory for Jupyter
mkdir -p notebooks
```

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Deploy Core Infrastructure (Tier 1)**
```bash
cd /root/projects/flipsync/fs_clean

# Deploy only core services first
docker-compose -f docker-compose.unified.yml up -d postgres redis ollama

# Wait for services to be healthy
echo "Waiting for core services to start..."
sleep 30

# Verify core services
docker ps --filter "label=core-service=true"
```

### **Step 2: Verify Core Services Health**
```bash
# Check PostgreSQL
docker exec flipsync-postgres pg_isready -U postgres

# Check Redis
docker exec flipsync-redis redis-cli ping

# Check Ollama (may take longer to start)
docker exec flipsync-ollama ollama list
```

### **Step 3: Deploy AI/ML Services (Tier 2)**
```bash
# Deploy vector database
docker-compose -f docker-compose.unified.yml up -d qdrant

# Verify Qdrant
curl -f http://localhost:6333/health || echo "Qdrant starting..."
```

### **Step 4: Deploy Development Tools (Tier 3)**
```bash
# Deploy development and management tools
docker-compose -f docker-compose.unified.yml up -d adminer redis-commander jupyter chrome

# Verify development tools
echo "Development tools deployed:"
echo "- Adminer: http://localhost:1080"
echo "- Redis Commander: http://localhost:1081"
echo "- Jupyter: http://localhost:1888 (token: flipsync-dev)"
echo "- Chrome: http://localhost:1223"
```

### **Step 5: Deploy Support Services (Tier 4)**
```bash
# Deploy communication and testing tools
docker-compose -f docker-compose.unified.yml up -d mailhog minio

# Verify support services
echo "Support services deployed:"
echo "- MailHog: http://localhost:1825"
echo "- MinIO: http://localhost:1901"
```

### **Step 6: Deploy Monitoring (Tier 5)**
```bash
# Create basic Prometheus config if it doesn't exist
cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'flipsync-services'
    static_configs:
      - targets: ['postgres:5432', 'redis:6379', 'ollama:11434']
EOF

# Deploy monitoring stack
docker-compose -f docker-compose.unified.yml up -d prometheus grafana

# Verify monitoring
echo "Monitoring deployed:"
echo "- Prometheus: http://localhost:1090"
echo "- Grafana: http://localhost:1300 (admin/admin)"
```

## 🔍 **POST-DEPLOYMENT VERIFICATION**

### **Complete Service Check**
```bash
# Check all services are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep flipsync

# Check service health
docker-compose -f docker-compose.unified.yml ps

# Check logs for any issues
docker-compose -f docker-compose.unified.yml logs --tail=50
```

### **Network Connectivity Test**
```bash
# Test internal network connectivity
docker exec flipsync-postgres pg_isready -h postgres -U postgres
docker exec flipsync-redis redis-cli -h redis ping

# Test from Ubuntu WSL distro
docker exec -it flipsync-postgres psql -U postgres -d flipsync -c "SELECT version();"
```

### **Service Access Verification**
```bash
# Database access from Ubuntu WSL distro
docker exec -it flipsync-postgres psql -U postgres -d flipsync

# Redis access
docker exec -it flipsync-redis redis-cli

# Ollama model check
docker exec -it flipsync-ollama ollama list
```

## 🎯 **FLIPSYNC INTEGRATION**

### **Database Initialization**
```bash
# Run FlipSync authentication database initialization
cd /root/projects/flipsync/fs_clean
PYTHONPATH=/root/projects/flipsync/fs_clean python3 fs_agt_clean/database/init_auth_db.py
```

### **MCP Server Configuration Update**
Update MCP servers to use new ports:
```json
{
  "postgres": {
    "args": [
      "postgresql://postgres:postgres@localhost:1432/flipsync"
    ]
  }
}
```

### **Application Configuration**
Update application environment variables:
```bash
# Database connection
DATABASE_URL=postgresql://postgres:postgres@localhost:1432/flipsync

# Redis connection
REDIS_URL=redis://localhost:1379

# Ollama connection
OLLAMA_BASE_URL=http://localhost:11434
```

## 🔧 **MANAGEMENT COMMANDS**

### **Start All Services**
```bash
cd /root/projects/flipsync/fs_clean
docker-compose -f docker-compose.unified.yml up -d
```

### **Stop All Services**
```bash
docker-compose -f docker-compose.unified.yml down
```

### **Restart Core Services Only**
```bash
docker-compose -f docker-compose.unified.yml restart postgres redis ollama
```

### **View Service Logs**
```bash
# All services
docker-compose -f docker-compose.unified.yml logs -f

# Specific service
docker-compose -f docker-compose.unified.yml logs -f postgres
```

### **Scale Services (if needed)**
```bash
# Scale Redis for high load
docker-compose -f docker-compose.unified.yml up -d --scale redis=2
```

## 🚨 **TROUBLESHOOTING**

### **Port Conflicts**
If you encounter port conflicts:
```bash
# Check what's using the ports
netstat -tulpn | grep :1432
netstat -tulpn | grep :1379

# Stop conflicting services
sudo systemctl stop postgresql
sudo systemctl stop redis-server
```

### **Volume Issues**
```bash
# Check volume status
docker volume ls
docker volume inspect fs_main_ollama_data

# Backup important volumes
docker run --rm -v fs_main_ollama_data:/data -v $(pwd):/backup alpine tar czf /backup/ollama-backup.tar.gz -C /data .
```

### **Network Issues**
```bash
# Recreate network
docker network rm flipsync-core-network
docker-compose -f docker-compose.unified.yml up -d
```

### **Service Health Issues**
```bash
# Check service health
docker inspect flipsync-postgres | grep Health -A 10
docker inspect flipsync-redis | grep Health -A 10
docker inspect flipsync-ollama | grep Health -A 10
```

## 📊 **SERVICE ENDPOINTS SUMMARY**

| Service | Internal Port | External Port | Web UI | Purpose |
|---------|---------------|---------------|---------|---------|
| PostgreSQL | 5432 | 1432 | - | Primary database |
| Redis | 6379 | 1379 | - | Cache/sessions |
| Ollama | 11434 | 11434 | - | AI models |
| Qdrant | 6333/6334 | 6333/6334 | http://localhost:6333/dashboard | Vector DB |
| Adminer | 8080 | 1080 | http://localhost:1080 | DB management |
| Redis Commander | 8081 | 1081 | http://localhost:1081 | Redis management |
| Jupyter | 8888 | 1888 | http://localhost:1888 | Data analysis |
| Chrome | 3000/8080 | 1222/1223 | http://localhost:1223 | Browser automation |
| MailHog | 1025/8025 | 1025/1825 | http://localhost:1825 | Email testing |
| MinIO | 9000/9001 | 1900/1901 | http://localhost:1901 | Object storage |
| Prometheus | 9090 | 1090 | http://localhost:1090 | Metrics |
| Grafana | 3000 | 1300 | http://localhost:1300 | Monitoring |

## 🎯 **SUCCESS CRITERIA**

✅ **Deployment Successful When:**
- All 12 services are running and healthy
- PostgreSQL accessible on port 1432
- Redis accessible on port 1379
- Ollama responding on port 11434
- All web UIs accessible
- FlipSync authentication database initialized
- MCP servers can connect to services
- No port conflicts with existing services

This unified configuration provides a **complete development ecosystem** running entirely in the `docker-desktop` WSL distro, following our hybrid architecture principles.
