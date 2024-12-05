from django import template

register = template.Library()

@register.simple_tag
def render_form_field(form_field):
    return form_field.label_tag() + str(form_field)

@register.simple_tag
def show_errors(form):
    errors = form.errors.as_ul()
    return errors if errors else ""

@register.simple_tag
def is_required(field):
    return "required" if field.field.required else ""
