from django.urls import re_path

from apps.notifications.consumers import CommandeConsumer

websocket_urlpatterns = [
    re_path(r"ws/commandes/(?P<groupe>\w+)/$", CommandeConsumer.as_asgi()),
]
