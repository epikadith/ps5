#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ANSI Color Codes for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}      PHANTOM CONSENSUS - STARTUP SCRIPT        ${NC}"
echo -e "${BLUE}================================================${NC}"

echo -e "\n${YELLOW}[1/3] Running Python Strategic Engine...${NC}"
# Run the core python consensus engine
if uv run python consensus_engine.py data/raw output/final_agreement.json; then
    echo -e "${GREEN}✓ Engine executed successfully. Outputs generated.${NC}"
else
    echo -e "${RED}✗ Engine failed to execute. Check errors above.${NC}"
    exit 1
fi

echo -e "\n${YELLOW}[2/3] Installing Frontend Dependencies (if missing)...${NC}"
cd dashboard
# Install npm dependencies silently if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    npm install
fi
echo -e "${GREEN}✓ Dependencies verified.${NC}"

echo -e "\n${YELLOW}[3/3] Launching React Dashboard...${NC}"
echo -e "The dashboard will be available at: ${GREEN}http://localhost:5173${NC}"
echo -e "(Press Ctrl+C to stop the server)\n"

# Start the Vite development server
npm run dev
