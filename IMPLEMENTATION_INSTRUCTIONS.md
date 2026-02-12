# MentorConnect - New Features Implementation Instructions

This document describes the newly implemented features and how to run them.

## Features Implemented

### 1. Guest Student Applications (No Account Required)
- **App**: `applications`
- **Flow**: Students without accounts can apply to mentors via a public form
- **URLs**: 
  - `/applications/apply/` - General application form
  - `/applications/apply/<mentor_id>/` - Apply to specific mentor (from mentor profile)
  - `/applications/apply/success/` - Thank you page
- **Mentor Dashboard**: New "Guest Applications" section with approve/reject and feedback
- **Admin Dashboard**: Full applications list with approve/reject

### 2. Email Onboarding After Approval
- When mentor approves: System sends email with secure invitation token link
- Token valid for 7 days
- **URL**: `/applications/invite/<token>/` - Invitation-based registration
- Flow: Apply → Mentor approves → Email sent → Applicant clicks link → Creates account → Auto-linked to application → Mentor feedback shown on student dashboard

### 3. Physical / In-Person Sessions
- **Extended Session model** with:
  - `session_type` (online / physical)
  - `location_name`, `address`, `latitude`, `longitude`
  - `student_attended`, `mentor_attended`
- **Session detail page**: Map preview (Leaflet/OpenStreetMap) for physical sessions with coordinates
- Mentors can set location via Django admin or when creating sessions

### 4. Shared Calendar Sync
- **ICS Export**: Each session has "Add to Calendar" button
- **URL**: `/sessions/<pk>/calendar/` - Downloads .ics file
- Adds session to student/mentor calendar (Google Calendar, Outlook, etc.)
- Shows date, time, session type, location (if physical)

### 5. Admin Full Tracking
- **Applications**: `/dashboard/admin/applications/` - List, filter, approve/reject
- **Sessions**: Enhanced with filters (date range, mentor, student, session type), physical location column, attendance tracking
- Admin sidebar: New "Applications" link

## Files Created/Modified

### New Files
- `applications/` - Entire new app (models, views, forms, urls, admin, services, templates)
- `applications/migrations/0001_initial.py`
- `sessions_app/migrations/0004_session_session_type_and_more.py`
- `sessions_app/calendar_utils.py`
- `templates/applications/` - apply.html, apply_success.html, mentor_applications.html, mentor_application_detail.html, register_with_token.html, invitation_expired.html
- `templates/sessions_app/detail.html` - Session detail with map
- `templates/dashboard/admin_applications.html`, `admin_application_detail.html`

### Modified Files
- `config/settings.py` - Added applications app, DEFAULT_FROM_EMAIL
- `config/urls.py` - Added applications routes
- `sessions_app/models.py` - Session type, location, attendance fields
- `sessions_app/views.py` - session_ics_export view
- `sessions_app/urls.py` - session_ics route
- `dashboard/views.py` - Admin applications, enhanced session filters
- `dashboard/urls.py` - Admin application routes
- `templates/components/dashboard_sidebar.html` - Guest Applications (mentor), Applications (admin)
- `templates/profiles/mentor_detail.html` - "Apply as Guest" button for non-logged-in users
- `templates/dashboard/admin_sessions.html` - Enhanced filters, type, location columns
- `templates/sessions_app/list.html` - Session type badge, Add to Calendar
- `templates/dashboard/mentor_dashboard.html` - Guest applications section
- `templates/dashboard/student_dashboard.html` - Mentor feedback from linked application
- `core/context_processors.py` - pending_requests_count, guest_applications_pending_count

## Run Instructions

### 1. Apply Migrations
```bash
python manage.py migrate
```

### 2. (Optional) Create Superuser
```bash
python manage.py createsuperuser
```

### 3. Run Development Server
```bash
python manage.py runserver
```

### 4. Email Configuration
- **Development**: Emails print to console (default `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`)
- **Production**: Set in `.env`:
  - `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`
  - `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`
  - `DEFAULT_FROM_EMAIL`

### 5. Site Domain (for invitation links)
- For production, add `SITE_DOMAIN = 'yourdomain.com'` to settings or set in environment
- Default uses ALLOWED_HOSTS[0]

## Key URLs

| Feature | URL |
|---------|-----|
| Guest Apply | /applications/apply/ |
| Apply to Mentor | /applications/apply/<mentor_id>/ |
| Invitation Register | /applications/invite/<token>/ |
| Mentor Applications | /applications/mentor/applications/ (login required) |
| Admin Applications | /dashboard/admin/applications/ (admin) |
| Session Detail (with map) | /sessions/<pk>/ |
| Session ICS Export | /sessions/<pk>/calendar/ |

## UI Requirements Met
- Clean, minimal, professional design
- Application forms styled
- Map preview card (Leaflet)
- Calendar UI (ICS download)
- Status badges (pending/approved/rejected)
- Smooth transitions (existing CSS)
