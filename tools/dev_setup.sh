#!/bin/bash
# FlipSync Development Environment Setup
# Sets up the sophisticated multi-agent development environment

set -e

echo "=== FlipSync Development Environment Setup ==="
echo "Setting up enterprise-grade e-commerce automation platform"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -d "fs_agt_clean" ]; then
    print_error "Not in FlipSync root directory. Please run from /home/brend/Flipsync_Final"
    exit 1
fi

print_status "Found FlipSync codebase"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
required_version="3.9"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    print_status "Python $python_version is compatible"
else
    print_error "Python 3.9+ required, found $python_version"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No virtual environment detected"
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    print_status "Virtual environment created and activated"
else
    print_status "Virtual environment detected"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "No requirements.txt found, installing basic dependencies"
    pip install fastapi uvicorn sqlalchemy pydantic redis asyncpg
fi

# Install development tools
echo "Installing development tools..."
pip install black isort flake8 mypy bandit vulture pre-commit
print_status "Development tools installed"

# Setup pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    print_status "Pre-commit hooks installed"
else
    print_warning "No pre-commit configuration found"
fi

# Check Docker
if command -v docker &> /dev/null; then
    print_status "Docker is available"
    if docker ps &> /dev/null; then
        print_status "Docker daemon is running"
    else
        print_warning "Docker daemon is not running"
    fi
else
    print_warning "Docker not found - required for full development environment"
fi

# Check Flutter (if mobile directory exists)
if [ -d "mobile" ]; then
    if command -v flutter &> /dev/null; then
        flutter_version=$(flutter --version | head -1)
        print_status "Flutter found: $flutter_version"
    else
        print_warning "Flutter not found - required for mobile development"
    fi
fi

# Create development directories
mkdir -p logs
mkdir -p temp
mkdir -p tools
print_status "Development directories created"

# Make tools executable
if [ -d "tools" ]; then
    chmod +x tools/*.py 2>/dev/null || true
    chmod +x tools/*.sh 2>/dev/null || true
    print_status "Tools made executable"
fi

echo ""
echo "=== Development Environment Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Review architecture documentation:"
echo "   - COMPREHENSIVE_ARCHITECTURE_GUIDE.md"
echo "   - DEVELOPER_ARCHITECTURE_PRIMER.md"
echo ""
echo "2. Use development tools:"
echo "   - python tools/agent_debugger.py --list"
echo "   - python validate_architecture_preservation.py"
echo ""
echo "3. Start development services:"
echo "   - docker-compose up (if using Docker)"
echo "   - python fs_agt_clean/main.py (for backend)"
echo ""
echo "4. Run tests:"
echo "   - pytest fs_agt_clean/tests/"
echo ""
print_status "FlipSync development environment ready!"
