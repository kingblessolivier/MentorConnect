"""
Applications Services
Email sending, token handling, and smart mentor matching
"""

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.db import models


def send_approval_email(application):
    """Send invitation email when mentor approves guest application"""
    from .models import InvitationToken

    # Delete old tokens for this application, create new one
    InvitationToken.objects.filter(application=application).delete()
    token_obj = InvitationToken.create_for_application(application)

    # Build absolute URL for registration
    domain = getattr(settings, 'SITE_DOMAIN', None) or (
        settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
    )
    if settings.DEBUG and domain == 'localhost':
        domain = 'localhost:8000'
    scheme = 'https' if not settings.DEBUG else 'http'
    path = reverse('applications:register_with_token', kwargs={'token': token_obj.token})
    registration_url = f"{scheme}://{domain}{path}"

    site_name = getattr(settings, 'SITE_NAME', 'MentorConnect')
    subject = f"Your application has been approved - {site_name}"

    context = {
        'application': application,
        'registration_url': registration_url,
        'site_name': site_name,
    }

    html_message = render_to_string('emails/approval_email.html', context)
    message = strip_tags(html_message)

    send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mentorconnect.local'),
        recipient_list=[application.email],
        fail_silently=True,
        html_message=html_message,
    )


def calculate_mentor_student_compatibility(student, mentor):
    """
    Calculate compatibility score between student and mentor (0-100).
    Considers skills, expertise, availability, location, and preferences.
    """
    from profiles.models import MentorProfile
    from mentorship.models import MentorAvailability
    
    score = 0.0
    factors = []
    weights = []
    
    try:
        mentor_profile = mentor.mentor_profile
    except:
        return 0.0
    
    # 1. Skills matching (weight: 25%)
    if hasattr(student, 'student_profile') and student.student_profile.skills:
        student_skills = set([s.strip().lower() for s in student.student_profile.skills.split(',') if s.strip()])
    else:
        student_skills = set()
    
    if mentor_profile.skills:
        mentor_skills = set([s.strip().lower() for s in mentor_profile.skills.split(',') if s.strip()])
    else:
        mentor_skills = set()
    
    if student_skills and mentor_skills:
        common_skills = student_skills.intersection(mentor_skills)
        if mentor_skills:
            skill_match = len(common_skills) / len(mentor_skills) * 100
        else:
            skill_match = 0
    else:
        skill_match = 0
    
    factors.append(skill_match)
    weights.append(0.25)
    
    # 2. Expertise area matching (weight: 20%)
    if hasattr(student, 'student_profile') and student.student_profile.field_of_interest:
        student_field = student.student_profile.field_of_interest.lower()
    else:
        student_field = ''
    
    if mentor_profile.expertise:
        mentor_expertise = mentor_profile.expertise.lower()
        if student_field and mentor_expertise:
            # Simple keyword matching - could be enhanced with NLP
            if student_field in mentor_expertise or mentor_expertise in student_field:
                expertise_match = 100
            else:
                # Check for common words
                student_words = set(student_field.split())
                mentor_words = set(mentor_expertise.split())
                common_words = student_words.intersection(mentor_words)
                if student_words:
                    expertise_match = len(common_words) / len(student_words) * 100
                else:
                    expertise_match = 0
        else:
            expertise_match = 0
    else:
        expertise_match = 0
    
    factors.append(expertise_match)
    weights.append(0.20)
    
    # 3. Availability matching (weight: 20%)
    # Check if mentor has upcoming availability
    upcoming_availability = MentorAvailability.objects.filter(
        mentor=mentor,
        date__gte=timezone.now().date(),
        current_bookings__lt=models.F('max_bookings')
    ).count()
    
    if upcoming_availability > 0:
        availability_match = 100
    else:
        availability_match = 0
    
    factors.append(availability_match)
    weights.append(0.20)
    
    # 4. Location preferences (weight: 15%)
    if hasattr(student, 'student_profile') and student.student_profile.location:
        student_location = student.student_profile.location.lower()
    else:
        student_location = ''
    
    if mentor_profile.city:
        mentor_location = mentor_profile.city.lower()
        if student_location and mentor_location:
            if student_location == mentor_location:
                location_match = 100
            elif student_location in mentor_location or mentor_location in student_location:
                location_match = 80
            else:
                location_match = 0
        else:
            location_match = 50  # Neutral score if location info missing
    else:
        location_match = 50
    
    factors.append(location_match)
    weights.append(0.15)
    
    # 5. Mentor rating and experience (weight: 10%)
    rating_score = (mentor_profile.rating or 0) * 20  # Convert 0-5 to 0-100
    experience_score = min(100, (mentor_profile.experience_years or 0) * 10)  # 10 years = 100
    
    reputation_match = (rating_score + experience_score) / 2
    factors.append(reputation_match)
    weights.append(0.10)
    
    # 6. Session type preference (weight: 10%)
    if hasattr(student, 'student_profile'):
        student_prefers_virtual = getattr(student.student_profile, 'prefers_virtual', False)
        student_prefers_in_person = getattr(student.student_profile, 'prefers_in_person', False)
    else:
        student_prefers_virtual = False
        student_prefers_in_person = False
    
    mentor_accepts_virtual = mentor_profile.accepts_virtual
    mentor_accepts_in_person = mentor_profile.accepts_in_person
    
    session_match = 0
    if (student_prefers_virtual and mentor_accepts_virtual) or \
       (student_prefers_in_person and mentor_accepts_in_person):
        session_match = 100
    elif mentor_accepts_virtual and mentor_accepts_in_person:
        session_match = 80  # Mentor is flexible
    else:
        session_match = 0
    
    factors.append(session_match)
    weights.append(0.10)
    
    # Calculate weighted average
    weighted_sum = sum(f * w for f, w in zip(factors, weights))
    total_weight = sum(weights)
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0


