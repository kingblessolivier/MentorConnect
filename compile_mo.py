#!/usr/bin/env python
"""
Alternative message compiler using only Python standard library
Converts .po files to .mo files
"""
import struct
import array
from pathlib import Path

def generate(po_file_path, mo_file_path):
    """Convert a .po file to .mo file"""

    messages = {}
    translations = {}

    with open(po_file_path, 'r', encoding='utf-8') as f:
        current_msg = None
        current_str = None

        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            if line.startswith('msgid '):
                if current_msg is not None and current_str is not None:
                    messages[current_msg] = current_str
                current_msg = line[6:].strip('"')
                current_str = ''
            elif line.startswith('msgstr '):
                current_str = line[7:].strip('"')
            elif current_str is not None and line.startswith('"'):
                current_str += line.strip('"')

        # Add last entry
        if current_msg is not None and current_str is not None:
            messages[current_msg] = current_str

    # Build translations dict (skip empty msgid and msgstr)
    for msgid, msgstr in messages.items():
        if msgid and msgstr:
            translations[msgid] = msgstr

    # Generate .mo file
    keys = sorted(translations.keys())
    offsets = []
    ids = b''
    strs = b''

    for key in keys:
        value = translations[key]

        key_bytes = key.encode('utf-8')
        value_bytes = value.encode('utf-8')

        offsets.append((len(ids), len(key_bytes), len(strs), len(value_bytes)))
        ids += key_bytes + b'\x00'
        strs += value_bytes + b'\x00'

    # Generate hash table
    keyoffset = 7 * 4 + 16 * len(keys)
    valueoffset = keyoffset + len(ids)

    koffsets = []
    voffsets = []

    for o1, l1, o2, l2 in offsets:
        koffsets.append((l1, keyoffset + o1))
        voffsets.append((l2, valueoffset + o2))

    # Write .mo file
    with open(mo_file_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('Iiiiiii', 0xde120495, 0, len(keys), 7*4, 7*4+len(keys)*8, 0, 0))

        for l, o in koffsets:
            f.write(struct.pack('ii', l, o))
        for l, o in voffsets:
            f.write(struct.pack('ii', l, o))

        f.write(ids)
        f.write(strs)

if __name__ == '__main__':
    base_dir = Path(__file__).resolve().parent
    locale_dir = base_dir / 'locale'

    for lang_dir in locale_dir.iterdir():
        if not lang_dir.is_dir() or lang_dir.name.startswith('.'):
            continue

        lc_messages_dir = lang_dir / 'LC_MESSAGES'
        if not lc_messages_dir.exists():
            continue

        for po_file in lc_messages_dir.glob('*.po'):
            mo_file = po_file.with_suffix('.mo')
            print(f"Compiling {po_file.name} -> {mo_file.name}")
            try:
                generate(str(po_file), str(mo_file))
                print(f"  ✓ Success")
            except Exception as e:
                print(f"  ✗ Error: {e}")
