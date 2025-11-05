#!/usr/bin/env python3
"""
Setup script for SkylitAI Desktop UI
"""
import os
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False
    return True

def setup_env_file():
    """Setup environment file"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.template'):
            print("Creating .env file from template...")
            with open('.env.template', 'r') as template:
                content = template.read()
            with open('.env', 'w') as env_file:
                env_file.write(content)
            print("✅ .env file created!")
            print("⚠️  Please edit .env file with your Schwab API credentials")
        else:
            print("❌ .env.template not found")
            return False
    else:
        print("✅ .env file already exists")
    return True

def main():
    print("🚀 Setting up SkylitAI Desktop UI...")
    
    # Install requirements
    if not install_requirements():
        return
    
    # Setup environment
    if not setup_env_file():
        return
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your Schwab API credentials")
    print("2. Run: streamlit run app.py")
    print("\nFor help with Schwab API setup, visit:")
    print("https://developer.schwab.com/")

if __name__ == "__main__":
    main()
