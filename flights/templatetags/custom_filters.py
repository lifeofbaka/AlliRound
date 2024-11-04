# templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def show_items(sequence, position):
    return sequence[position]