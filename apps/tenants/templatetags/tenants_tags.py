from django import template

register = template.Library()


@register.simple_tag
def plateforme_parametres():
    """Charge le singleton ParametrePlateforme (logo, nom) pour la console."""
    from apps.tenants.models import ParametrePlateforme

    return ParametrePlateforme.load()