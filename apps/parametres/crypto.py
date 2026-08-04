"""Chiffrement/déchiffrement des mots de passe sensibles (SMTP).

Utilise Fernet (cryptographie symétrique) avec une clé dérivée
de `settings.SECRET_KEY`. Les valeurs chiffrées sont préfixées
par "enc:" pour être distinguées des valeurs en clair (légacy).
"""

import base64
import hashlib

from django.conf import settings

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:
    Fernet = None


PREFIX = "enc:"


def _cle():
    """Dérive une clé Fernet (32 octets, base64 URL-safe) depuis SECRET_KEY."""
    digest = base64.urlsafe_b64encode(
        hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    )
    return digest


def _fernet():
    if Fernet is None:
        raise ImportError(
            "La bibliothèque 'cryptography' est requise pour chiffrer les mots de passe."
        )
    return Fernet(_cle())


def chiffrer(texte):
    """Chiffre une valeur en clair. Retourne 'enc:' + texte chiffré."""
    if not texte:
        return ""
    return PREFIX + _fernet().encrypt(texte.encode("utf-8")).decode("utf-8")


def dechiffrer(chaine):
    """Déchiffre une valeur chiffrée ('enc:...'). Valeur en clair (légacy) -> inchangée."""
    if not chaine or not chaine.startswith(PREFIX):
        return chaine
    try:
        return _fernet().decrypt(chaine[len(PREFIX):].encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return ""


def est_chiffree(chaine):
    return bool(chaine and chaine.startswith(PREFIX))
