"""
Accounts App Models
Custom User model with role-based authentication (Student, Mentor, Admin)
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with role-based access
    Supports: Student, Mentor, Admin roles
    """
    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        MENTOR = 'mentor', 'Mentor'
        ADMIN = 'admin', 'Admin'

    # Remove username field, use email for authentication
    username = None
    email = models.EmailField('Email Address', unique=True)

    # Role field
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Role'
    )

    # Profile fields
    first_name = models.CharField('First Name', max_length=100)
    last_name = models.CharField('Last Name', max_length=100)
    phone = models.CharField('Phone Number', max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Profile Photo'
    )

    # Status fields
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)

    # Preferences
    language = models.CharField(max_length=5, default='en', choices=[
        ('en', 'English'),
        ('rw', 'Kinyarwanda'),
    ])

    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_mentor(self):
        return self.role == self.Role.MENTOR

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.svg'

    def get_profile(self):
        """Get the user's role-specific profile"""
        if self.is_student:
            try:
                return self.student_profile
            except Exception:
                return None
        elif self.is_mentor:
            try:
                return self.mentor_profile
            except Exception:
                return None
        return None

