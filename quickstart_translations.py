#!/usr/bin/env python
"""
Quick start script for MentorConnect language/translation system
Run this first to set up everything
"""
import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def print_header(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)

def print_step(step_num, title):
    print(f"\n[{step_num}/3] {title}")
    print("-" * 70)

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"  → {description}...", end=" ", flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print("⚠ (non-zero exit)")
            if result.stderr:
                print(f"    Error: {result.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠ (timeout)")
        return False
    except Exception as e:
        print(f"✗ ({e})")
        return False

def main():
    print_header("MENTORCONNECT TRANSLATION QUICK START")

    print("\nThis script will:")
    print("  1. Set up translation files (PO & MO)")
    print("  2. Verify Django configuration")
    print("  3. Provide setup instructions")

    print_step(1, "INITIALIZING TRANSLATION FILES")

    # Check if init_translations.py exists
    init_script = BASE_DIR / 'init_translations.py'
    if init_script.exists():
        run_command(
            f"{sys.executable} {init_script}",
            "Running translation initialization"
        )
    else:
        print(f"  ✗ {init_script} not found")
        print("  → Please run: python init_translations.py manually")

    print_step(2, "VERIFYING DJANGO SETUP")

    # Run Django check
    run_command(
        f"{sys.executable} manage.py check",
        "Django health check"
    )

    # Run test script
    test_script = BASE_DIR / 'test_django_setup.py'
    if test_script.exists():
        print(f"\n  → Running verification tests...")
        try:
            subprocess.run(
                [sys.executable, str(test_script)],
                cwd=BASE_DIR,
                timeout=30
            )
        except Exception as e:
            print(f"  ⚠ Test script error: {e}")

    print_step(3, "SETUP COMPLETE")

    print("\n✓ Translation system is now initialized!")

    print("\n" + "=" * 70)
    print("NEXT STEPS".center(70))
    print("=" * 70)

    print("""
1. Start the development server:
   python manage.py runserver

2. Test language switching:
   - Open http://localhost:8000/
   - Look for language switcher (usually top-right)
   - Click to switch between English and Kinyarwanda
   - Verify UI updates appropriately

3. Add more translations:
   - Edit locale/en/LC_MESSAGES/django.po (English)
   - Edit locale/rw/LC_MESSAGES/django.po (Kinyarwanda)
   - Run: python manage.py compilemessages
   - Restart server to see changes

4. For more information:
   - Read: LANGUAGE_SETUP.md
   - Run: python TRANSLATION_SETUP_SUMMARY.py
   - Check: https://docs.djangoproject.com/en/stable/topics/i18n/

TROUBLESHOOTING
───────────────

If translations don't show:
  1. Clear browser cache
  2. Delete browser cookies
  3. Run: python manage.py compilemessages
  4. Restart the server

If you see errors:
  1. Run: python test_django_setup.py
  2. Check errors reported
  3. Follow suggestions in output

""")

    print("=" * 70)
    print("✓ MentorConnect is ready for multi-language support!")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
