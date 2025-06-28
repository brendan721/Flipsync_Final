#!/bin/bash
# FlipSync Bashrc Integration for AI Agents
# AGENT_CONTEXT: Automatic terminal setup for new AI agent sessions
# AGENT_PRIORITY: Zero-configuration productivity environment
# AGENT_PATTERN: Seamless onboarding with immediate development capability

# FlipSync AI Agent Environment Setup
# This script is automatically sourced for new AI agent terminals

# Prevent multiple sourcing
if [[ "${FLIPSYNC_BASHRC_LOADED}" == "true" ]]; then
    return 0
fi

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[1;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m'

# Core FlipSync Environment Variables
export FLIPSYNC_ROOT="/root/projects/flipsync"
export FLIPSYNC_FS_CLEAN="$FLIPSYNC_ROOT/fs_clean"
export FLIPSYNC_BACKEND="$FLIPSYNC_FS_CLEAN/fs_agt_clean"
export FLIPSYNC_MOBILE="$FLIPSYNC_FS_CLEAN/mobile/flutter_app"
export FLIPSYNC_MEMORY="$FLIPSYNC_FS_CLEAN/memory-bank"

# Database Configuration
export FLIPSYNC_DB_URL="postgresql://postgres:postgres@localhost:1432/flipsync"
export FLIPSYNC_AI_DB_URL="postgresql://postgres:postgres@localhost:1432/flipsync_ai_tools"
export FLIPSYNC_SQLITE_DB="$FLIPSYNC_FS_CLEAN/flipsync_ai_tools.db"

# Development Environment
export PYTHONPATH="$FLIPSYNC_FS_CLEAN:$PYTHONPATH"
export NODE_ENV="development"
export FLASK_ENV="development"

# Navigation Aliases
alias cdfs="cd $FLIPSYNC_FS_CLEAN"
alias cdbe="cd $FLIPSYNC_BACKEND"
alias cdapi="cd $FLIPSYNC_BACKEND/api"
alias cdauth="cd $FLIPSYNC_BACKEND/api/routes"
alias cdmodels="cd $FLIPSYNC_BACKEND/database/models"
alias cdcore="cd $FLIPSYNC_BACKEND/core"
alias cdtests="cd $FLIPSYNC_BACKEND/tests"
alias cdmobile="cd $FLIPSYNC_MOBILE"
alias cdmem="cd $FLIPSYNC_MEMORY"

# Development Aliases
alias runapi="cd $FLIPSYNC_BACKEND && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
alias testapi="cd $FLIPSYNC_BACKEND && python -m pytest tests/ -v"
alias testcov="cd $FLIPSYNC_BACKEND && python -m pytest tests/ --cov=app --cov-report=html --cov-report=term"
alias testwatch="cd $FLIPSYNC_BACKEND && python -m pytest tests/ -v --tb=short -x"
alias lintapi="cd $FLIPSYNC_BACKEND && python -m flake8 app/"
alias typecheck="cd $FLIPSYNC_BACKEND && python -m mypy app/"
alias formatcode="cd $FLIPSYNC_BACKEND && python -m black app/ tests/"

# Database Aliases
alias dbconnect="docker exec -it flipsync-postgres psql -U postgres -d flipsync"
alias aidbconnect="docker exec -it flipsync-postgres psql -U postgres -d flipsync_ai_tools"
alias dbstatus="docker exec flipsync-postgres psql -U postgres -c '\l'"
alias dbtables="docker exec flipsync-postgres psql -U postgres -d flipsync -c '\dt'"
alias aidbtables="docker exec flipsync-postgres psql -U postgres -d flipsync_ai_tools -c '\dt'"
alias dbbackup="docker exec flipsync-postgres pg_dump -U postgres flipsync > flipsync_backup_\$(date +%Y%m%d_%H%M%S).sql"

# Docker Aliases
alias dps="docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
alias dlogs="docker logs -f"
alias dstats="docker stats --no-stream"
alias dclean="docker system prune -f"

# Git Aliases
alias gst="git status"
alias glog="git log --oneline -10"
alias glogfull="git log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit"
alias gdiff="git diff"
alias gadd="git add"
alias gcommit="git commit -m"
alias gpush="git push"
alias gpull="git pull"
alias gbranch="git branch -a"
alias gcheckout="git checkout"

# FlipSync-specific functions
flipsync_status() {
    echo -e "${CYAN}🎯 FlipSync Development Status${NC}"
    echo -e "${YELLOW}================================${NC}"
    
    # Project status
    echo -e "${GREEN}📊 Project:${NC} FlipSync Multi-Agent E-Commerce Platform"
    echo -e "${GREEN}📈 Progress:${NC} 85% Complete | Authentication: 90%"
    echo -e "${GREEN}🛠️ Stack:${NC} FastAPI + SQLAlchemy + PostgreSQL + Flutter"
    echo ""
    
    # Database status
    echo -e "${CYAN}💾 Database Status:${NC}"
    if docker ps | grep -q flipsync-postgres; then
        echo -e "${GREEN}  ✓ PostgreSQL container running${NC}"
        local app_tables=$(docker exec flipsync-postgres psql -U postgres -d flipsync -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
        local ai_tables=$(docker exec flipsync-postgres psql -U postgres -d flipsync_ai_tools -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs)
        echo -e "${GREEN}  ✓ App database: ${app_tables} tables${NC}"
        echo -e "${GREEN}  ✓ AI tools database: ${ai_tables} tables${NC}"
    else
        echo -e "${RED}  ✗ PostgreSQL container not running${NC}"
    fi
    
    # Current directory context
    echo ""
    echo -e "${CYAN}📁 Current Context:${NC}"
    echo -e "${GREEN}  📍 Location:${NC} $(pwd)"
    if [[ $(pwd) == *"flipsync"* ]]; then
        echo -e "${GREEN}  ✓ In FlipSync project${NC}"
    else
        echo -e "${YELLOW}  ⚠ Outside FlipSync project${NC}"
    fi
    
    # Quick actions
    echo ""
    echo -e "${CYAN}⚡ Quick Actions:${NC}"
    echo -e "${YELLOW}  cdauth${NC}    - Go to authentication routes"
    echo -e "${YELLOW}  runapi${NC}    - Start FastAPI development server"
    echo -e "${YELLOW}  testcov${NC}   - Run tests with coverage report"
    echo -e "${YELLOW}  dbconnect${NC} - Connect to application database"
}

flipsync_help() {
    echo -e "${CYAN}🚀 FlipSync AI Agent Commands${NC}"
    echo -e "${YELLOW}==============================${NC}"
    echo ""
    echo -e "${GREEN}Navigation:${NC}"
    echo -e "  ${YELLOW}cdfs${NC}       - Go to FlipSync root"
    echo -e "  ${YELLOW}cdbe${NC}       - Go to backend"
    echo -e "  ${YELLOW}cdauth${NC}     - Go to auth routes"
    echo -e "  ${YELLOW}cdmodels${NC}   - Go to database models"
    echo -e "  ${YELLOW}cdcore${NC}     - Go to core modules"
    echo -e "  ${YELLOW}cdmem${NC}      - Go to memory bank"
    echo ""
    echo -e "${GREEN}Development:${NC}"
    echo -e "  ${YELLOW}runapi${NC}     - Start FastAPI server"
    echo -e "  ${YELLOW}testapi${NC}    - Run all tests"
    echo -e "  ${YELLOW}testcov${NC}    - Run tests with coverage"
    echo -e "  ${YELLOW}testwatch${NC}  - Run tests in watch mode"
    echo -e "  ${YELLOW}lintapi${NC}    - Lint the API code"
    echo -e "  ${YELLOW}typecheck${NC}  - Run type checking"
    echo -e "  ${YELLOW}formatcode${NC} - Format code with black"
    echo ""
    echo -e "${GREEN}Database:${NC}"
    echo -e "  ${YELLOW}dbconnect${NC}    - Connect to app database"
    echo -e "  ${YELLOW}aidbconnect${NC}  - Connect to AI tools database"
    echo -e "  ${YELLOW}dbtables${NC}     - List app database tables"
    echo -e "  ${YELLOW}aidbtables${NC}   - List AI tools database tables"
    echo ""
    echo -e "${GREEN}Utilities:${NC}"
    echo -e "  ${YELLOW}flipsync_status${NC} - Show project status"
    echo -e "  ${YELLOW}flipsync_help${NC}   - Show this help"
    echo -e "  ${YELLOW}dps${NC}             - Show Docker containers"
    echo ""
}

# Custom prompt for FlipSync development
flipsync_prompt() {
    local git_branch=""
    if git rev-parse --git-dir > /dev/null 2>&1; then
        git_branch=" ($(git branch --show-current))"
    fi
    
    local current_dir=$(basename "$(pwd)")
    echo -e "${CYAN}[FlipSync:${current_dir}${git_branch}]${NC} "
}

# Set custom prompt
export PS1='$(flipsync_prompt)$ '

# Welcome message for new terminals
flipsync_welcome() {
    if [[ "${FLIPSYNC_WELCOME_SHOWN}" != "true" ]]; then
        echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${PURPLE}║${NC}              ${CYAN}FlipSync AI Agent Terminal${NC}              ${PURPLE}║${NC}"
        echo -e "${PURPLE}║${NC}           ${GREEN}Ready for immediate development${NC}           ${PURPLE}║${NC}"
        echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN}💡 Quick Start:${NC}"
        echo -e "  • Type ${YELLOW}flipsync_status${NC} for project overview"
        echo -e "  • Type ${YELLOW}flipsync_help${NC} for available commands"
        echo -e "  • Type ${YELLOW}cdauth${NC} to go to authentication routes"
        echo ""
        export FLIPSYNC_WELCOME_SHOWN="true"
    fi
}

# Auto-navigate to FlipSync project if not already there
if [[ $(pwd) != *"flipsync"* ]] && [[ -d "$FLIPSYNC_FS_CLEAN" ]]; then
    cd "$FLIPSYNC_FS_CLEAN"
fi

# Mark as loaded
export FLIPSYNC_BASHRC_LOADED="true"

# Show welcome message
flipsync_welcome
