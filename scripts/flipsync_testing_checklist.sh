#!/bin/bash

echo "📋 FlipSync Testing Pre-Flight Checklist"
echo "========================================"

# Check Flutter environment
echo "1. Checking Flutter environment..."
flutter doctor --verbose | grep -E "(Flutter|Web|Chrome)" | head -10

# Check dependencies
echo ""
echo "2. Checking dependencies..."
cd /home/brend/Flipsync_Final/mobile
flutter pub deps | grep -E "(MISSING|ERROR)" || echo "   ✅ All dependencies OK"

# Check web build capability
echo ""
echo "3. Testing web build..."
flutter build web --debug > /dev/null 2>&1 && echo "   ✅ Web build successful" || echo "   ❌ Web build failed"

# Check API connectivity (if backend is running)
echo ""
echo "4. Checking API connectivity..."
curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "   ✅ API accessible" || echo "   ⚠️  API not accessible (this is OK for web-only testing)"

# Check if PostgreSQL is available
echo ""
echo "5. Checking database connectivity..."
pg_isready -h localhost -p 5432 > /dev/null 2>&1 && echo "   ✅ PostgreSQL accessible" || echo "   ⚠️  PostgreSQL not accessible (install with: sudo apt install postgresql)"

# Check if Redis is available
echo ""
echo "6. Checking Redis connectivity..."
redis-cli ping > /dev/null 2>&1 && echo "   ✅ Redis accessible" || echo "   ⚠️  Redis not accessible (install with: sudo apt install redis-server)"

echo ""
echo "🚀 Ready for testing! Next steps:"
echo "   1. Run: ./start_flipsync_web_testing.sh"
echo "   2. Access: http://localhost:8080"
echo "   3. AI can test the web application directly"
