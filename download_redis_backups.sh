#!/bin/bash
# Execute this script on your local machine to download Redis backups

echo "🔽 Downloading Redis backup files from production droplet..."

# Download all Redis backup files
scp root@174.138.77.110:/tmp/flipsync_redis_backup/redis_production_backup.rdb ./flipsync_production_backup_20250804_201444/
scp root@174.138.77.110:/tmp/flipsync_redis_backup/ebay_tokens_backup.txt ./flipsync_production_backup_20250804_201444/
scp root@174.138.77.110:/tmp/flipsync_redis_backup/ebay_keys.txt ./flipsync_production_backup_20250804_201444/
scp root@174.138.77.110:/tmp/flipsync_redis_backup/token_keys.txt ./flipsync_production_backup_20250804_201444/
scp root@174.138.77.110:/tmp/flipsync_redis_backup/session_keys.txt ./flipsync_production_backup_20250804_201444/

echo "✅ Redis backup files downloaded!"
echo ""
echo "🔍 Verifying all backup files are present:"
ls -la flipsync_production_backup_20250804_201444/

echo ""
echo "📊 Backup verification checklist:"
echo "- [ ] Database backup: flipsync_production_database.sql ($(du -h flipsync_production_backup_20250804_201444/flipsync_production_database.sql 2>/dev/null | cut -f1 || echo 'MISSING'))"
echo "- [ ] Database schema: flipsync_database_schema.sql ($(du -h flipsync_production_backup_20250804_201444/flipsync_database_schema.sql 2>/dev/null | cut -f1 || echo 'MISSING'))"
echo "- [ ] Redis RDB: redis_production_backup.rdb ($(du -h flipsync_production_backup_20250804_201444/redis_production_backup.rdb 2>/dev/null | cut -f1 || echo 'MISSING'))"
echo "- [ ] eBay tokens: ebay_tokens_backup.txt ($(wc -l < flipsync_production_backup_20250804_201444/ebay_tokens_backup.txt 2>/dev/null || echo '0') tokens)"

if [ -f "flipsync_production_backup_20250804_201444/flipsync_production_database.sql" ] && 
   [ -f "flipsync_production_backup_20250804_201444/redis_production_backup.rdb" ] && 
   [ -f "flipsync_production_backup_20250804_201444/ebay_tokens_backup.txt" ]; then
    echo ""
    echo "✅ ALL BACKUPS VERIFIED - READY FOR CLEAN DEPLOYMENT!"
    echo "🚀 Proceed to execute: ./deploy_clean_droplet.sh"
else
    echo ""
    echo "❌ BACKUP VERIFICATION FAILED - DO NOT PROCEED WITH DEPLOYMENT"
    echo "Missing backup files detected. Ensure all backups are complete before proceeding."
fi
