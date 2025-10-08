#!/usr/bin/env python3
"""
Generate Secure Secrets for Environment Configuration
Creates cryptographically secure secret keys for JWT, Flask sessions, etc.
"""

import secrets
import sys


def generate_secret_key(length: int = 64) -> str:
    """Generate a URL-safe secret key"""
    return secrets.token_urlsafe(length)


def generate_hex_key(length: int = 32) -> str:
    """Generate a hexadecimal secret key"""
    return secrets.token_hex(length)


def main():
    print("=" * 80)
    print("Secure Secret Key Generator")
    print("=" * 80)
    print()

    print("Copy these values to your .env file:")
    print()

    print("# Flask Secret Key (for session management)")
    print(f"SECRET_KEY={generate_secret_key(64)}")
    print()

    print("# JWT Secret Key (for token signing)")
    print(f"JWT_SECRET_KEY={generate_secret_key(64)}")
    print()

    print("# Additional Keys (if needed)")
    print(f"# Backup Key 1: {generate_secret_key(64)}")
    print(f"# Backup Key 2: {generate_secret_key(64)}")
    print()

    print("=" * 80)
    print("⚠️  SECURITY NOTES:")
    print("  1. Never commit these keys to version control")
    print("  2. Use different keys for each environment")
    print("  3. Rotate keys periodically")
    print("  4. Store production keys in a secrets manager")
    print("=" * 80)


if __name__ == "__main__":
    main()
