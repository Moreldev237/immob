from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def index_view(request):
    """
    View to serve the frontend homepage.
    This serves the immob.html file when accessing the root URL.
    """
    return render(request, 'immob.html')


def login_view(request):
    """
    View to serve the login page.
    """
    return render(request, 'login.html')


def register_view(request):
    """
    View to serve the registration page.
    """
    return render(request, 'register.html')


def properties_view(request):
    """
    View to serve the properties listing page.
    """
    return render(request, 'properties.html')


def property_detail_view(request, property_id):
    """
    View to serve the property detail page.
    """
    return render(request, 'property_detail.html', {'property_id': property_id})


@login_required
def profile_view(request):
    """
    View to serve the user profile page.
    """
    return render(request, 'profile.html')


@login_required
def favorites_view(request):
    """
    View to serve the user's favorites page.
    """
    return render(request, 'favorites.html')


@login_required
def reviews_view(request):
    """
    View to serve the reviews management page.
    """
    return render(request, 'reviews.html')


def contact_view(request):
    """
    View to serve the contact page.
    """
    return render(request, 'contact.html')
