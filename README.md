# MentorConnect - Student-Mentor Mentorship Platform

A fully-featured, production-ready mentorship platform built with Django, Django Templates, and Django Channels.

## Features

### User Roles
- **Students**: Find mentors, request mentorship, book sessions, track progress
- **Mentors**: Manage availability, approve requests, conduct sessions, build reputation
- **Admins**: Manage users, customize theme, moderate content, view analytics

### Core Features
- 🔐 Custom authentication with role-based access control
- 👤 Comprehensive profiles for students and mentors
- 🔍 Advanced mentor search with filters (skills, rating, availability)
- 📅 Session booking with availability calendar
- 💬 Real-time chat using Django Channels
- 🔔 Real-time notifications
- 📰 LinkedIn-style feed with posts, comments, likes, shares
- ⭐ Rating and review system
- 🎨 Admin-customizable theme colors
- 🌐 Multilingual support (English/Kinyarwanda)
- ♿ Accessibility features (text-to-speech, high contrast, large text)

## Tech Stack

- **Backend**: Django 6.0+
- **Frontend**: Django Templates, CSS3, JavaScript
- **Database**: SQLite (dev) / PostgreSQL (production)
- **Real-time**: Django Channels
- **Icons**: Feather Icons

## Installation

### 1. Clone and Setup

```bash
cd mentor_platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production
DB_NAME=mentor_connect_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

## Project Structure

```
mentor_platform/
├── config/                 # Project settings
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── accounts/              # User authentication
├── profiles/              # Student & mentor profiles
├── dashboard/             # Role-based dashboards
├── mentorship/            # Mentorship requests & reviews
├── feed/                  # Social feed (posts, comments)
├── sessions_app/          # Session booking & availability
├── chat/                  # Real-time messaging
├── notifications/         # Notification system
├── core/                  # Site settings, themes, utils
├── templates/             # HTML templates
│   ├── base.html
│   ├── components/
│   ├── accounts/
│   ├── dashboard/
│   ├── feed/
│   └── ...
├── static/                # CSS, JS, images
│   ├── css/main.css
│   └── js/main.js
└── media/                 # User uploads
```

## User Accounts for Testing

### Admin
- Email: admin@mentorconnect.com
- Password: admin123

### Creating Test Users
1. Visit /accounts/signup/
2. Choose Student or Mentor
3. Fill in the registration form

## Admin Features

Access the admin dashboard at `/dashboard/admin/`:

- **User Management**: View, activate/deactivate, delete users
- **Theme Customization**: Change all colors dynamically
- **Site Settings**: Update logo, name, contact info
- **Activity Logs**: Monitor user activities
- **Broadcast**: Send notifications to all users

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `POST /accounts/signup/student/` - Student registration
- `POST /accounts/signup/mentor/` - Mentor registration

### Profiles
- `GET /profiles/<id>/` - View profile
- `GET /profiles/edit/` - Edit profile
- `POST /profiles/follow/<id>/` - Follow user
- `POST /profiles/unfollow/<id>/` - Unfollow user

### Mentorship
- `GET /mentorship/search/` - Search mentors
- `POST /mentorship/request/<mentor_id>/` - Send request
- `POST /mentorship/requests/<id>/approve/` - Approve request
- `POST /mentorship/requests/<id>/reject/` - Reject request

### Sessions
- `GET /sessions/` - List sessions
- `POST /sessions/book/<mentor_id>/` - Book session
- `GET /sessions/calendar/<mentor_id>/` - View mentor calendar

### Feed
- `GET /feed/` - View feed
- `POST /feed/post/create/` - Create post
- `POST /feed/post/<id>/like/` - Like post
- `POST /feed/post/<id>/comment/` - Add comment

### Chat
- `GET /chat/` - List conversations
- `GET /chat/conversation/<id>/` - View conversation
- `POST /chat/send/<conversation_id>/` - Send message

### Notifications
- `GET /notifications/` - List notifications
- `GET /notifications/count/` - Get unread count
- `POST /notifications/<id>/read/` - Mark as read

## Customization

### Changing Theme Colors

1. Login as admin
2. Go to Dashboard > Theme
3. Adjust colors using the color pickers
4. Save changes

### Adding Translations

1. Go to Dashboard > Settings
2. Add translations for Kinyarwanda
3. Use the language switcher in navbar

### Modifying Styles

Edit `static/css/main.css` - all styles use CSS variables for easy theming.

## Deployment

### For Production

1. Set `DEBUG=False` in settings
2. Configure PostgreSQL database
3. Set up Redis for Django Channels
4. Use Daphne or Uvicorn as ASGI server
5. Configure static files with WhiteNoise or Nginx
6. Set proper `ALLOWED_HOSTS`

### Environment Variables

```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379
ALLOWED_HOSTS=yourdomain.com
```

## License

MIT License - Free for personal and commercial use.

## Support

For issues and feature requests, please create an issue in the repository.

---

Built with ❤️ for connecting students with mentors
