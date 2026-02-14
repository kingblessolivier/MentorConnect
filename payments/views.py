"""
Payments App Views
Payment submission (student), verification (finance), and payouts
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

# Placeholder for payment-related views (e.g. submit payment, verify, list)
# Main flow is in applications/views (submit with payment) and dashboard (finance verify)
