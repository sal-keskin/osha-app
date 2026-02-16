from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

def medical_access_required(view_func):
    """
    Decorator to check if user has medical access rights.
    Admin and Doctor roles have access.
    Specialist role is denied.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user has profile
        if hasattr(request.user, 'profile'):
            if request.user.profile.has_medical_access():
                return view_func(request, *args, **kwargs)
            else:
                # KVKK Compliance: Explicit denial for non-medical staff
                messages.error(request, "Muayenelere erişmek için İş Yeri Hekimi Rolüne Sahip Olmanız Gerekmektedir!")
                return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
        
        # Fallback for superusers without profile (shouldn't happen in prod but safe dev fallback)
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
            
        # Default deny for anyone else (e.g. user without profile)
        messages.error(request, "Yetkisiz erişim. Profil bilgisi bulunamadı.")
        return redirect('dashboard')
        
    return _wrapped_view
