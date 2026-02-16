from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView
from applications.models import Application

class MFApplicationDetailView(LoginRequiredMixin, MentorFacilitatorRequiredMixin, DetailView):
    """Mentor Facilitator: view mentorship application details"""
    template_name = 'dashboard/mf_application_detail.html'
    context_object_name = 'application'

    def get_object(self):
        return get_object_or_404(Application, pk=self.kwargs['pk'])

    def get_queryset(self):
        return Application.objects.select_related(
            'applicant', 'selected_mentor', 'selected_availability_slot'
        )
