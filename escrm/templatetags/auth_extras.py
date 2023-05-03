from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter
def has_group(user, groups):
    if groups is None:
        return False
    group_list = [group.strip() for group in groups.split(',')]
    # print(group_list)
    return user.groups.filter(name__in=group_list).exists()
