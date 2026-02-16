from datetime import date
from django.db.models import Count
from core.models import Worker, Facility, Education, Examination
from core.utils import get_allowed_workplaces
import logging

logger = logging.getLogger(__name__)

def get_user_scoped_stats(user):
    """
    Calculates dashboard stats based strictly on the user's allowed universe.
    Returns a safe dictionary even on error to prevent 500s.
    """
    try:
        # 1. Get the Universe (The Allowed Workplaces)
        allowed_workplaces = get_allowed_workplaces(user)
        
        # 2. Scope the Sub-Models
        # Optimization: Don't fetch objects, just querysets
        scoped_workers = Worker.objects.filter(workplace__in=allowed_workplaces)
        scoped_facilities = Facility.objects.filter(workplace__in=allowed_workplaces)
        
        # 3. Calculate Counts
        total_workers = scoped_workers.count()
        total_facilities = scoped_facilities.count()
        
        # 4. Calculate Compliance %
        if total_workers > 0:
            # Education: Percentage (Fast approximation using exists/count)
            trained_workers = scoped_workers.filter(education__isnull=False).distinct().count()
            training_pct = int((trained_workers / total_workers * 100))
            
            # Examination
            examined_workers = scoped_workers.filter(examination__isnull=False).distinct().count()
            exam_pct = int((examined_workers / total_workers * 100))
            
            # First Aid
            first_aid_count = scoped_workers.filter(first_aid_certificate=True).count()
        else:
            training_pct = 0
            exam_pct = 0
            first_aid_count = 0

        return {
            'total_workplaces': allowed_workplaces.count(),
            'total_facilities': total_facilities,
            'total_workers': total_workers,
            'training_pct': training_pct,
            'exam_pct': exam_pct,
            'first_aid_count': first_aid_count,
        }
    except Exception as e:
        logger.error(f"Error calculating stats: {e}", exc_info=True)
        # Return zeros on error to prevent crash
        return {
            'total_workplaces': 0,
            'total_facilities': 0,
            'total_workers': 0,
            'training_pct': 0,
            'exam_pct': 0,
            'first_aid_count': 0,
        }
