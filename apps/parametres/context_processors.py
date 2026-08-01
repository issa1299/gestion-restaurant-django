from .models import ParametreRestaurant


def parametre_global(request):
    return {"parametre": ParametreRestaurant.load()}
