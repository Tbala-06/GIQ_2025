#!/bin/bash
# Installation script for PS3 Motor Controller on Raspberry Pi 5
# This script installs all necessary dependencies

echo "=================================================="
echo "PS3 Motor Controller - Raspberry Pi 5 Setup"
echo "=================================================="
echo ""

# Detect Raspberry Pi model
if grep -q "Raspberry Pi 5" /proc/cpuinfo; then
    echo "✅ Detected: Raspberry Pi 5"
    RPI_VERSION=5
elif grep -q "Raspberry Pi 4" /proc/cpuinfo; then
    echo "✅ Detected: Raspberry Pi 4"
    RPI_VERSION=4
elif grep -q "Raspberry Pi 3" /proc/cpuinfo; then
    echo "✅ Detected: Raspberry Pi 3"
    RPI_VERSION=3
else
    echo "⚠️  Warning: Could not detect Raspberry Pi model"
    echo "   Assuming Raspberry Pi 5..."
    RPI_VERSION=5
fi

echo ""
echo "Updating system packages..."
sudo apt-get update

echo ""
echo "Installing Python dependencies..."

# Install pygame for PS3 controller support
echo "  → Installing pygame..."
sudo apt-get install -y python3-pygame

# Install GPIO library based on RPi version
if [ "$RPI_VERSION" -eq 5 ]; then
    echo "  → Installing gpiod (RPi 5 native)..."
    sudo apt-get install -y python3-libgpiod
else
    echo "  → Installing RPi.GPIO (RPi 4/3)..."
    sudo apt-get install -y python3-rpi.gpio
fi

# Optional: Install bluetooth tools for wireless PS3 controller
echo ""
read -p "Install Bluetooth tools for wireless PS3 controller? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  → Installing Bluetooth tools..."
    sudo apt-get install -y bluetooth bluez bluez-tools
fi

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. Connect your L298N motor driver to GPIO pins"
echo "  2. Connect PS3 controller via USB"
echo "  3. Run: python3 ps3_motor_controller.py"
echo ""
echo "For full setup guide, see: PS3_MOTOR_SETUP.md"
echo ""
