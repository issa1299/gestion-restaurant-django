"""Service CinetPay — Mobile Money (Orange Money, Moov, Wave, MTN) en FCFA.

Documentation officielle : https://docs.cinetpay.com/api/1.0-en/checkout

Flux :
1. POST /v2/payment          → initiation (renvoie payment_url)
2. Utilisateur redirigé sur  payment_url (caisse CinetPay)
3. CinetPay appelle notify_url (webhook POST, CSRF désactivé)
4. Notre serveur appelle     /v2/payment/check pour vérifier le statut réel
5. L'utilisateur revient sur return_url
"""

import json
import urllib.request
import urllib.error

URL_PAYMENT = "https://api-checkout.cinetpay.com/v2/payment"
URL_CHECK = "https://api-checkout.cinetpay.com/v2/payment/check"


class CinetPayError(Exception):
    pass


def _post(url, payload, timeout=30):
    """Envoie un POST JSON, retourne le dict de réponse."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise CinetPayError(f"CinetPay HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise CinetPayError(f"CinetPay réseau: {e.reason}") from e


def initialiser_paiement(
    apikey,
    site_id,
    transaction_id,
    montant,
    devise="XOF",
    description="Abonnement RestaurantPro",
    notify_url=None,
    return_url=None,
    customer_name="",
    customer_surname="",
    channels="MOBILE_MONEY",
):
    """Initialise un paiement et retourne la réponse de CinetPay.

    La réponse contient : code, message, data.payment_url, data.payment_token,
    data.payment_id, data.payment_date.
    """
    payload = {
        "apikey": apikey,
        "site_id": site_id,
        "transaction_id": transaction_id,
        "amount": int(montant),
        "currency": devise,
        "description": description,
        "channels": channels,
        "lang": "fr",
    }
    if notify_url:
        payload["notify_url"] = notify_url
    if return_url:
        payload["return_url"] = return_url
    if customer_name:
        payload["customer_name"] = customer_name
    if customer_surname:
        payload["customer_surname"] = customer_surname

    reponse = _post(URL_PAYMENT, payload)
    if str(reponse.get("code")) != "0":
        raise CinetPayError(
            f"CinetPay init échec ({reponse.get('code')}): "
            f"{reponse.get('message')}"
        )
    return reponse


def verifier_paiement(apikey, site_id, transaction_id):
    """Vérifie le statut réel d'une transaction via l'API de vérification."""
    reponse = _post(
        URL_CHECK,
        {
            "apikey": apikey,
            "site_id": site_id,
            "transaction_id": transaction_id,
        },
    )
    return reponse
