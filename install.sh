#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Installing wlmaker-pro...${NC}"

# Check if Python3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python3 is not installed. Please install Python3 first.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

# Activate virtual environment and install requirements
echo -e "${YELLOW}Installing dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt

# Create the wlmaker command
echo -e "${YELLOW}Creating wlmaker command...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "#!/bin/bash" > /usr/local/bin/wlmaker
echo "source $SCRIPT_DIR/venv/bin/activate" >> /usr/local/bin/wlmaker
echo "python3 $SCRIPT_DIR/wlmaker-v02.py \"\$@\"" >> /usr/local/bin/wlmaker
chmod +x /usr/local/bin/wlmaker

echo -e "${GREEN}Installation completed successfully!${NC}"
echo -e "${YELLOW}You can now use 'wlmaker' command from anywhere.${NC}"
echo -e "${YELLOW}Try 'wlmaker --help' to see usage instructions.${NC}" 