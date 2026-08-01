from django import template

register = template.Library()


@register.filter
def has_role(user, roles):

    if not user.is_authenticated:
        return False

    roles_list = roles.split(",")

    return user.role in roles_list


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)