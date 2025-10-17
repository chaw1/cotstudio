#!/usr/bin/env python3
"""
COT Studio MVP - Password Hash Generator
Generates bcrypt hash for new passwords
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from passlib.context import CryptContext
except ImportError:
    print("Error: passlib not installed")
    print("Please install it with: pip install passlib[bcrypt]")
    sys.exit(1)

def generate_password_hash(password: str) -> str:
    """Generate bcrypt hash for password"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)

def verify_password_hash(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.verify(password, hashed)

def main():
    if len(sys.argv) != 2:
        print("Usage: python generate-password-hash.py <password>")
        print("Example: python generate-password-hash.py 971028")
        sys.exit(1)
    
    password = sys.argv[1]
    
    print(f"Generating bcrypt hash for password: {password}")
    print("-" * 50)
    
    # Generate hash
    hashed = generate_password_hash(password)
    print(f"Password: {password}")
    print(f"Hash: {hashed}")
    
    # Verify the hash works
    if verify_password_hash(password, hashed):
        print("✅ Hash verification successful")
    else:
        print("❌ Hash verification failed")
    
    print("-" * 50)
    print("Copy this hash to your seed data file:")
    print(f"'hashed_password': '{hashed}',")

if __name__ == "__main__":
    main()