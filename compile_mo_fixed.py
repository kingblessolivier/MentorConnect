#!/usr/bin/env python
"""
Proper MO file compiler
Based on Python's gettext format
"""
import struct
import array
from pathlib import Path

def generate_mo_file(po_content, mo_file_path):
    """Generate a proper MO file from PO content"""

    # Parse the PO file to extract translations
    messages = {}
    lines = po_content.strip().split('\n')

    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    for line in lines:
        line = line.rstrip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue

        # Handle msgid
        if line.startswith('msgid '):
            # Save previous entry
            if current_msgid is not None and current_msgstr is not None:
                if current_msgid:  # Skip empty msgid (header)
                    messages[current_msgid] = current_msgstr

            # Extract the string
            current_msgid = line[6:].strip()
            if current_msgid.startswith('"') and current_msgid.endswith('"'):
                current_msgid = current_msgid[1:-1]
            else:
                current_msgid = ''

            in_msgid = True
            in_msgstr = False

        # Handle msgstr
        elif line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True

            current_msgstr = line[7:].strip()
            if current_msgstr.startswith('"') and current_msgstr.endswith('"'):
                current_msgstr = current_msgstr[1:-1]
            else:
                current_msgstr = ''

        # Handle continuation lines
        elif in_msgid and line.startswith('"'):
            part = line.strip()[1:-1]
            current_msgid += part

        elif in_msgstr and line.startswith('"'):
            part = line.strip()[1:-1]
            current_msgstr += part

    # Add last entry
    if current_msgid is not None and current_msgstr is not None:
        if current_msgid:
            messages[current_msgid] = current_msgstr

    # Build MO file
    # Format: https://www.gnu.org/software/gettext/manual/gettext.html#MO-Files

    # Filter out empty translations
    msgs = {k: v for k, v in messages.items() if k and v}

    if not msgs:
        # Create empty MO file (just header)
        msgs = {'': ''}

    ids = []
    strs = []

    for msgid in sorted(msgs.keys()):
        ids.append(msgid.encode('utf-8'))
        strs.append(msgs[msgid].encode('utf-8'))

    # Generate the MO file
    keyoffset = 7 * 4 + len(ids) * 8
    valueoffset = keyoffset + sum(len(k) + 1 for k in ids)

    koffsets = []
    voffsets = []

    k_offset = keyoffset
    for msgid in sorted(msgs.keys()):
        msgid_bytes = msgid.encode('utf-8')
        koffsets.append((len(msgid_bytes), k_offset))
        k_offset += len(msgid_bytes) + 1

    v_offset = valueoffset
    for msgid in sorted(msgs.keys()):
        msgstr_bytes = msgs[msgid].encode('utf-8')
        voffsets.append((len(msgstr_bytes), v_offset))
        v_offset += len(msgstr_bytes) + 1

    # Write MO file
    with open(mo_file_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('I', 0xde120495))  # Magic number for MO files
        f.write(struct.pack('I', 0))            # Version
        f.write(struct.pack('I', len(ids)))     # Number of strings
        f.write(struct.pack('I', 7*4))          # Offset of hash table for original strings
        f.write(struct.pack('I', 7*4 + len(ids)*8))  # Offset of hash table for translated strings
        f.write(struct.pack('I', 0))            # Size of hashing table (not used)
        f.write(struct.pack('I', 0))            # Offset of hashing table (not used)

        # Write key offsets
        for length, offset in koffsets:
            f.write(struct.pack('II', length, offset))

        # Write value offsets
        for length, offset in voffsets:
            f.write(struct.pack('II', length, offset))

        # Write keys
        for msgid in sorted(msgs.keys()):
            f.write(msgid.encode('utf-8'))
            f.write(b'\x00')

        # Write values
        for msgid in sorted(msgs.keys()):
            f.write(msgs[msgid].encode('utf-8'))
            f.write(b'\x00')

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
            print(f"Compiling {po_file.name}...")
            try:
                with open(po_file, 'r', encoding='utf-8') as f:
                    po_content = f.read()

                generate_mo_file(po_content, str(mo_file))
                print(f"  ✓ Created {mo_file.name}")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
