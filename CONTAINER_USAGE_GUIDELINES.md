# FlipSync Container Usage Guidelines

## 🚨 **CRITICAL: Container Selection Guidelines**

### **✅ PREFERRED CONTAINERS (Use These)**

#### **Production API Container**
- **Container Name**: `flipsync-production-api`
- **Compose File**: `docker-compose.production.yml`
- **Service Name**: `api`
- **Why Use**: ✅ **Caches dependencies** - rebuilds are fast (10 seconds)
- **Command**: `docker-compose -f docker-compose.production.yml up -d api`

#### **Infrastructure Services**
- **Redis**: `flipsync-infrastructure-redis` (from `docker-compose.infrastructure.yml`)
- **PostgreSQL**: `flipsync-infrastructure-postgres` (from `docker-compose.infrastructure.yml`)
- **Why Use**: ✅ **Shared across projects** - persistent data and caching

### **❌ AVOID THESE CONTAINERS**

#### **FlipSync App Container**
- **Container Name**: `flipsync-api`
- **Compose File**: `docker-compose.flipsync-app.yml`
- **Service Name**: `flipsync-api`
- **Why Avoid**: ❌ **Forces dependency reinstall** - rebuilds take 5+ minutes
- **When to Use**: Only for testing new environment configurations

---

## 🔧 **Standard Workflow**

### **Starting FlipSync for Development**
```bash
# 1. Start infrastructure services (Redis, PostgreSQL)
docker-compose -f docker-compose.infrastructure.yml up -d redis postgres

# 2. Start production API (with cached dependencies)
docker-compose -f docker-compose.production.yml up -d api

# 3. Start Flutter web app
cd mobile && flutter run -d web-server --web-port 3001 --web-hostname 0.0.0.0
```

### **Restarting After Code Changes**
```bash
# Quick restart (10 seconds) - dependencies cached
docker-compose -f docker-compose.production.yml restart api
```

### **Full Rebuild (Only When Necessary)**
```bash
# Only when Dockerfile or dependencies change
docker-compose -f docker-compose.production.yml up -d --build api
```

---

## 📋 **Container Status Reference**

### **Required Running Containers**
- ✅ `flipsync-production-api` (API backend)
- ✅ `flipsync-infrastructure-redis` (Redis cache)
- ✅ `flipsync-infrastructure-postgres` (PostgreSQL database)

### **Optional Containers**
- 🔧 `flipsync-infrastructure-adminer` (Database admin tool - not needed for FlipSync operation)
- 🔧 `flipsync-production-nginx` (Load balancer - optional for development)
- 🔧 `flipsync-production-qdrant` (Vector database - for AI features)

### **Containers to Avoid**
- ❌ `flipsync-api` (Forces dependency reinstall)
- ❌ Any Ollama containers (FlipSync uses OpenAI APIs only)

---

## 🎯 **Key Principles**

1. **Dependency Caching**: Always prefer containers that cache dependencies
2. **Infrastructure Sharing**: Use shared infrastructure services across projects
3. **Fast Iteration**: Optimize for quick restart cycles during development
4. **Production Parity**: Use production-like containers for development

---

## 🚨 **Emergency Recovery**

If containers are in a bad state:
```bash
# Stop all FlipSync containers
docker stop $(docker ps -q --filter "name=flipsync")

# Start fresh with correct containers
docker-compose -f docker-compose.infrastructure.yml up -d redis postgres
docker-compose -f docker-compose.production.yml up -d api
```

---

**Last Updated**: 2025-06-26  
**Created By**: AI Agent (to prevent future dependency reinstall issues)
