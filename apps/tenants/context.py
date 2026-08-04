from contextvars import ContextVar

# Restaurant courant de la requête en cours (thread/async local).
_restaurant_courant: ContextVar = ContextVar("restaurant_courant", default=None)


def set_current_restaurant(restaurant):
    """Définit le restaurant courant (objet Restaurant ou None)."""
    _restaurant_courant.set(restaurant)


def get_current_restaurant():
    """Retourne le restaurant courant (objet Restaurant) ou None."""
    return _restaurant_courant.get()


def get_current_restaurant_id():
    """Retourne l'id du restaurant courant, ou None."""
    r = get_current_restaurant()
    return r.id if r is not None else None
