"""
Gunicorn configuration for FlipSync production deployment.
Optimized for 35+ agent multi-tier architecture with high performance requirements.
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))
max_workers = int(os.getenv("MAX_WORKERS", 8))
worker_class = os.getenv("WORKER_CLASS", "uvicorn.workers.UvicornWorker")
worker_connections = int(os.getenv("WORKER_CONNECTIONS", 1000))
max_requests = int(os.getenv("MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("MAX_REQUESTS_JITTER", 100))

# Timeout settings optimized for agent coordination
timeout = int(os.getenv("TIMEOUT", 120))
keepalive = int(os.getenv("KEEPALIVE", 2))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", 30))

# Performance optimizations
preload_app = os.getenv("PRELOAD_APP", "true").lower() == "true"
enable_stdio_inheritance = True
reuse_port = True

# Process naming
proc_name = "flipsync-api"

# User and group
user = "app"
group = "app"

# Logging configuration
accesslog = "/app/logs/api/access.log"
errorlog = "/app/logs/api/error.log"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# SSL (if enabled)
keyfile = os.getenv("SSL_KEYFILE")
certfile = os.getenv("SSL_CERTFILE")

# Hooks for production monitoring
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("FlipSync API starting with %s workers", workers)
    server.log.info("Production configuration loaded")
    server.log.info("Agent architecture: 35+ agents, 7 workflow templates")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("FlipSync API reloading workers")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info("Worker %s interrupted", worker.pid)

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info("Worker %s about to be forked", worker.pid)

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    worker.log.info("Worker %s spawned", worker.pid)

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("FlipSync API ready to serve requests")
    server.log.info("Performance target: <2s API response time")
    server.log.info("Scalability target: 100+ concurrent users")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.info("Worker %s aborted", worker.pid)

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug("%s %s", req.method, req.path)

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    # Log slow requests for performance monitoring
    if hasattr(req, 'start_time'):
        duration = time.time() - req.start_time
        if duration > 2.0:  # Log requests taking more than 2 seconds
            worker.log.warning("Slow request: %s %s took %.2fs", req.method, req.path, duration)

# Environment-specific configurations
if os.getenv("ENVIRONMENT") == "production":
    # Production-specific settings
    workers = min(workers, max_workers)
    worker_connections = min(worker_connections, 1000)
    
    # Enable detailed logging for production monitoring
    capture_output = True
    enable_stdio_inheritance = True
    
elif os.getenv("ENVIRONMENT") == "staging":
    # Staging-specific settings
    workers = max(2, workers // 2)
    loglevel = "debug"
    
else:
    # Development fallback
    workers = 1
    reload = True
    loglevel = "debug"

# Resource limits for agent coordination
tmp_upload_dir = "/app/temp/uploads"
worker_tmp_dir = "/app/temp/processing"

# Custom configuration for FlipSync agent architecture
flipsync_config = {
    "agents": {
        "max_concurrent": 35,
        "coordination_timeout": 30,
        "workflow_timeout": 120,
    },
    "performance": {
        "api_response_target": 2.0,
        "concurrent_users_target": 100,
        "agent_response_timeout": 10.0,
    },
    "monitoring": {
        "enable_metrics": True,
        "enable_tracing": True,
        "log_slow_requests": True,
        "performance_alerts": True,
    }
}

# Export configuration for application use
os.environ["FLIPSYNC_PRODUCTION_CONFIG"] = str(flipsync_config)
