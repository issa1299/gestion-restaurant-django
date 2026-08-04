from django.conf import settings


def saas_mode(request):
    return {"SAAS_MODE": settings.SAAS_MODE}
