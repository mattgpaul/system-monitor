#!/usr/bin/env python
"""Test script for server polling task."""

import sys
import os
from pathlib import Path

# Get the project root and add server directory to path
project_root = Path(__file__).resolve().parent.parent
server_path = project_root / "app" / "server"
sys.path.insert(0, str(server_path))

# Set up Django environment
os.environ.setdefault('ENV', 'dev')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server_config.settings')

# Load environment first
from dotenv import load_dotenv
env_file = project_root / 'dev.env'
if env_file.exists():
    load_dotenv(env_file)

# Initialize Django
import django
django.setup()

from monitoring.tasks import poll_agent_telemetry

def main():
    print("Testing server polling task...")
    try:
        result = poll_agent_telemetry()
        print("Polling result:", result)
        
        if result.get('status') == 'success':
            print("SUCCESS: Agent connection working")
            return 0
        else:
            print("FAILED: Agent connection failed")
            return 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())