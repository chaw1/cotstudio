#!/usr/bin/env python3
"""
Test alembic configuration
"""
from alembic.config import Config
from alembic import command
import os

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "alembic.ini")

print(f"Config path: {config_path}")
print(f"Config exists: {os.path.exists(config_path)}")

if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        content = f.read()
        print("Config content:")
        print(content[:500])

try:
    # Create alembic config
    alembic_cfg = Config(config_path)
    
    # Check if script_location is set
    script_location = alembic_cfg.get_main_option("script_location")
    print(f"Script location: {script_location}")
    
    # Try to get current revision
    command.current(alembic_cfg)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()