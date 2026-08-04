from django.db import models
from .context import get_current_restaurant_id


class TenantManager(models.Manager):
    """Manager qui filtre automatiquement les requêtes par restaurant courant.

    - `objects` (défaut) : ne renvoie QUE les lignes du restaurant courant.
    - `.all_objects()` : échappe au filtre (utilisé par l'admin plateforme / migrations).
    - `.create()` : affecte automatiquement le restaurant courant.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        rid = get_current_restaurant_id()
        if rid is not None:
            qs = qs.filter(restaurant_id=rid)
        return qs

    def all_objects(self):
        return super().get_queryset()

    def create(self, **kwargs):
        if "restaurant" not in kwargs and "restaurant_id" not in kwargs:
            rid = get_current_restaurant_id()
            if rid is not None:
                kwargs["restaurant_id"] = rid
        return super().create(**kwargs)

    def get_or_create(self, defaults=None, **kwargs):
        if "restaurant" not in kwargs and "restaurant_id" not in kwargs:
            rid = get_current_restaurant_id()
            if rid is not None:
                kwargs["restaurant_id"] = rid
        return super().get_or_create(defaults=defaults, **kwargs)
