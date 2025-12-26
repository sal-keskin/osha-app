from django import template

register = template.Library()

@register.filter
def getattr(obj, attr_name):
    """
    Custom template filter to get an attribute of an object dynamically.
    Usage: {{ object|getattr:attribute_name }}
    """
    try:
        return obj.__getattribute__(attr_name)
    except AttributeError:
        # Try as dictionary lookup if object is a dict (not likely here but good practice)
        try:
            return obj[attr_name]
        except (TypeError, KeyError):
            return ""
