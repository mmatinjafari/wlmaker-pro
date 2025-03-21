#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Updating wlmaker-pro...${NC}"

# Get the absolute path of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Git is not installed. Please install Git first to update the tool.${NC}"
    exit 1
fi

# Check if the directory is a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}This is not a git repository. Cannot update automatically.${NC}"
    echo -e "${YELLOW}Please re-clone the repository:${NC}"
    echo -e "git clone https://github.com/mmatinjafari/wlmaker-pro.git"
    exit 1
fi

# Pull the latest changes
echo -e "${YELLOW}Pulling the latest changes from the repository...${NC}"
git pull

# Check if Python virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and update dependencies
echo -e "${YELLOW}Updating dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Update the wlmaker command
echo -e "${YELLOW}Updating wlmaker command...${NC}"
if [ -f "/usr/local/bin/wlmaker" ]; then
    sudo bash -c "cat > /usr/local/bin/wlmaker" << EOL
#!/bin/bash
source $SCRIPT_DIR/venv/bin/activate
python3 $SCRIPT_DIR/wlmaker-v02.py "\$@"
EOL
    sudo chmod +x /usr/local/bin/wlmaker
else
    echo -e "${RED}The wlmaker command was not found in /usr/local/bin.${NC}"
    echo -e "${YELLOW}Re-creating the command...${NC}"
    sudo bash -c "cat > /usr/local/bin/wlmaker" << EOL
#!/bin/bash
source $SCRIPT_DIR/venv/bin/activate
python3 $SCRIPT_DIR/wlmaker-v02.py "\$@"
EOL
    sudo chmod +x /usr/local/bin/wlmaker
fi

# Check for external dependencies
echo -e "${YELLOW}Checking external dependencies...${NC}"
if ! command -v katana &> /dev/null; then
    echo -e "${RED}Katana is not installed. Please install it:${NC}"
    echo -e "go install github.com/projectdiscovery/katana/cmd/katana@latest"
fi

if ! command -v waybackurls &> /dev/null; then
    echo -e "${RED}waybackurls is not installed. Please install it:${NC}"
    echo -e "go install github.com/tomnomnom/waybackurls@latest"
fi

echo -e "${GREEN}wlmaker-pro has been successfully updated!${NC}"
echo -e "${YELLOW}You can continue to use the 'wlmaker' command from anywhere.${NC}"
echo -e "${YELLOW}Try 'wlmaker --help' to see usage instructions.${NC}" 