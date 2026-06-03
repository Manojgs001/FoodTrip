from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allow dict[key] lookups in templates: {{ dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, 0)
    return 0

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter: {{ "a,b,c"|split:"," }}"""
    return value.split(delimiter)

# Maps status → how many steps are complete (0-4)
STATUS_STEP = {
    'Pending': 0,
    'Paid': 1,
    'Preparing': 2,
    'Out for Delivery': 3,
    'Delivered': 4,
}

@register.filter
def status_step(status):
    """Return numeric step index for order status."""
    return STATUS_STEP.get(status, 0)
