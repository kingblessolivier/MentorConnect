"""
Profiles App Models
Student and Mentor profile models with all required fields
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _



class StudentProfile(models.Model):
    """
    Extended profile for students
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    # Bio and Personal Info
    bio = models.TextField(
        blank=True,
        max_length=1000,
        help_text='Tell us about yourself'
    )
    headline = models.CharField(
        max_length=200,
        blank=True,
        help_text='e.g., Computer Science Student at University of Rwanda'
    )

    # Education
    institution = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='School/University'
    )
    field_of_study = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Field of Study'
    )
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Expected Graduation Year'
    )

    # Skills and Interests
    skills = models.TextField(
        blank=True,
        help_text='Comma-separated list of skills (e.g., Python, Data Analysis, Leadership)'
    )
    interests = models.TextField(
        blank=True,
        help_text='What topics are you interested in learning about?'
    )
    goals = models.TextField(
        blank=True,
        help_text='What are your career goals?'
    )

    # CV/Resume
    cv = models.FileField(
        upload_to='cvs/',
        blank=True,
        null=True,
        verbose_name='CV/Resume'
    )

    # Social Links
    linkedin_url = models.URLField(blank=True, verbose_name='LinkedIn')
    github_url = models.URLField(blank=True, verbose_name='GitHub')
    portfolio_url = models.URLField(blank=True, verbose_name='Portfolio')

    # Profile Completion
    profile_completed = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'

    def __str__(self):
        return f"{self.user.get_full_name()} - Student Profile"

    def get_skills_list(self):
        """Return skills as a list"""
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

    def get_interests_list(self):
        """Return interests as a list"""
        if self.interests:
            return [i.strip() for i in self.interests.split(',') if i.strip()]
        return []

    def calculate_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.bio, self.headline, self.institution,
            self.field_of_study, self.skills, self.interests,
            self.goals, self.user.avatar
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)


class MentorProfile(models.Model):
    """
    Extended profile for mentors - Shadow/Observation Internship Platform
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_profile'
    )

    # Bio and Professional Info
    bio = models.TextField(
        blank=True,
        max_length=2000,
        help_text='Tell students about yourself and your experience'
    )
    headline = models.CharField(
        max_length=200,
        blank=True,
        help_text='e.g., Senior Software Engineer at Google'
    )

    # Professional Details
    expertise = models.CharField(
        max_length=200,
        help_text='Your main area of expertise'
    )
    skills = models.TextField(
        help_text='Comma-separated list of skills you can teach'
    )
    experience_years = models.PositiveIntegerField(
        default=0,
        verbose_name='Years of Experience'
    )

    # Current Position
    company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Company/Organization'
    )
    job_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Job Title/Profession'
    )

    # Location (for physical observation internships)
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='City/Region',
        help_text='e.g., Kigali, Nairobi, Lagos'
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        default='Rwanda',
        verbose_name='Country'
    )
    workplace_address = models.TextField(
        blank=True,
        verbose_name='Workplace Address',
        help_text='Where students will shadow you'
    )

    # Education Background
    diploma = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Diploma/Degree',
        help_text='e.g., Master of Medicine, Bachelor of Engineering'
    )
    educational_institution = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Educational Institution',
        help_text='e.g., University of Rwanda, MIT'
    )

    # Observation Internship Settings
    accepts_in_person = models.BooleanField(
        default=True,
        verbose_name='Accepts In-Person Shadowing',
        help_text='Allow students to shadow you at your workplace'
    )
    accepts_virtual = models.BooleanField(
        default=False,
        verbose_name=_('Accepts Virtual Sessions'),
        help_text=_('Offer virtual mentoring sessions')
    )
    min_internship_days = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Minimum Internship Days'),
        help_text=_('Minimum days for observation internship (1-5)')
    )
    max_internship_days = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Maximum Internship Days'),
        help_text=_('Maximum days for observation internship (1-5)')
    )

    # Availability
    is_available = models.BooleanField(
        default=True,
        verbose_name=_('Available for Mentoring')
    )
    max_mentees = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Maximum Number of Mentees')
    )

    # Session Preferences
    session_duration = models.PositiveIntegerField(
        default=60,
        help_text=_('Default session duration in minutes'),
        verbose_name=_('Session Duration')
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Leave 0 for free mentoring'),
        verbose_name=_('Hourly Rate')
    )

    # Rating
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)

    # Featured
    is_featured = models.BooleanField(default=False)

    # Social Links
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    # Profile Status
    profile_completed = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mentor Profile'
        verbose_name_plural = 'Mentor Profiles'
        ordering = ['-is_featured', '-rating', '-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - Mentor Profile"

    def get_skills_list(self):
        """Return skills as a list"""
        if self.skills:
            return [s.strip() for s in self.skills.split(',') if s.strip()]
        return []

    def calculate_completion(self):
        """Calculate profile completion percentage"""
        fields = [
            self.bio, self.headline, self.expertise,
            self.skills, self.company, self.job_title,
            self.user.avatar
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)

    # def update_rating(self):
    #     """Recalculate average rating from reviews"""
    #     from mentorship.models import Review
    #     reviews = Review.objects.filter(mentor=self.user)
    #     if reviews.exists():
    #         self.rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
    #         self.total_reviews = reviews.count()
    #         self.save()


class Follow(models.Model):
    """
    Model for following mentors
    """
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='following'
    )
    followed = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'followed')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.follower.get_full_name()} follows {self.followed.get_full_name()}"


class Skill(models.Model):
    """
    Predefined skills for searching/filtering
    """
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100, blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='Icon class name')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

