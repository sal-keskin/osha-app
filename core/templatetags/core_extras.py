from django import template

register = template.Library()

@register.filter(name='getattr')
def get_attribute(obj, attr_name):
    """
    Custom template filter to get an attribute of an object dynamically.
    Usage: {{ object|getattr:attribute_name }}
    """
    try:
        val = getattr(obj, attr_name)
        if callable(val):
            return val()
        return val
    except (AttributeError, TypeError):
        # Try as dictionary lookup
        try:
            return obj[attr_name]
        except (TypeError, KeyError):
            return ""
