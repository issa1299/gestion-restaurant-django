import os
import uuid

_DOSSIERS = {
    "produits": "produits",
    "clients": "clients",
    "users": "users",
    "galerie": "galerie",
    "parametres": "parametres",
}


def upload_restaurant(instance, filename):
    """upload_to tenant-aware : sépare les fichiers par restaurant.

    Ex : restaurants/12/produits/<uuid>.<ext>
    """
    dossier = _DOSSIERS.get(instance._meta.model_name, "autres")
    rid = getattr(instance, "restaurant_id", None) or 0
    ext = os.path.splitext(filename)[1]
    nom = f"{uuid.uuid4().hex}{ext}"
    return os.path.join("restaurants", str(rid), dossier, nom)
