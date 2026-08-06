"""Service PayDunya — Mobile Money (Orange Money, Wave, Moov, MTN) en FCFA.

Documentation officielle : https://developers.paydunya.com/

Flux (Paiement Avec Redirection - PAR) :
1. POST /v1/checkout-invoice/create    → réponse response_code="00",
   response_text = URL de la caisse PayDunya, token = token de facture.
2. Utilisateur redirigé sur l'URL de paiement (caisse PayDunya).
3. PayDunya appelle callback_url (IPN : POST application/x-www-form-urlencoded,
   champ "data" = JSON, CSRF désactivé).
4. Notre serveur appelle GET /v1/checkout-invoice/confirm/{token}
   pour vérifier le statut réel.
5. L'utilisateur revient sur return_url (avec ?token=...).
"""

import hashlib
import json
import urllib.error
import urllib.request

BASE_TEST = "https://app.paydunya.com/sandbox-api"
BASE_LIVE = "https://app.paydunya.com/api"


class PayDunyaError(Exception):
    pass


def _base(mode):
    return BASE_LIVE if mode == "live" else BASE_TEST


def _headers(master_key, private_key, token):
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "PAYDUNYA-MASTER-KEY": master_key,
        "PAYDUNYA-PRIVATE-KEY": private_key,
        "PAYDUNYA-TOKEN": token,
    }


def _request(mode, path, method, master_key, private_key, token, payload=None, timeout=30):
    """Effectue une requête HTTP vers l'API PayDunya et retourne le dict JSON."""
    req = urllib.request.Request(
        f"{_base(mode)}{path}",
        headers=_headers(master_key, private_key, token),
        method=method,
    )
    if payload is not None:
        req.data = json.dumps(payload).encode("utf-8")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise PayDunyaError(f"PayDunya HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise PayDunyaError(f"PayDunya réseau: {e.reason}") from e


def initialiser_paiement(
    master_key,
    private_key,
    token,
    mode="test",
    montant=0,
    description="",
    store_name="RestaurantPro",
    callback_url=None,
    return_url=None,
    cancel_url=None,
    customer_name="",
    customer_phone="",
):
    """Crée une facture PayDunya (checkout invoice) et retourne la réponse.

    La réponse contient : response_code, response_text (URL de paiement),
    description, token (token de facture).
    """
    payload = {
        "invoice": {
            "total_amount": int(montant),
            "description": description,
        },
        "store": {"name": store_name},
    }
    if customer_name:
        client = {"name": customer_name}
        if customer_phone:
            client["phone"] = customer_phone
        payload["invoice"]["customer"] = client
    payload["actions"] = {
        "cancel_url": cancel_url or "",
        "return_url": return_url or "",
        "callback_url": callback_url or "",
    }

    reponse = _request(
        mode,
        "/v1/checkout-invoice/create",
        "POST",
        master_key,
        private_key,
        token,
        payload,
    )
    if str(reponse.get("response_code")) != "00":
        raise PayDunyaError(
            f"PayDunya init échec ({reponse.get('response_code')}): "
            f"{reponse.get('response_text')}"
        )
    return reponse


def verifier_paiement(master_key, private_key, token, mode="test", invoice_token=""):
    """Vérifie le statut réel d'une facture via l'API de confirmation."""
    if not invoice_token:
        raise PayDunyaError("PayDunya vérif : token de facture manquant.")
    return _request(
        mode,
        f"/v1/checkout-invoice/confirm/{invoice_token}",
        "GET",
        master_key,
        private_key,
        token,
    )


def verifier_hash(master_key, hash_value):
    """Vérifie le hash IPN : SHA-512 de la master key, renvoyé par PayDunya."""
    if not hash_value:
        return False
    attendu = hashlib.sha512(master_key.encode("utf-8")).hexdigest()
    return str(hash_value) == attendu
