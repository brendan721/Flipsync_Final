#!/usr/bin/env python3

"""
FlipSync Application Metrics Collector
=====================================
Comprehensive metrics collection for FlipSync production monitoring
"""

import asyncio
import json
import logging
import os
import psutil
import redis
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import aiohttp
import asyncpg

# Configuration
METRICS_CONFIG = {
    "collection_interval": 60,  # seconds
    "retention_days": 30,
    "redis_host": "127.0.0.1",
    "redis_port": 6379,
    "redis_password": "",  # Set if Redis requires auth
    "db_host": "192.168.110.71",
    "db_port": 5432,
    "db_name": "flipsync_agentic_test",
    "db_user": "postgres",
    "db_password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
    "api_base_url": "https://www.flipsyncai.com/api",
    "metrics_file": "/var/log/flipsync/performance/metrics.json",
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/flipsync/performance/metrics_collector.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("flipsync-metrics")


class MetricsCollector:
    """Comprehensive metrics collection for FlipSync"""

    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.session = None

    async def initialize(self):
        """Initialize connections"""
        try:
            # Initialize Redis connection
            redis_kwargs = {
                "host": METRICS_CONFIG["redis_host"],
                "port": METRICS_CONFIG["redis_port"],
                "decode_responses": True,
            }

            if METRICS_CONFIG["redis_password"]:
                redis_kwargs["password"] = METRICS_CONFIG["redis_password"]

            self.redis_client = redis.Redis(**redis_kwargs)

            # Test Redis connection
            try:
                self.redis_client.ping()
                logger.info("Redis connection established")
            except redis.AuthenticationError:
                logger.warning("Redis authentication failed - continuing without Redis")
                self.redis_client = None
            except Exception as e:
                logger.warning(
                    f"Redis connection failed: {e} - continuing without Redis"
                )
                self.redis_client = None

            # Initialize database connection pool
            self.db_pool = await asyncpg.create_pool(
                host=METRICS_CONFIG["db_host"],
                port=METRICS_CONFIG["db_port"],
                database=METRICS_CONFIG["db_name"],
                user=METRICS_CONFIG["db_user"],
                password=METRICS_CONFIG["db_password"],
                min_size=1,
                max_size=5,
            )
            logger.info("Database connection pool established")

            # Initialize HTTP session
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            )
            logger.info("HTTP session initialized")

        except Exception as e:
            logger.error(f"Failed to initialize connections: {e}")
            raise

    async def collect_system_metrics(self) -> Dict:
        """Collect system-level metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = os.getloadavg()

            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Network metrics
            network = psutil.net_io_counters()

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg_1m": load_avg[0],
                    "load_avg_5m": load_avg[1],
                    "load_avg_15m": load_avg[2],
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                    "free": memory.free,
                },
                "swap": {
                    "total": swap.total,
                    "used": swap.used,
                    "free": swap.free,
                    "percent": swap.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv,
                },
            }
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    async def collect_application_metrics(self) -> Dict:
        """Collect application-specific metrics"""
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "backend": await self._collect_backend_metrics(),
                "database": await self._collect_database_metrics(),
                "redis": await self._collect_redis_metrics(),
                "api": await self._collect_api_metrics(),
            }
            return metrics
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return {}

    async def _collect_backend_metrics(self) -> Dict:
        """Collect backend service metrics"""
        try:
            # Find backend process
            backend_processes = []
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if "uvicorn" in proc.info["name"] and "fs_agt_clean" in " ".join(
                        proc.info["cmdline"]
                    ):
                        backend_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not backend_processes:
                return {"status": "not_running"}

            # Get metrics from the main backend process
            proc = backend_processes[0]

            return {
                "status": "running",
                "pid": proc.pid,
                "memory_percent": proc.memory_percent(),
                "memory_info": proc.memory_info()._asdict(),
                "cpu_percent": proc.cpu_percent(),
                "num_threads": proc.num_threads(),
                "connections": len(proc.connections()),
                "create_time": proc.create_time(),
            }
        except Exception as e:
            logger.error(f"Failed to collect backend metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def _collect_database_metrics(self) -> Dict:
        """Collect database metrics"""
        try:
            if not self.db_pool:
                return {"status": "no_connection"}

            async with self.db_pool.acquire() as conn:
                # Get database size
                db_size = await conn.fetchval(
                    "SELECT pg_size_pretty(pg_database_size($1))",
                    METRICS_CONFIG["db_name"],
                )

                # Get connection count
                connection_count = await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = $1",
                    METRICS_CONFIG["db_name"],
                )

                # Get table statistics
                table_stats = await conn.fetch(
                    """
                    SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                    FROM pg_stat_user_tables
                    ORDER BY n_tup_ins + n_tup_upd + n_tup_del DESC
                    LIMIT 10
                """
                )

                return {
                    "status": "connected",
                    "database_size": db_size,
                    "connection_count": connection_count,
                    "table_stats": [dict(row) for row in table_stats],
                }
        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def _collect_redis_metrics(self) -> Dict:
        """Collect Redis metrics"""
        try:
            if not self.redis_client:
                return {"status": "no_connection"}

            info = self.redis_client.info()

            return {
                "status": "connected",
                "memory_used": info.get("used_memory"),
                "memory_used_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
            }
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def _collect_api_metrics(self) -> Dict:
        """Collect API performance metrics"""
        try:
            if not self.session:
                return {"status": "no_session"}

            # Test API endpoints
            endpoints = ["/", "/health", "/agents/status"]

            results = {}
            for endpoint in endpoints:
                url = f"{METRICS_CONFIG['api_base_url']}{endpoint}"
                start_time = time.time()

                try:
                    async with self.session.get(url) as response:
                        response_time = (time.time() - start_time) * 1000  # ms

                        results[endpoint] = {
                            "status_code": response.status,
                            "response_time_ms": response_time,
                            "content_length": response.headers.get("content-length", 0),
                        }
                except Exception as e:
                    results[endpoint] = {
                        "status_code": 0,
                        "response_time_ms": 0,
                        "error": str(e),
                    }

            return {"status": "tested", "endpoints": results}
        except Exception as e:
            logger.error(f"Failed to collect API metrics: {e}")
            return {"status": "error", "error": str(e)}

    async def store_metrics(self, metrics: Dict):
        """Store metrics to file and Redis"""
        try:
            # Store to file
            os.makedirs(os.path.dirname(METRICS_CONFIG["metrics_file"]), exist_ok=True)

            with open(METRICS_CONFIG["metrics_file"], "a") as f:
                f.write(json.dumps(metrics) + "\n")

            # Store to Redis with TTL
            if self.redis_client:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                key = f"flipsync:metrics:{timestamp}"

                self.redis_client.setex(
                    key,
                    timedelta(days=METRICS_CONFIG["retention_days"]).total_seconds(),
                    json.dumps(metrics),
                )

            logger.info("Metrics stored successfully")

        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")

    async def cleanup_old_metrics(self):
        """Clean up old metrics"""
        try:
            # Clean up Redis keys older than retention period
            if self.redis_client:
                cutoff_date = datetime.utcnow() - timedelta(
                    days=METRICS_CONFIG["retention_days"]
                )
                cutoff_str = cutoff_date.strftime("%Y%m%d_%H%M%S")

                pattern = "flipsync:metrics:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    # Extract timestamp from key
                    timestamp_str = key.split(":")[-1]
                    if timestamp_str < cutoff_str:
                        self.redis_client.delete(key)

            logger.info("Old metrics cleaned up")

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")

    async def collect_and_store(self):
        """Main collection and storage function"""
        try:
            logger.info("Starting metrics collection...")

            # Collect all metrics
            system_metrics = await self.collect_system_metrics()
            app_metrics = await self.collect_application_metrics()

            # Combine metrics
            combined_metrics = {
                "collection_time": datetime.utcnow().isoformat(),
                "system": system_metrics,
                "application": app_metrics,
            }

            # Store metrics
            await self.store_metrics(combined_metrics)

            logger.info("Metrics collection completed successfully")

        except Exception as e:
            logger.error(f"Failed to collect and store metrics: {e}")

    async def close(self):
        """Close all connections"""
        try:
            if self.session:
                await self.session.close()

            if self.db_pool:
                await self.db_pool.close()

            if self.redis_client:
                self.redis_client.close()

            logger.info("All connections closed")

        except Exception as e:
            logger.error(f"Failed to close connections: {e}")


async def main():
    """Main function for metrics collection"""
    collector = MetricsCollector()

    try:
        await collector.initialize()

        # Run collection once
        await collector.collect_and_store()

        # Cleanup old metrics
        await collector.cleanup_old_metrics()

    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return 1

    finally:
        await collector.close()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