def find_recommended_mentors(student, limit=5):
    """
    Find recommended mentors for a student based on compatibility.
    Returns list of tuples (mentor, compatibility_score, match_reasons).
    """
    from django.contrib.auth import get_user_model
    from profiles.models import MentorProfile
    
    User = get_user_model()
    
    # Get all available mentors
    available_mentors = User.objects.filter(
        role='mentor',
        mentor_profile__is_available=True,
        mentor_profile__profile_completed=True
    ).select_related('mentor_profile')
    
    recommendations = []
    
    for mentor in available_mentors:
        score = calculate_mentor_student_compatibility(student, mentor)
        
        if score > 0:  # Only include mentors with some compatibility
            # Generate match reasons
            match_reasons = []
            
            try:
                mentor_profile = mentor.mentor_profile
                
                # Check skills match
                if hasattr(student, 'student_profile') and student.student_profile.skills:
                    student_skills = set([s.strip().lower() for s in student.student_profile.skills.split(',') if s.strip()])
                    mentor_skills = set([s.strip().lower() for s in mentor_profile.skills.split(',') if s.strip()])
                    common_skills = student_skills.intersection(mentor_skills)
                    if common_skills:
                        match_reasons.append(f"Shared skills: {', '.join(list(common_skills)[:3])}")
                
                # Check expertise match
                if hasattr(student, 'student_profile') and student.student_profile.field_of_interest:
                    student_field = student.student_profile.field_of_interest
                    if mentor_profile.expertise and student_field.lower() in mentor_profile.expertise.lower():
                        match_reasons.append(f"Expertise in {student_field}")
                
                # Check availability
                from mentorship.models import MentorAvailability
                upcoming = MentorAvailability.objects.filter(
                    mentor=mentor,
                    date__gte=timezone.now().date(),
                    current_bookings__lt=models.F('max_bookings')
                ).exists()
                if upcoming:
                    match_reasons.append("Has upcoming availability")
                
                # Check rating
                if mentor_profile.rating and mentor_profile.rating >= 4.0:
                    match_reasons.append(f"High rating ({mentor_profile.rating}/5)")
                
            except Exception:
                pass
            
            recommendations.append({
                'mentor': mentor,
                'score': round(score, 1),
                'match_reasons': match_reasons[:3],  # Limit to top 3 reasons
                'profile': mentor_profile
            })
    
    # Sort by score descending
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return recommendations[:limit]


def auto_match_mentor(application):
    """
    Automatically select the best mentor for an application based on compatibility.
    Can be used during application wizard step 3.
    """
    if not application.applicant:
        return None
    
    recommendations = find_recommended_mentors(application.applicant, limit=3)
    
    if recommendations:
        # Select top recommendation
        best_match = recommendations[0]
        
        # Update application with selected mentor
        application.selected_mentor = best_match['mentor']
        application.save()
        
        # Log the auto-match
        from applications.models import ActivityLog
        ActivityLog.objects.create(
            user=application.applicant,
            action='auto_match',
            description=f"Auto-matched with {best_match['mentor'].get_full_name()} "
                       f"(score: {best_match['score']})"
        )
        
        return best_match['mentor']
    
    return None
