#!/usr/bin/env python
"""
Fix corrupted translation files by creating empty but valid .mo files
"""
import struct
import os

def create_empty_mo_file(path):
    """
    Create a valid empty .mo file (gettext binary format)
    .mo file structure:
    - Magic number (4 bytes)
    - Version (4 bytes)
    - Number of strings (4 bytes)
    - Offset of table with original strings (4 bytes)
    - Offset of table with translated strings (4 bytes)
    - Size of hash table (4 bytes)
    - Offset of hash table (4 bytes)
    """

    # Ensure directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'wb') as f:
        # Magic number for .mo files (little-endian)
        f.write(struct.pack('<I', 0xde120495))
        # Version
        f.write(struct.pack('<I', 0))
        # Number of strings (0 for empty translation)
        f.write(struct.pack('<I', 0))
        # Offset of table with original strings
        f.write(struct.pack('<I', 28))
        # Offset of table with translated strings
        f.write(struct.pack('<I', 28))
        # Size of hash table
        f.write(struct.pack('<I', 0))
        # Offset of hash table
        f.write(struct.pack('<I', 0))

# Create directories if they don't exist
locale_paths = [
    'locale/en/LC_MESSAGES/django.mo',
    'locale/rw/LC_MESSAGES/django.mo',
]

for path in locale_paths:
    create_empty_mo_file(path)
    print(f"Created valid empty .mo file: {path}")

print("Translation files fixed successfully!")
