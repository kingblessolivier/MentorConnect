#!/usr/bin/env python
"""
Setup translation files for MentorConnect
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Create locale directories if they don't exist
locale_dir = BASE_DIR / 'locale'
for lang in ['en', 'rw']:
    lc_messages = locale_dir / lang / 'LC_MESSAGES'
    lc_messages.mkdir(parents=True, exist_ok=True)

# English translation file
en_po_content = """# English translations for MentorConnect
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: en\\n"

msgid "Home"
msgstr "Home"

msgid "Login"
msgstr "Login"

msgid "Dashboard"
msgstr "Dashboard"

msgid "Logout"
msgstr "Logout"

msgid "Profile"
msgstr "Profile"

msgid "Settings"
msgstr "Settings"
"""

# Kinyarwanda translation file
rw_po_content = """# Kinyarwanda translations for MentorConnect
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: rw\\n"

msgid "Home"
msgstr "Ahabanza"

msgid "Login"
msgstr "Injira"

msgid "Dashboard"
msgstr "Dashibodi"

msgid "Logout"
msgstr "Sohoka"

msgid "Profile"
msgstr "Umwirondoro"

msgid "Settings"
msgstr "Igenamiterere"
"""

# Write PO files
with open(locale_dir / 'en' / 'LC_MESSAGES' / 'django.po', 'w', encoding='utf-8') as f:
    f.write(en_po_content)

with open(locale_dir / 'rw' / 'LC_MESSAGES' / 'django.po', 'w', encoding='utf-8') as f:
    f.write(rw_po_content)

# Create minimal MO files (just empty headers to avoid errors)
mo_header = b'\xde\x12\x04\x95\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

with open(locale_dir / 'en' / 'LC_MESSAGES' / 'django.mo', 'wb') as f:
    f.write(mo_header)

with open(locale_dir / 'rw' / 'LC_MESSAGES' / 'django.mo', 'wb') as f:
    f.write(mo_header)

print("✓ Translation files created successfully")
print("✓ Locale structure:")
print(f"  - {locale_dir}/en/LC_MESSAGES/django.po")
print(f"  - {locale_dir}/en/LC_MESSAGES/django.mo")
print(f"  - {locale_dir}/rw/LC_MESSAGES/django.po")
print(f"  - {locale_dir}/rw/LC_MESSAGES/django.mo")
