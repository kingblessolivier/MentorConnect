#!/usr/bin/env python
"""
Test script to verify Django application loads with proper translation support
"""
import os
import sys
import django
from pathlib import Path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("✓ Django setup successful!")
    print("✓ No translation/import errors!")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("TRANSLATION CONFIGURATION VERIFICATION")
print("=" * 60)

# Check settings
settings = django.conf.settings
print("\n1. INTERNATIONALIZATION SETTINGS:")
print(f"  ✓ USE_I18N (translations enabled): {settings.USE_I18N}")
print(f"  ✓ USE_L10N (localization enabled): {settings.USE_L10N}")
print(f"  ✓ LANGUAGE_CODE (default): {settings.LANGUAGE_CODE}")
print(f"  ✓ TIME_ZONE: {settings.TIME_ZONE}")
print(f"  ✓ LOCALE_PATHS: {settings.LOCALE_PATHS}")

print("\n2. AVAILABLE LANGUAGES:")
for code, name in settings.LANGUAGES:
    print(f"  ✓ {code}: {name}")

# Check middleware
print("\n3. MIDDLEWARE STATUS:")
middleware = settings.MIDDLEWARE
locale_enabled = False
language_enabled = False

for mid in middleware:
    if 'LocaleMiddleware' in mid:
        print(f"  ✓ {mid} - ENABLED")
        locale_enabled = True
    elif 'LanguageMiddleware' in mid:
        print(f"  ✓ {mid} - ENABLED")
        language_enabled = True

if not locale_enabled:
    print("  ⚠ LocaleMiddleware - DISABLED")
if not language_enabled:
    print("  ⚠ LanguageMiddleware - DISABLED")

# Check translation files
print("\n4. TRANSLATION FILES:")
base_dir = Path(settings.BASE_DIR)
for lang_code, lang_name in settings.LANGUAGES:
    mo_file = base_dir / 'locale' / lang_code / 'LC_MESSAGES' / 'django.mo'
    po_file = base_dir / 'locale' / lang_code / 'LC_MESSAGES' / 'django.po'

    mo_exists = mo_file.exists()
    po_exists = po_file.exists()

    status = "✓" if (mo_exists or po_exists) else "⚠"
    print(f"  {status} {lang_code} ({lang_name}):")
    print(f"      PO: {po_file.name if po_exists else 'missing'}")
    print(f"      MO: {mo_file.name if mo_exists else 'missing'}")

# Check context processors
print("\n5. CONTEXT PROCESSORS:")
template_settings = settings.TEMPLATES[0]
context_processors = template_settings['OPTIONS'].get('context_processors', [])
language_processor_found = any('language_settings' in cp for cp in context_processors)

if language_processor_found:
    print("  ✓ language_settings context processor - ENABLED")
else:
    print("  ⚠ language_settings context processor - DISABLED")

# Test translation activation
print("\n6. TRANSLATION ACTIVATION TEST:")
try:
    from django.utils import translation

    # Test English
    translation.activate('en')
    current = translation.get_language()
    print(f"  ✓ Activated English: {current}")

    # Test Kinyarwanda
    translation.activate('rw')
    current = translation.get_language()
    print(f"  ✓ Activated Kinyarwanda: {current}")

    # Reset to default
    translation.activate(settings.LANGUAGE_CODE)

except Exception as e:
    print(f"  ⚠ Translation activation test failed: {e}")

# Final summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if locale_enabled and language_enabled and language_processor_found and settings.USE_I18N:
    print("✓ All language/translation components are properly configured!")
    print("\nThe application is ready for:")
    print("  • Multi-language support (English & Kinyarwanda)")
    print("  • Automatic language detection")
    print("  • User language preferences")
    print("  • URL-based language routing")
    print("\nNext steps:")
    print("  1. Run: python init_translations.py")
    print("  2. Start the development server")
    print("  3. Test language switching")
else:
    print("⚠ Some components need attention:")
    if not settings.USE_I18N:
        print("  • USE_I18N is disabled")
    if not locale_enabled:
        print("  • LocaleMiddleware is disabled")
    if not language_enabled:
        print("  • LanguageMiddleware is disabled")
    if not language_processor_found:
        print("  • language_settings context processor is disabled")

print("\n" + "=" * 60)

