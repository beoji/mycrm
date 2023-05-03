from django import template
import calendar


register = template.Library()

@register.filter
def month_name(month_number):
    if month_number == '1':
        return 'Styczeń'
    if month_number == '2':
        return 'Luty'
    if month_number == '3':
        return 'Marzec'
    if month_number == '4':
        return 'Kwiecień'
    if month_number == '5':
        return 'Maj'
    if month_number == '6':
        return 'Czerwiec'
    if month_number == '7':
        return 'Lipiec'
    if month_number == '8':
        return 'Sierpień'
    if month_number == '9':
        return 'Wrzesień'
    if month_number == '10':
        return 'Październik'
    if month_number == '11':
        return 'Listopad'
    if month_number == '12':
        return 'Grudzień'


register.filter('month_name', month_name)