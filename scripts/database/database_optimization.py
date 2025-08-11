#!/usr/bin/env python3

"""
FlipSync Database Optimization Script
====================================
Comprehensive PostgreSQL optimization for FlipSync production
"""

import asyncio
import asyncpg
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Configuration
DB_CONFIG = {
    "host": "192.168.110.71",
    "port": 5432,
    "database": "flipsync_agentic_test",
    "user": "postgres",
    "password": "FlipSync_DB_Prod_2024_Secure_Key_9x7z",
    "min_size": 5,
    "max_size": 20,
    "command_timeout": 60,
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/var/log/flipsync/performance/db_optimization.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("flipsync-db-optimizer")


class DatabaseOptimizer:
    """Comprehensive database optimization for FlipSync"""

    def __init__(self):
        self.pool = None
        self.optimization_results = {}

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=DB_CONFIG["host"],
                port=DB_CONFIG["port"],
                database=DB_CONFIG["database"],
                user=DB_CONFIG["user"],
                password=DB_CONFIG["password"],
                min_size=DB_CONFIG["min_size"],
                max_size=DB_CONFIG["max_size"],
                command_timeout=DB_CONFIG["command_timeout"],
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def analyze_database_performance(self) -> Dict:
        """Analyze current database performance"""
        logger.info("Analyzing database performance...")

        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "database_size": await self._get_database_size(),
            "connection_stats": await self._get_connection_stats(),
            "table_stats": await self._get_table_statistics(),
            "index_usage": await self._get_index_usage(),
            "slow_queries": await self._get_slow_queries(),
            "cache_hit_ratio": await self._get_cache_hit_ratio(),
            "lock_stats": await self._get_lock_statistics(),
        }

        return analysis

    async def _get_database_size(self) -> Dict:
        """Get database size information"""
        try:
            async with self.pool.acquire() as conn:
                # Database size
                db_size = await conn.fetchval(
                    "SELECT pg_size_pretty(pg_database_size($1))", DB_CONFIG["database"]
                )

                # Table sizes
                table_sizes = await conn.fetch(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY size_bytes DESC
                    LIMIT 10
                """
                )

                return {
                    "total_size": db_size,
                    "largest_tables": [dict(row) for row in table_sizes],
                }
        except Exception as e:
            logger.error(f"Failed to get database size: {e}")
            return {}

    async def _get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetch(
                    """
                    SELECT 
                        state,
                        COUNT(*) as count
                    FROM pg_stat_activity 
                    WHERE datname = $1
                    GROUP BY state
                """,
                    DB_CONFIG["database"],
                )

                max_connections = await conn.fetchval("SHOW max_connections")

                return {
                    "connection_states": {row["state"]: row["count"] for row in stats},
                    "max_connections": int(max_connections),
                    "pool_size": f"{DB_CONFIG['min_size']}-{DB_CONFIG['max_size']}",
                }
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}

    async def _get_table_statistics(self) -> List[Dict]:
        """Get table usage statistics"""
        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetch(
                    """
                    SELECT 
                        schemaname,
                        relname as tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup
                    FROM pg_stat_user_tables
                    ORDER BY seq_scan + idx_scan DESC
                    LIMIT 20
                """
                )

                return [dict(row) for row in stats]
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return []

    async def _get_index_usage(self) -> List[Dict]:
        """Get index usage statistics"""
        try:
            async with self.pool.acquire() as conn:
                # Index usage stats
                index_stats = await conn.fetch(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                    LIMIT 20
                """
                )

                # Unused indexes
                unused_indexes = await conn.fetch(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size
                    FROM pg_stat_user_indexes
                    WHERE idx_scan = 0
                    AND schemaname NOT IN ('information_schema', 'pg_catalog')
                """
                )

                return {
                    "most_used": [dict(row) for row in index_stats],
                    "unused": [dict(row) for row in unused_indexes],
                }
        except Exception as e:
            logger.error(f"Failed to get index usage: {e}")
            return {}

    async def _get_slow_queries(self) -> List[Dict]:
        """Get slow query information"""
        try:
            async with self.pool.acquire() as conn:
                # Check if pg_stat_statements is available
                extension_exists = await conn.fetchval(
                    """
                    SELECT EXISTS(
                        SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                    )
                """
                )

                if not extension_exists:
                    return {"error": "pg_stat_statements extension not available"}

                slow_queries = await conn.fetch(
                    """
                    SELECT 
                        query,
                        calls,
                        total_time,
                        mean_time,
                        rows
                    FROM pg_stat_statements
                    WHERE mean_time > 100  -- queries taking more than 100ms on average
                    ORDER BY mean_time DESC
                    LIMIT 10
                """
                )

                return [dict(row) for row in slow_queries]
        except Exception as e:
            logger.warning(f"Could not get slow queries: {e}")
            return {"error": str(e)}

    async def _get_cache_hit_ratio(self) -> Dict:
        """Get cache hit ratio"""
        try:
            async with self.pool.acquire() as conn:
                # Buffer cache hit ratio
                cache_hit = await conn.fetchrow(
                    """
                    SELECT 
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit) as heap_hit,
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as ratio
                    FROM pg_statio_user_tables
                """
                )

                # Index cache hit ratio
                index_hit = await conn.fetchrow(
                    """
                    SELECT 
                        sum(idx_blks_read) as idx_read,
                        sum(idx_blks_hit) as idx_hit,
                        sum(idx_blks_hit) / (sum(idx_blks_hit) + sum(idx_blks_read)) * 100 as ratio
                    FROM pg_statio_user_indexes
                """
                )

                return {
                    "buffer_cache_hit_ratio": (
                        float(cache_hit["ratio"]) if cache_hit["ratio"] else 0
                    ),
                    "index_cache_hit_ratio": (
                        float(index_hit["ratio"]) if index_hit["ratio"] else 0
                    ),
                }
        except Exception as e:
            logger.error(f"Failed to get cache hit ratio: {e}")
            return {}

    async def _get_lock_statistics(self) -> Dict:
        """Get lock statistics"""
        try:
            async with self.pool.acquire() as conn:
                locks = await conn.fetch(
                    """
                    SELECT 
                        mode,
                        COUNT(*) as count
                    FROM pg_locks
                    WHERE database = (SELECT oid FROM pg_database WHERE datname = $1)
                    GROUP BY mode
                """,
                    DB_CONFIG["database"],
                )

                return {row["mode"]: row["count"] for row in locks}
        except Exception as e:
            logger.error(f"Failed to get lock statistics: {e}")
            return {}

    async def optimize_database(self) -> Dict:
        """Apply database optimizations"""
        logger.info("Applying database optimizations...")

        optimizations = {
            "timestamp": datetime.utcnow().isoformat(),
            "vacuum_analyze": await self._run_vacuum_analyze(),
            "reindex": await self._run_reindex(),
            "update_statistics": await self._update_statistics(),
            "connection_pool": await self._optimize_connection_pool(),
        }

        return optimizations

    async def _run_vacuum_analyze(self) -> Dict:
        """Run VACUUM ANALYZE on all tables"""
        try:
            async with self.pool.acquire() as conn:
                # Get all user tables
                tables = await conn.fetch(
                    """
                    SELECT schemaname, tablename 
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                """
                )

                results = []
                for table in tables:
                    table_name = f"{table['schemaname']}.{table['tablename']}"
                    start_time = time.time()

                    try:
                        await conn.execute(f"VACUUM ANALYZE {table_name}")
                        duration = time.time() - start_time
                        results.append(
                            {
                                "table": table_name,
                                "status": "success",
                                "duration": duration,
                            }
                        )
                        logger.info(
                            f"VACUUM ANALYZE completed for {table_name} in {duration:.2f}s"
                        )
                    except Exception as e:
                        results.append(
                            {"table": table_name, "status": "error", "error": str(e)}
                        )
                        logger.error(f"VACUUM ANALYZE failed for {table_name}: {e}")

                return {
                    "status": "completed",
                    "tables_processed": len(results),
                    "results": results,
                }
        except Exception as e:
            logger.error(f"Failed to run VACUUM ANALYZE: {e}")
            return {"status": "error", "error": str(e)}

    async def _run_reindex(self) -> Dict:
        """Reindex tables if needed"""
        try:
            async with self.pool.acquire() as conn:
                # Get indexes that might benefit from reindexing
                indexes = await conn.fetch(
                    """
                    SELECT 
                        schemaname,
                        tablename,
                        indexname
                    FROM pg_stat_user_indexes
                    WHERE idx_scan > 1000  -- Only reindex frequently used indexes
                    ORDER BY idx_scan DESC
                    LIMIT 10
                """
                )

                results = []
                for index in indexes:
                    index_name = f"{index['schemaname']}.{index['indexname']}"
                    start_time = time.time()

                    try:
                        await conn.execute(f"REINDEX INDEX {index_name}")
                        duration = time.time() - start_time
                        results.append(
                            {
                                "index": index_name,
                                "status": "success",
                                "duration": duration,
                            }
                        )
                        logger.info(
                            f"REINDEX completed for {index_name} in {duration:.2f}s"
                        )
                    except Exception as e:
                        results.append(
                            {"index": index_name, "status": "error", "error": str(e)}
                        )
                        logger.error(f"REINDEX failed for {index_name}: {e}")

                return {
                    "status": "completed",
                    "indexes_processed": len(results),
                    "results": results,
                }
        except Exception as e:
            logger.error(f"Failed to run REINDEX: {e}")
            return {"status": "error", "error": str(e)}

    async def _update_statistics(self) -> Dict:
        """Update table statistics"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("ANALYZE")
                logger.info("Database statistics updated")
                return {"status": "success"}
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
            return {"status": "error", "error": str(e)}

    async def _optimize_connection_pool(self) -> Dict:
        """Optimize connection pool settings"""
        try:
            # Current pool stats
            pool_stats = {
                "min_size": self.pool._minsize,
                "max_size": self.pool._maxsize,
                "current_size": len(self.pool._holders),
                "available_connections": len(
                    [h for h in self.pool._holders if h._con is not None]
                ),
            }

            logger.info(f"Connection pool stats: {pool_stats}")
            return {"status": "analyzed", "stats": pool_stats}
        except Exception as e:
            logger.error(f"Failed to optimize connection pool: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_optimization_report(self) -> Dict:
        """Generate comprehensive optimization report"""
        logger.info("Generating optimization report...")

        # Run analysis
        analysis = await self.analyze_database_performance()

        # Apply optimizations
        optimizations = await self.optimize_database()

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)

        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": analysis,
            "optimizations": optimizations,
            "recommendations": recommendations,
        }

        # Save report
        report_file = f"/var/log/flipsync/performance/db_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Optimization report saved to {report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

        return report

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Cache hit ratio recommendations
        cache_ratio = analysis.get("cache_hit_ratio", {})
        buffer_ratio = cache_ratio.get("buffer_cache_hit_ratio", 0)
        if buffer_ratio < 95:
            recommendations.append(
                f"Buffer cache hit ratio is {buffer_ratio:.1f}% - consider increasing shared_buffers"
            )

        # Connection recommendations
        conn_stats = analysis.get("connection_stats", {})
        if "connection_states" in conn_stats:
            active_conns = conn_stats["connection_states"].get("active", 0)
            if active_conns > DB_CONFIG["max_size"] * 0.8:
                recommendations.append(
                    "High connection usage - consider increasing connection pool size"
                )

        # Index recommendations
        index_usage = analysis.get("index_usage", {})
        if isinstance(index_usage, dict) and "unused" in index_usage:
            unused_count = len(index_usage["unused"])
            if unused_count > 0:
                recommendations.append(
                    f"Found {unused_count} unused indexes - consider dropping them"
                )

        # Table size recommendations
        db_size = analysis.get("database_size", {})
        if "largest_tables" in db_size:
            for table in db_size["largest_tables"][:3]:  # Top 3 largest tables
                if table["size_bytes"] > 1000000000:  # > 1GB
                    recommendations.append(
                        f"Large table {table['tablename']} ({table['size']}) - consider partitioning"
                    )

        return recommendations

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")


async def main():
    """Main optimization function"""
    optimizer = DatabaseOptimizer()

    try:
        await optimizer.initialize()
        report = await optimizer.generate_optimization_report()

        # Display summary
        print("\n" + "=" * 50)
        print("DATABASE OPTIMIZATION SUMMARY")
        print("=" * 50)

        if "recommendations" in report:
            print(f"\n📋 Recommendations ({len(report['recommendations'])}):")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"   {i}. {rec}")

        if "optimizations" in report:
            print(f"\n🔧 Optimizations Applied:")
            for key, value in report["optimizations"].items():
                if isinstance(value, dict) and "status" in value:
                    status = "✅" if value["status"] == "success" else "❌"
                    print(f"   {status} {key.replace('_', ' ').title()}")

        print(f"\n📊 Full report saved to optimization log")

        return 0

    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return 1

    finally:
        await optimizer.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
