"""
Calendar utilities - ICS file generation for session export
"""

from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import uuid


def generate_ics_for_session(session, user_role='participant'):
    """Generate ICS content for a single session"""
    # Prefer `start`/`end` fields; fallback to legacy `scheduled_time`/`duration`
    dt_start = getattr(session, 'start', None) or getattr(session, 'scheduled_time', None)
    dt_end = getattr(session, 'end', None)
    if not dt_end and dt_start:
        # fallback duration 60 minutes
        dt_end = dt_start + timedelta(minutes=getattr(session, 'duration', 60) or 60)

    # Format for ICS (UTC)
    def format_dt(dt):
        return dt.strftime('%Y%m%dT%H%M%SZ')

    location = ''
    if session.session_type == 'physical' and session.address:
        location = session.address
    elif session.meeting_link:
        location = session.meeting_link

    desc = session.description or ''
    if session.session_type == 'physical':
        desc = f"In-Person Session\n{location}\n\n{desc}".strip()
    elif session.meeting_link:
        desc = f"Join: {session.meeting_link}\n\n{desc}".strip()

    ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MentorConnect//Sessions//EN
BEGIN:VEVENT
UID:{uuid.uuid4()}@mentorconnect
DTSTAMP:{format_dt(timezone.now())}
DTSTART:{format_dt(dt_start)}
DTEND:{format_dt(dt_end)}
SUMMARY:{session.title}
DESCRIPTION:{desc.replace(chr(10), '\\n')}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""

    return ics


def session_ics_response(session, filename='session.ics'):
    """Return HttpResponse with ICS file for a session"""
    ics_content = generate_ics_for_session(session)
    response = HttpResponse(ics_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
