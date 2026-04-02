from django import template

register = template.Library()


@register.filter
def split(value, sep=','):
    """Divide una cadena por separador. Uso: "a,b,c"|split:"," """
    return [x.strip() for x in value.split(sep)]


@register.filter
def dictsort_by(queryset, attr):
    """Ordena un queryset/lista por atributo anidado."""
    try:
        return sorted(queryset, key=lambda x: str(getattr(x, attr, '')))
    except Exception:
        return queryset


@register.filter
def subtract(value, arg):
    """Resta: {{ valor|subtract:otro }} """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value


@register.filter
def currency(value):
    """Formatea como moneda boliviana."""
    try:
        return f"Bs {float(value):,.2f}"
    except (ValueError, TypeError):
        return value


@register.simple_tag
def get_item(dictionary, key):
    """Obtiene valor de un diccionario por clave variable."""
    return dictionary.get(key, '')


@register.inclusion_tag('base/_estado_badge.html')
def estado_badge(estado, display):
    return {'estado': estado, 'display': display}
