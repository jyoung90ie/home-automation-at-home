"""Creates custom template functions for use in .html templates"""
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def to_status_icon(value: bool) -> str:
    """Accepts a bool and returns icon indicating status"""
    output_html = ""
    if not isinstance(value, bool):
        return ""

    if value:
        output_html = '<i class="fas fa-check text-success" title="enabled icon"></i>'
    else:
        output_html = (
            '<i class="fas fa-times-circle text-danger" title="disabled icon"></i>'
        )

    return mark_safe(output_html)
