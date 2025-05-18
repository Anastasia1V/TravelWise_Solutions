import os
import django
from decimal import Decimal
from datetime import date

# Настройка Django окружения (если запускаете как отдельный скрипт)
# Это нужно, чтобы скрипт знал о ваших Django настройках и моделях
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'travelwise.settings')  # ЗАМЕНИТЕ 'travelwise' на имя вашей папки с settings.py
django.setup()

# Теперь можно импортировать ваши модели и функции
from core.currency_converter import convert_currency, INTERNAL_BASE_CURRENCY_CODE
from core.models import Currency, ExchangeRate
from django.utils import timezone


def run_tests():
    print(f"Внутренняя базовая валюта для конвертера: {INTERNAL_BASE_CURRENCY_CODE}")

    # Предположим, курсы есть на эту дату
    test_date = date(2025, 5, 16)
    # Если для этой даты нет курсов, замените на ту, для которой вы загрузили
    # latest_rate_entry = ExchangeRate.objects.order_by('-date').first()
    # if latest_rate_entry:
    #     test_date = latest_rate_entry.date
    # else:
    #     print("Нет курсов в базе для теста!")
    #     return

    print(f"Тестирование конвертации для даты: {test_date}")

    print("\n--- Тесты конвертации ---")

    amount_eur_test = Decimal('100')
    from_c = 'EUR'
    to_c = 'USD'
    converted_val = convert_currency(amount_eur_test, from_c, to_c, test_date)
    print(f"{amount_eur_test} {from_c} = {converted_val} {to_c}")

    amount_usd_test = Decimal('100')
    from_c = 'USD'
    to_c = 'EUR'
    converted_val = convert_currency(amount_usd_test, from_c, to_c, test_date)
    print(f"{amount_usd_test} {from_c} = {converted_val} {to_c}")

    # Добавьте сюда другие тестовые случаи, как в предыдущем примере
    # Например, EUR в RUB
    rub_curr = Currency.objects.filter(code='RUB').first()
    if rub_curr:
        converted_rub = convert_currency(amount_eur_test, 'EUR', 'RUB', test_date)
        print(f"{amount_eur_test} EUR = {converted_rub} RUB")
    else:
        print("Валюта RUB не найдена для теста EUR -> RUB.")

    # Валюта в саму себя
    converted_eur_to_eur = convert_currency(amount_eur_test, 'EUR', 'EUR', test_date)
    print(f"{amount_eur_test} EUR = {converted_eur_to_eur} EUR")

    # Несуществующая валюта или курс
    unknown_conv = convert_currency(Decimal('100'), 'EUR', 'XYZ', test_date)
    print(f"100 EUR to XYZ = {unknown_conv}")


if __name__ == '__main__':
    run_tests()

