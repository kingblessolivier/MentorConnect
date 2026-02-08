"""
Core App Views
Public pages: Home, About, Mentors list, etc.
"""

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView
from django.http import JsonResponse
from django.utils import translation
from django.conf import settings
from django.db import models

from .models import SiteSettings, ThemeSettings, Testimonial, FAQ


class HomeView(TemplateView):
    """
    Landing page with hero section, services, featured mentors, testimonials
    """
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get featured testimonials
        context['testimonials'] = Testimonial.objects.filter(
            is_active=True,
            is_featured=True
        )[:6]

        # Get FAQs
        context['faqs'] = FAQ.objects.filter(is_active=True)[:5]

        # Get featured mentors (will be added later)
        try:
            from profiles.models import MentorProfile
            context['featured_mentors'] = MentorProfile.objects.filter(
                is_featured=True,
                user__is_active=True
            ).select_related('user')[:6]
        except Exception:
            context['featured_mentors'] = []

        return context


class AboutView(TemplateView):
    """
    About us page
    """
    template_name = 'core/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:3]
        return context


class MentorsListView(ListView):
    """
    Public mentors/professionals listing with search and filters
    For Mirror platform: Observation internship opportunities
    """
    template_name = 'core/mentors_list.html'
    context_object_name = 'mentors'
    paginate_by = 12

    def get_queryset(self):
        try:
            from profiles.models import MentorProfile
            queryset = MentorProfile.objects.filter(
                user__is_active=True
            ).select_related('user')

            # Search filter
            search = self.request.GET.get('search', '')
            if search:
                queryset = queryset.filter(
                    models.Q(user__first_name__icontains=search) |
                    models.Q(user__last_name__icontains=search) |
                    models.Q(expertise__icontains=search) |
                    models.Q(skills__icontains=search) |
                    models.Q(job_title__icontains=search) |
                    models.Q(company__icontains=search)
                )

            # Profession/Job Title filter
            profession = self.request.GET.get('profession', '')
            if profession:
                queryset = queryset.filter(
                    models.Q(job_title__icontains=profession) |
                    models.Q(expertise__icontains=profession)
                )

            # Skills filter
            skills = self.request.GET.get('skills', '')
            if skills:
                queryset = queryset.filter(skills__icontains=skills)

            # Company filter
            company = self.request.GET.get('company', '')
            if company:
                queryset = queryset.filter(company__icontains=company)

            # City/Region filter
            city = self.request.GET.get('city', '')
            if city:
                queryset = queryset.filter(
                    models.Q(city__icontains=city) |
                    models.Q(country__icontains=city)
                )

            # Mentorship type filter
            mentorship_type = self.request.GET.get('type', '')
            if mentorship_type == 'in_person':
                queryset = queryset.filter(accepts_in_person=True)
            elif mentorship_type == 'virtual':
                queryset = queryset.filter(accepts_virtual=True)
            elif mentorship_type == 'both':
                queryset = queryset.filter(accepts_in_person=True, accepts_virtual=True)

            return queryset.order_by('-is_featured', '-rating', '-created_at')
        except Exception:
            return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['profession'] = self.request.GET.get('profession', '')
        context['skills'] = self.request.GET.get('skills', '')
        context['company'] = self.request.GET.get('company', '')
        context['city'] = self.request.GET.get('city', '')
        context['type'] = self.request.GET.get('type', '')
        return context


class ContactView(TemplateView):
    """
    Contact us page
    """
    template_name = 'core/contact.html'


class PrivacyPolicyView(TemplateView):
    """
    Privacy Policy page
    """
    template_name = 'core/privacy.html'


class TermsOfServiceView(TemplateView):
    """
    Terms of Service page
    """
    template_name = 'core/terms.html'


class CookiePolicyView(TemplateView):
    """
    Cookie Policy page
    """
    template_name = 'core/cookies.html'


class HowItWorksView(TemplateView):
    """
    How It Works page for students
    """
    template_name = 'core/how_it_works.html'


class SuccessStoriesView(TemplateView):
    """
    Success Stories page
    """
    template_name = 'core/success_stories.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:12]
        return context


class MentorGuidelinesView(TemplateView):
    """
    Mentor Guidelines page
    """
    template_name = 'core/mentor_guidelines.html'


class ResourcesView(TemplateView):
    """
    Resources page
    """
    template_name = 'core/resources.html'


class CommunityView(TemplateView):
    """
    Community page
    """
    template_name = 'core/community.html'


def set_language(request):
    """
    View to switch language
    """
    language = request.GET.get('lang', 'en')

    if language in dict(settings.LANGUAGES):
        translation.activate(language)
        request.session['django_language'] = language

        response = redirect(request.META.get('HTTP_REFERER', '/'))
        response.set_cookie('django_language', language, max_age=365*24*60*60)
        return response

    return redirect('/')


def set_accessibility(request):
    """
    View to toggle accessibility settings
    """
    setting = request.GET.get('setting', '')
    value = request.GET.get('value', 'false') == 'true'

    if setting in ['high_contrast', 'large_text', 'text_to_speech']:
        request.session[setting] = value
        return JsonResponse({'success': True, 'setting': setting, 'value': value})

    return JsonResponse({'success': False, 'error': 'Invalid setting'})


def health_check(request):
    """
    Health check endpoint for deployment
    """
    return JsonResponse({'status': 'healthy', 'app': 'MentorConnect'})
