#!/bin/bash
###############################################################################
# Road Painting Robot - Installation Script
# Sets up the robot controller on Raspberry Pi
###############################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored messages
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_header() { echo -e "\n${BLUE}========================================${NC}\n${BLUE}  $1${NC}\n${BLUE}========================================${NC}\n"; }

# Check if script is run with sudo
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root/sudo"
    print_info "The script will request sudo when needed"
    exit 1
fi

print_header "Road Painting Robot - Installation"

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    RPI_MODEL=$(cat /proc/device-tree/model)
    print_success "Detected: $RPI_MODEL"
else
    print_warning "Not running on Raspberry Pi hardware"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled"
        exit 0
    fi
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"
print_info "Project directory: $PROJECT_ROOT"

# Step 1: Check Python version
print_header "Step 1: Checking Python"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Found $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    exit 1
fi

# Step 2: Create virtual environment
print_header "Step 2: Setting up Virtual Environment"
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        print_info "Removed old virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Step 3: Upgrade pip
print_header "Step 3: Upgrading pip"
pip install --upgrade pip
print_success "pip upgraded"

# Step 4: Install dependencies
print_header "Step 4: Installing Dependencies"
if [ -f "requirements.txt" ]; then
    print_info "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    print_success "All dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Step 5: Setup environment file
print_header "Step 5: Setting up Environment"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_success "Environment file created"
        print_warning "Please edit .env to configure your robot:"
        print_info "  nano .env"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_success "Environment file .env already exists"
fi

# Step 6: Setup user permissions
print_header "Step 6: Setting up Permissions"
print_info "Adding user to gpio and dialout groups..."

CURRENT_USER=$(whoami)
GROUPS_NEEDED=0

if ! groups $CURRENT_USER | grep -q "gpio"; then
    sudo usermod -a -G gpio $CURRENT_USER
    print_success "Added $CURRENT_USER to gpio group"
    GROUPS_NEEDED=1
else
    print_info "User already in gpio group"
fi

if ! groups $CURRENT_USER | grep -q "dialout"; then
    sudo usermod -a -G dialout $CURRENT_USER
    print_success "Added $CURRENT_USER to dialout group"
    GROUPS_NEEDED=1
else
    print_info "User already in dialout group"
fi

if [ $GROUPS_NEEDED -eq 1 ]; then
    print_warning "Group changes require logout/login to take effect"
fi

# Step 7: UART configuration
print_header "Step 7: UART Configuration"
print_info "Checking UART status..."

if [ -e /dev/serial0 ]; then
    print_success "UART serial port /dev/serial0 exists"
else
    print_warning "UART serial port /dev/serial0 not found"
    print_info "You may need to enable UART:"
    print_info "  sudo raspi-config"
    print_info "  → Interface Options → Serial Port"
    print_info "  → Login shell: NO, Serial hardware: YES"
fi

# Step 8: Create data directory
print_header "Step 8: Setting up Data Directory"
if [ ! -d "data" ]; then
    mkdir -p data
    print_success "Created data directory"
else
    print_info "Data directory already exists"
fi

# Step 9: Verify setup
print_header "Step 9: Verifying Installation"
print_info "Running verification script..."
if python verify_setup.py; then
    print_success "Setup verification passed!"
else
    print_warning "Some verification checks failed"
    print_info "Review the messages above and fix any issues"
fi

# Step 10: Download road data (optional)
print_header "Step 10: Road Data"
if [ ! -f "data/roads.geojson" ]; then
    print_warning "No road data found in data/roads.geojson"
    print_info "You can download road data using:"
    print_info "  source venv/bin/activate"
    print_info "  python tools/download_roads.py --lat YOUR_LAT --lon YOUR_LON --radius 500 --output data/roads.geojson"
else
    print_success "Road data file found"
fi

# Installation complete
print_header "Installation Complete!"

echo -e "${GREEN}Next Steps:${NC}\n"
echo "1. Configure your robot settings:"
echo "   ${BLUE}nano .env${NC}"
echo ""
echo "2. Download road data for your location:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo "   ${BLUE}python tools/download_roads.py --lat YOUR_LAT --lon YOUR_LON --radius 500 --output data/roads.geojson${NC}"
echo ""
echo "3. Test hardware components:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo "   ${BLUE}python tools/test_hardware.py${NC}"
echo ""
echo "4. Run the robot controller:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo "   ${BLUE}python main.py --simulate${NC}  # Test without hardware"
echo "   ${BLUE}python main.py${NC}              # Run with hardware"
echo ""
echo "5. (Optional) Set up auto-start on boot:"
echo "   ${BLUE}sudo cp systemd/road-robot.service /etc/systemd/system/${NC}"
echo "   ${BLUE}sudo systemctl enable road-robot.service${NC}"
echo "   ${BLUE}sudo systemctl start road-robot.service${NC}"
echo ""

if [ $GROUPS_NEEDED -eq 1 ]; then
    print_warning "IMPORTANT: You must logout and login again for group changes to take effect!"
fi

print_success "Installation script finished!"
echo ""
