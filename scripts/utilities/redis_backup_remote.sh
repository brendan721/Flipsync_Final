#!/bin/bash
# Execute this on the production droplet to backup Redis data
echo "📊 Backing up Redis data..."
redis-cli -p 6379 -a "FlipSync2024SecureRedis!" --rdb /tmp/redis_production_backup.rdb
redis-cli -p 6379 -a "FlipSync2024SecureRedis!" KEYS "*ebay*" > /tmp/ebay_keys.txt
redis-cli -p 6379 -a "FlipSync2024SecureRedis!" KEYS "*token*" > /tmp/token_keys.txt
redis-cli -p 6379 -a "FlipSync2024SecureRedis!" KEYS "*session*" > /tmp/session_keys.txt

# Export key values
while IFS= read -r key; do
    if [ ! -z "$key" ]; then
        value=$(redis-cli -p 6379 -a "FlipSync2024SecureRedis!" GET "$key")
        echo "$key=$value" >> /tmp/ebay_tokens_backup.txt
    fi
done < /tmp/ebay_keys.txt

echo "✅ Redis backup completed"
echo "Files created:"
ls -la /tmp/redis_production_backup.rdb /tmp/*_keys.txt /tmp/ebay_tokens_backup.txt
