from django import template

register = template.Library()

@register.filter
def key_in(d, key):
    return key in d

