#!/usr/bin/env python3
"""
Setup script for Synthetic Financial Data Generator

This script creates a virtual environment, activates it, and installs all required dependencies.
Run with: python3 setup.py
"""

import subprocess
import sys
import os
import venv
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def create_venv():
    """Create virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("🔄 Virtual environment already exists, skipping creation...")
        return True
    
    print("🏗️  Creating virtual environment...")
    try:
        venv.create("venv", with_pip=True)
        print("✅ Virtual environment created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating virtual environment: {e}")
        return False

def get_activation_command():
    """Get the appropriate activation command based on the operating system."""
    if sys.platform == "win32":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def get_python_executable():
    """Get the appropriate Python executable path for the virtual environment."""
    if sys.platform == "win32":
        return "venv\\Scripts\\python"
    else:
        return "venv/bin/python"

def install_requirements():
    """Install requirements using pip in the virtual environment."""
    python_exe = get_python_executable()
    
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        return False
    
    # Use the virtual environment's Python to install requirements
    command = f"{python_exe} -m pip install -r requirements.txt"
    return run_command(command, "Installing requirements")

def upgrade_pip():
    """Upgrade pip in the virtual environment."""
    python_exe = get_python_executable()
    command = f"{python_exe} -m pip install --upgrade pip"
    return run_command(command, "Upgrading pip")

def print_success_message():
    """Print success message with next steps."""
    activation_cmd = get_activation_command()
    
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    print("\n📋 Next steps:")
    print(f"1. Activate the virtual environment:")
    print(f"   {activation_cmd}")
    print("\n2. Run the interactive control script:")
    print("   python3 control.py")
    print("\n3. Or check the system status:")
    print("   python3 control.py --status")
    print("\n📚 For more options, see:")
    print("   python3 control.py --help")
    print("\n💡 Remember to activate the virtual environment whenever you work on this project!")
    print("="*60)

def main():
    """Main setup function."""
    print("🚀 Setting up Synthetic Financial Data Generator")
    print("="*50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Upgrade pip
    if not upgrade_pip():
        print("⚠️  Warning: Failed to upgrade pip, continuing...")
    
    # Install requirements
    if not install_requirements():
        print("❌ Failed to install requirements!")
        sys.exit(1)
    
    # Print success message
    print_success_message()

if __name__ == "__main__":
    main()