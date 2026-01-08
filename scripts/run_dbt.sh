#!/bin/bash

# Project Rift - dbt Execution Script
# Runs dbt transformations and logs the output

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DBT_PROJECT_DIR="$PROJECT_ROOT/dbt_project"
LOG_DIR="$PROJECT_ROOT/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/dbt_$TIMESTAMP.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Project Rift - dbt Execution${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Timestamp: $(date)"
echo -e "Log file: $LOG_FILE"
echo -e "${BLUE}========================================${NC}\n"

# Change to dbt project directory
cd "$DBT_PROJECT_DIR"

# Function to run dbt command and log output
run_dbt_command() {
    local command=$1
    local description=$2

    echo -e "${YELLOW}Running: $description${NC}"
    echo "$ dbt $command"

    if dbt "$command" | tee -a "$LOG_FILE"; then
        echo -e "${GREEN}✓ $description completed successfully${NC}\n"
        return 0
    else
        echo -e "${RED}✗ $description failed${NC}\n"
        return 1
    fi
}

# Check dbt installation
if ! command -v dbt &> /dev/null; then
    echo -e "${RED}ERROR: dbt is not installed${NC}"
    echo "Please install dbt-core and dbt-postgres"
    exit 1
fi

# Check database connection
echo -e "${YELLOW}Checking database connection...${NC}"
if run_dbt_command "debug" "Database connection test"; then
    echo -e "${GREEN}✓ Database connection successful${NC}\n"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "Please check your database credentials in .env"
    exit 1
fi

# Run dbt deps (install packages if needed)
if [ -f "packages.yml" ]; then
    echo -e "${YELLOW}Installing dbt packages...${NC}"
    run_dbt_command "deps" "Package installation"
fi

# Run dbt seed (load seed data if exists)
if [ -d "seeds" ] && [ "$(ls -A seeds)" ]; then
    echo -e "${YELLOW}Loading seed data...${NC}"
    run_dbt_command "seed" "Seed data loading"
fi

# Run dbt models
echo -e "${YELLOW}Running dbt models...${NC}"
if run_dbt_command "run" "Model execution"; then
    echo -e "${GREEN}✓ All models built successfully${NC}\n"
else
    echo -e "${RED}✗ Model execution failed${NC}"
    exit 1
fi

# Run dbt tests
echo -e "${YELLOW}Running dbt tests...${NC}"
if run_dbt_command "test" "Data quality tests"; then
    echo -e "${GREEN}✓ All tests passed${NC}\n"
else
    echo -e "${YELLOW}⚠ Some tests failed - check log for details${NC}\n"
fi

# Generate documentation (optional)
if [ "$1" == "--docs" ]; then
    echo -e "${YELLOW}Generating documentation...${NC}"
    run_dbt_command "docs generate" "Documentation generation"
    echo -e "${GREEN}✓ Documentation generated${NC}"
    echo -e "${BLUE}Run 'dbt docs serve' to view documentation${NC}\n"
fi

# Print summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}dbt Execution Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Log file: $LOG_FILE"
echo -e "Timestamp: $(date)"
echo -e "${BLUE}========================================${NC}"

# Return to original directory
cd "$PROJECT_ROOT"
