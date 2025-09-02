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
import urllib3
import json

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

def prompt_for_credentials():
    """Prompt user for credentials and create .env file."""
    print("\n" + "🔐 Credential Configuration")
    print("="*50)
    
    # Initial prompt asking if user wants to configure now
    print("This project uses optional API keys for full functionality:")
    print("• Elasticsearch (ES_API_KEY, ES_ENDPOINT_URL) - for data storage")
    print("• Google Gemini (GEMINI_API_KEY) - for AI content generation")
    print("\nNote: You can load existing data without Gemini API key")
    
    while True:
        configure_now = input("\nWould you like to configure credentials now? (y/n): ").lower().strip()
        if configure_now in ['y', 'yes']:
            break
        elif configure_now in ['n', 'no']:
            print("\n📝 To configure credentials later, set these environment variables:")
            print("   export GEMINI_API_KEY='your_gemini_key_here'")
            print("   export ES_API_KEY='your_elasticsearch_key_here'")  
            print("   export ES_ENDPOINT_URL='https://your-elasticsearch-url:443'")
            print("\n💡 Or create a .env file in the project directory with these variables")
            return None
        else:
            print("Please enter 'y' or 'n'")
    
    credentials = {}
    
    # Elasticsearch Configuration
    print("\n🔍 Elasticsearch Configuration (Optional)")
    print("Used for storing and searching generated financial data")
    
    es_url = input("Elasticsearch URL (press Enter for https://localhost:9200): ").strip()
    if not es_url:
        es_url = "https://localhost:9200"
    credentials['ES_ENDPOINT_URL'] = es_url
    
    es_key = input("Elasticsearch API Key (press Enter to skip): ").strip()
    if es_key:
        credentials['ES_API_KEY'] = es_key
    
    # Gemini Configuration  
    print("\n🤖 Google Gemini Configuration (Optional)")
    print("Used for generating AI-powered financial news and reports")
    print("Note: Not required if you only want to load existing data")
    
    gemini_key = input("Gemini API Key (press Enter to skip): ").strip()
    if gemini_key:
        credentials['GEMINI_API_KEY'] = gemini_key
    
    if credentials:
        return create_env_file(credentials)
    else:
        print("\n⚠️  No credentials provided. You can add them later if needed.")
        return None

def create_env_file(credentials):
    """Create .env file with provided credentials."""
    env_path = Path(".env")
    
    print(f"\n📄 Creating .env file...")
    print("⚠️  Note: Credentials are being written to .env file (excluded from git)")
    
    try:
        with open(env_path, 'w') as f:
            f.write("# Synthetic Financial Data Generator Environment Variables\n")
            f.write("# Generated by setup.py - Edit as needed\n\n")
            
            for key, value in credentials.items():
                f.write(f"{key}={value}\n")
        
        print("✅ .env file created successfully")
        
        # Test connection if Elasticsearch credentials provided
        if 'ES_API_KEY' in credentials and 'ES_ENDPOINT_URL' in credentials:
            test_elasticsearch_connection(credentials['ES_ENDPOINT_URL'], credentials['ES_API_KEY'])
        
        return env_path
        
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return None

def test_elasticsearch_connection(url, api_key):
    """Test Elasticsearch connection."""
    print(f"\n🔗 Testing Elasticsearch connection...")
    
    try:
        # Disable SSL warnings for testing
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        import urllib.request
        
        # Create request with authentication
        request = urllib.request.Request(f"{url}/_cluster/health")
        request.add_header("Authorization", f"ApiKey {api_key}")
        request.add_header("Content-Type", "application/json")
        
        # Test connection with timeout
        response = urllib.request.urlopen(request, timeout=10)
        
        if response.status == 200:
            print("✅ Elasticsearch connection successful!")
        else:
            print(f"⚠️  Elasticsearch responded with status: {response.status}")
            
    except Exception as e:
        print(f"⚠️  Could not connect to Elasticsearch: {e}")
        print("   This is normal if Elasticsearch isn't running yet")

def get_enhanced_next_steps(env_created=False):
    """Get enhanced next steps based on configuration."""
    activation_cmd = get_activation_command()
    
    steps = []
    steps.append("1. Activate the virtual environment:")
    steps.append(f"   {activation_cmd}")
    steps.append("")
    
    if env_created:
        steps.append("2. Verify your configuration:")
        steps.append("   python3 control.py --status")
        steps.append("")
        steps.append("3. Quick start with all features:")
        steps.append("   python3 control.py --quick-start")
        steps.append("")
        steps.append("4. Or run interactive mode:")
        steps.append("   python3 control.py")
    else:
        steps.append("2. Configure credentials (if needed):")
        steps.append("   Edit .env file or set environment variables")
        steps.append("")
        steps.append("3. Check system status:")
        steps.append("   python3 control.py --status")
        steps.append("")
        steps.append("4. Run interactive mode:")
        steps.append("   python3 control.py")
    
    steps.append("")
    steps.append("📚 Common Commands:")
    steps.append("   python3 control.py --help              # Show all options")
    steps.append("   python3 control.py --quick-start       # Generate full dataset")
    steps.append("   python3 control.py --check-indices     # Check Elasticsearch")
    steps.append("   python3 control.py --custom --accounts # Generate accounts only")
    
    return steps

def print_success_message(env_created=False):
    """Print enhanced success message with next steps."""
    print("\n" + "="*60)
    print("🎉 Setup completed successfully!")
    print("="*60)
    
    steps = get_enhanced_next_steps(env_created)
    print("\n📋 Next steps:")
    for step in steps:
        print(step)
    
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
    
    # Configure credentials
    env_created = False
    try:
        env_file = prompt_for_credentials()
        env_created = env_file is not None
    except KeyboardInterrupt:
        print("\n\n🛑 Setup interrupted. You can configure credentials later.")
        env_created = False
    except Exception as e:
        print(f"\n⚠️  Error during credential configuration: {e}")
        print("You can configure credentials later.")
        env_created = False
    
    # Print success message with context-aware next steps
    print_success_message(env_created)

if __name__ == "__main__":
    main()