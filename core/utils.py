from django.db.models import Q
from .models import Workplace
from datetime import date

def get_allowed_workplaces(user):
    """
    Returns a QuerySet of Workplaces the user is explicitly authorized to access.
    Handles Admins, Managers, and assigned Professionals.
    """
    # 1. Superusers always see everything
    if user.is_superuser:
        return Workplace.objects.all()

    # 2. Check user profile role
    # Use getattr to avoid potential DoesNotExist errors if profile missing
    if hasattr(user, 'profile'):
        role = user.profile.role
        if role in ['ADMIN', 'MANAGER']:
            return Workplace.objects.all()

    # 3. Doctors & Experts see ONLY assigned workplaces
    # usage: checks the 'assignments' relation
    # Also enforcing date validity
    today = date.today()
    
    return Workplace.objects.filter(
        assignments__user=user,
        assignments__is_active=True,
        assignments__start_date__lte=today
    ).filter(
        Q(assignments__end_date__isnull=True) | Q(assignments__end_date__gte=today)
    ).distinct()


