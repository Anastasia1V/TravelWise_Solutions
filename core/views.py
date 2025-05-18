# core/views.py
from django.http import JsonResponse
from .models import Currency


# Если ExchangeRate нужен для фильтрации, можно импортировать

def get_available_currencies_api(request):
    """
    Возвращает список всех валют из справочника Currency,
    отсортированных по названию для удобства пользователя.
    """
    # Вариант 1: Просто все валюты из справочника Currency
    currencies = Currency.objects.all().order_by('name')

    # Вариант 2 (опционально, если хотите показывать только те, для которых есть хоть один курс):
    # from .models import ExchangeRate
    # currencies_with_rates_codes = ExchangeRate.objects.values_list('currency__code', flat=True).distinct()
    # currencies = Currency.objects.filter(code__in=currencies_with_rates_codes).order_by('name')
    # Если используете этот вариант, убедитесь, что у вас достаточно курсов для всех нужных валют.

    results = []
    for c in currencies:
        results.append({
            'code': c.code,
            'name': f"{c.name} ({c.code})",  # Для отображения пользователю, например "Евро (EUR)"
            'symbol': c.symbol or ''  # Символ, или пустая строка если нет
        })

    return JsonResponse(results, safe=False)  # safe=False, так как возвращаем список