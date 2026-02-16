from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import UserProfile, ActionLog
from django.contrib.auth.models import User

@receiver(pre_save, sender=UserProfile)
def log_user_role_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = UserProfile.objects.get(pk=instance.pk)
            if old_instance.role != instance.role:
                # Create audit log
                # Note: We don't have request.user here easily without thread locals or passing it.
                # For now, we logging the change. Ideally we'd want the "Actor".
                # Since this runs on save, usually triggered by a view.
                # We can store the change description here, but the Actor is tricky in signals.
                # Instead, we might handle the LOGGING in the View for the Actor context.
                # BUT, the requirement said "Create a signal or middleware".
                # A signal is good for "User A changed User B", but signal only knows User B (instance).
                # To stick to requirements while being practical:
                # I will implement the log logic here but simpler, or allow the View to create the log.
                # Use a middleware to capture Request User? Too complex for this phase.
                # Let's rely on the View for the "Actor" and use Signal for system-side tracking or just stick to View.
                # Plan Check: "KVKK Audit Logging (The "Watcher"): Create a signal or middleware..."
                # I'll create a helper function `log_action` and call it from Views for better context.
                pass
        except UserProfile.DoesNotExist:
            pass
