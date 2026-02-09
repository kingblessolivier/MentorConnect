# Language & Translation Setup for MentorConnect

## Overview
This document explains the language/translation system for MentorConnect, which supports English (en) and Kinyarwanda (rw).

## Configuration Status

### ✓ Enabled Components
- **USE_I18N = True**: Internationalization is fully enabled
- **LocaleMiddleware**: Handles automatic language detection and URL routing
- **LanguageMiddleware**: Custom middleware for language persistence in sessions/cookies
- **Language Context Processor**: Provides translations to all templates
- **Fallback Handling**: Graceful error handling for missing translation files

### Files Modified
1. **config/settings.py**
   - Enabled `USE_I18N = True`
   - Added `LocaleMiddleware` to MIDDLEWARE
   - Added `LanguageMiddleware` to MIDDLEWARE
   - Configured LANGUAGE_CODE and LANGUAGES

2. **core/middleware.py**
   - Added error handling to LanguageMiddleware
   - Gracefully falls back if translation activation fails

3. **core/context_processors.py**
   - Enhanced language_settings() with try-catch blocks
   - Provides translation dictionaries to templates

## Translation Files Structure

```
locale/
├── en/
│   └── LC_MESSAGES/
│       ├── django.po    (Portable Object file - human readable)
│       └── django.mo    (Machine Object file - compiled)
└── rw/
    └── LC_MESSAGES/
        ├── django.po
        └── django.mo
```

## How Translations Work

### 1. PO Files (django.po)
These are human-readable translation files with this format:
```
msgid "Original English text"
msgstr "Translated text"
```

### 2. MO Files (django.mo)
These are compiled binary files that Django uses at runtime for performance.

## Setup Instructions

### Option 1: Automatic Setup (Recommended)
Run the translation initialization script:

```bash
python init_translations.py
```

This will:
- Create locale directory structure
- Generate PO files with basic translations
- Compile PO files to MO files
- Verify Django configuration

### Option 2: Manual Django Compilation
If you prefer to use Django's built-in tools:

```bash
# Extract translatable strings from code
python manage.py makemessages -l en
python manage.py makemessages -l rw

# Compile translations
python manage.py compilemessages
```

### Option 3: Using Existing Setup Script
```bash
python setup_translations.py
```

## Using Translations in Templates

### Method 1: Using trans template tag
```html
{% load i18n %}
<h1>{% trans "Welcome" %}</h1>
<p>{% trans "Login" %}</p>
```

### Method 2: Using context dictionary
```html
<h1>{{ t.welcome }}</h1>
<p>{{ t.login }}</p>
```

## Using Translations in Python Code

```python
from django.utils.translation import gettext as _

message = _("Welcome to MentorConnect")
```

## Language Switching

### URL-Based (via LocaleMiddleware)
```
/en/dashboard/    - English version
/rw/dashboard/    - Kinyarwanda version
```

### Session-Based (via LanguageMiddleware)
Set in session:
```python
request.session['django_language'] = 'rw'
```

### Cookie-Based
Set cookies:
```python
response.set_cookie('site_language', 'rw', max_age=365*24*60*60)
```

## Available Translations

### Built-in Context Translations
The system provides these translations in `core.context_processors.language_settings()`:

**English (en)**
- home, about, mentors, login, signup, logout, dashboard, profile, settings, search, feed, chat, notifications, sessions, welcome, find_mentor, become_mentor, get_started, learn_more, contact_us, follow, unfollow, book_session, send_message, view_profile, edit_profile, save, cancel, delete, confirm, loading, no_results, error, success, warning, info

**Kinyarwanda (rw)**
- ahabanza, turi aha, abakozi, injira, andika, sohoka, dashibodi, umwirondoro, igenamiterere, teka, inyemezo, ikiganiro, impabura, igihe, murakaza neza, gafata umukozi, biba umukozi, tangira, menya byinshi, twandikire, kurikira, kureka gukurikira, gufata igihe, ohereza ubutumwa, reba umwirondoro, hindura umwirondoro, bika, hagarika, siba, emeza, gutegereza, nta bisubizo, ikosa, byagenze neza, umuburo, amakuru

## Troubleshooting

### Missing Translation Files
If you see warnings about missing .mo files:
1. Run `python init_translations.py`
2. Or manually run `python manage.py compilemessages`

### Translations Not Showing
1. Clear browser cache (cookies)
2. Verify `USE_I18N = True` in settings
3. Check that .mo files exist in locale/*/LC_MESSAGES/
4. Restart the Django development server

### Language Not Switching
1. Verify LANGUAGES in settings.py has both 'en' and 'rw'
2. Check middleware order in settings.py (LocaleMiddleware should come after SessionMiddleware)
3. Verify language parameter is valid

### Database Not Ready
The middleware includes error handling for when the database isn't ready. If you see errors during initial setup:
1. Run migrations: `python manage.py migrate`
2. Restart the server

## Best Practices

1. **Always use translation strings** in code:
   ```python
   # Good
   message = _("Welcome")
   
   # Bad
   message = "Welcome"
   ```

2. **Mark strings for translation** in templates:
   ```html
   <!-- Good -->
   <h1>{% trans "Welcome" %}</h1>
   
   <!-- Bad -->
   <h1>Welcome</h1>
   ```

3. **Extract and update strings regularly**:
   ```bash
   python manage.py makemessages --all
   python manage.py compilemessages
   ```

4. **Add missing translations** by editing django.po files:
   - Edit `locale/en/LC_MESSAGES/django.po`
   - Edit `locale/rw/LC_MESSAGES/django.po`
   - Run compilemessages

## Adding New Languages

To add a new language (e.g., French - fr):

1. Create directory structure:
   ```bash
   mkdir -p locale/fr/LC_MESSAGES
   ```

2. Add language to LANGUAGES in settings.py:
   ```python
   LANGUAGES = [
       ('en', 'English'),
       ('rw', 'Kinyarwanda'),
       ('fr', 'Français'),
   ]
   ```

3. Generate translation files:
   ```bash
   python manage.py makemessages -l fr
   ```

4. Edit `locale/fr/LC_MESSAGES/django.po` with French translations

5. Compile:
   ```bash
   python manage.py compilemessages
   ```

## Error Recovery

The system is designed to fail gracefully:
- If translation files are missing, defaults to English
- If translation activation fails, continues without translations
- Middleware catches exceptions and falls back safely

## Testing

To verify translations are working:

```bash
python test_django_setup.py
```

This will check:
- Django setup loads without errors
- Settings are configured correctly
- Middleware is enabled
- No translation errors occur

## Performance Notes

- MO files are compiled and cached by Django for performance
- Translation lookups are fast (compiled binary format)
- Minimal overhead for language switching
- Cookies cache language preference to avoid repeated lookups

## Resources

- [Django Internationalization Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [GNU gettext Format](https://www.gnu.org/software/gettext/manual/gettext.html)
- [Kinyarwanda Language Guide](https://en.wikipedia.org/wiki/Kinyarwanda)

## Support

For issues with translations:
1. Check this README
2. Review error messages in Django logs
3. Verify file permissions on locale directory
4. Ensure encoding is UTF-8
5. Check for special characters in PO files

---
Last Updated: February 9, 2026
