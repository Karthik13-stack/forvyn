#!/usr/bin/env python
"""
Simple script to start the LexiLaw backend + frontend server.
Run from anywhere in the project directory.
"""
import os
import sys
import subprocess
from pathlib import Path

# Find the backend directory
current = Path.cwd()
backend_dir = None

# Check if we're already in backend
if (current / "app" / "main.py").exists():
    backend_dir = current
else:
    # Look for it in parent or subdirectories
    for parent in [current, current.parent]:
        for candidate in [parent / "backend", parent]:
            if (candidate / "app" / "main.py").exists():
                backend_dir = candidate
                break
        if backend_dir:
            break

if not backend_dir:
    print("❌ Could not find backend directory with app/main.py")
    print("Please run this script from the project root or backend directory")
    sys.exit(1)

print(f"✅ Found backend at: {backend_dir}")
print(f"\n🚀 Starting LexiLaw Server...")
print(f"   Backend: http://localhost:8000")
print(f"   Frontend: http://localhost:8000")
print(f"\nPress Ctrl+C to stop the server\n")

os.chdir(backend_dir)
subprocess.run([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
