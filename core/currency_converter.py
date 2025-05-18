# core/currency_converter.py
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from django.utils import timezone
from django.conf import settings  # Для получения базовой валюты
from .models import ExchangeRate, Currency  # Убедитесь, что модели импортируются правильно

# Определяем нашу внутреннюю базовую валюту, относительно которой ВСЕ курсы хранятся в БД.
# Это должно совпадать с тем, как вы загружаете курсы командой update_exchange_rates
# (т.е. значение --base или settings.BASE_CURRENCY_FOR_RATES для этой команды).
INTERNAL_BASE_CURRENCY_CODE = getattr(settings, 'BASE_CURRENCY_FOR_RATES', 'USD').upper()


def convert_currency(amount, from_currency_code, to_currency_code, date_for_conversion=None):
    """
    Конвертирует сумму из одной валюты в другую, используя сохраненные курсы обмена.
    Предполагается, что все курсы в базе ExchangeRate хранятся относительно INTERNAL_BASE_CURRENCY_CODE.
    """
    from_currency_code_upper = str(from_currency_code).upper()
    to_currency_code_upper = str(to_currency_code).upper()

    if from_currency_code_upper == to_currency_code_upper:
        try:
            return Decimal(str(amount))  # Просто возвращаем сумму, если валюты совпадают
        except InvalidOperation:
            # log или raise error, если сумма невалидна
            return None

    if date_for_conversion is None:
        # Если дата не указана, используем самую последнюю доступную дату курсов
        # Это может быть вчерашний день или ранее, если сегодня выходной или курсы еще не обновились
        latest_rate_entry = ExchangeRate.objects.order_by('-date').first()
        if not latest_rate_entry:
            # log.warning("No exchange rates found in the database at all.")
            return None  # Нет курсов в базе вообще
        date_for_conversion = latest_rate_entry.date

    # print(f"Конвертация для даты: {date_for_conversion}")

    try:
        amount_decimal = Decimal(str(amount))
        if amount_decimal == Decimal(0):  # Если сумма 0, результат 0
            return Decimal(0)
    except InvalidOperation:
        # log.error(f"Некорректная сумма для конвертации: {amount}")
        return None

    # Получаем объекты Currency. Если их нет, значит, мы не поддерживаем эти валюты.
    try:
        # Это не обязательно, если вы уверены, что коды всегда будут в таблице Currency,
        # но это хорошая проверка.
        from_curr_obj = Currency.objects.get(code=from_currency_code_upper)
        to_curr_obj = Currency.objects.get(code=to_currency_code_upper)
    except Currency.DoesNotExist:
        # log.warning(f"Одна из валют ({from_currency_code_upper} или {to_currency_code_upper}) не найдена в справочнике Currency.")
        return None

    # Получаем курсы для ИСХОДНОЙ и ЦЕЛЕВОЙ валют относительно INTERNAL_BASE_CURRENCY_CODE
    # Ищем самый последний курс на указанную дату или РАНЕЕ (fallback)
    rate_from_db_obj = ExchangeRate.objects.filter(
        currency=from_curr_obj,
        date__lte=date_for_conversion  # Ищем на эту дату или ранее
    ).order_by('-date').first()  # Берем самый свежий из найденных

    rate_to_db_obj = ExchangeRate.objects.filter(
        currency=to_curr_obj,
        date__lte=date_for_conversion
    ).order_by('-date').first()

    if not rate_from_db_obj:
        # log.warning(f"Курс для {from_currency_code_upper} к {INTERNAL_BASE_CURRENCY_CODE} не найден на {date_for_conversion} или ранее.")
        return None
    if not rate_to_db_obj:
        # log.warning(f"Курс для {to_currency_code_upper} к {INTERNAL_BASE_CURRENCY_CODE} не найден на {date_for_conversion} или ранее.")
        return None

    # Курсы из базы: rate_from_db_obj.rate = "сколько from_currency за 1 INTERNAL_BASE_CURRENCY"
    #                rate_to_db_obj.rate   = "сколько to_currency за 1 INTERNAL_BASE_CURRENCY"
    rate_from_base = rate_from_db_obj.rate
    rate_to_base = rate_to_db_obj.rate

    # print(f"Debug: {amount_decimal} {from_currency_code_upper} -> {to_currency_code_upper} @ {date_for_conversion}")
    # print(f"1 {INTERNAL_BASE_CURRENCY_CODE} = {rate_from_base} {from_currency_code_upper}")
    # print(f"1 {INTERNAL_BASE_CURRENCY_CODE} = {rate_to_base} {to_currency_code_upper}")

    if rate_from_base == Decimal(0):  # Избегаем деления на ноль
        # log.error(f"Нулевой курс для {from_currency_code_upper} к {INTERNAL_BASE_CURRENCY_CODE}.")
        return None

    # Шаг 1: Конвертируем исходную сумму в INTERNAL_BASE_CURRENCY
    # amount_исходная * (1 INTERNAL_BASE_CURRENCY / rate_from_base ИСХОДНОЙ_ВАЛЮТЫ) = сумма_в_INTERNAL_BASE_CURRENCY
    amount_in_internal_base = amount_decimal / rate_from_base
    # print(f"Сумма в {INTERNAL_BASE_CURRENCY_CODE}: {amount_in_internal_base}")

    # Шаг 2: Конвертируем сумму из INTERNAL_BASE_CURRENCY в целевую валюту
    # сумма_в_INTERNAL_BASE_CURRENCY * (rate_to_base ЦЕЛЕВОЙ_ВАЛЮТЫ / 1 INTERNAL_BASE_CURRENCY) = сумма_в_ЦЕЛЕВОЙ_ВАЛЮТЕ
    converted_amount = amount_in_internal_base * rate_to_base
    # print(f"Сконвертированная сумма в {to_currency_code_upper}: {converted_amount}")

    # Округляем до 2 знаков после запятой для денежных сумм (стандартно)
    # Вы можете настроить количество знаков, если нужно больше/меньше
    return converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)