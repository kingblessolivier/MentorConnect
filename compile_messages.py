#!/usr/bin/env python
"""
Script to compile .po files to .mo files without gettext
"""
import os
import polib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOCALE_DIR = BASE_DIR / 'locale'

def compile_po_to_mo():
    """Compile all .po files to .mo files"""

    for lang_dir in LOCALE_DIR.iterdir():
        if not lang_dir.is_dir() or lang_dir.name.startswith('.'):
            continue

        lc_messages_dir = lang_dir / 'LC_MESSAGES'
        if not lc_messages_dir.exists():
            continue

        for po_file in lc_messages_dir.glob('*.po'):
            print(f"Compiling {po_file}...")
            try:
                po = polib.pofile(str(po_file))
                mo_file = po_file.with_suffix('.mo')
                po.save_as_mofile(str(mo_file))
                print(f"  ✓ Created {mo_file}")
            except Exception as e:
                print(f"  ✗ Error: {e}")

if __name__ == '__main__':
    compile_po_to_mo()
    print("\nDone!")
