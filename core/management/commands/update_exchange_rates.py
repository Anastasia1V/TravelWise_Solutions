# core/management/commands/update_exchange_rates.py
import requests
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings  # Будем использовать settings для базовой валюты
from core.models import Currency, ExchangeRate


class Command(BaseCommand):
    help = 'Updates exchange rates from Frankfurter.app API for all currencies in DB against a base currency (e.g., USD).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Optional. The date for which to fetch rates (YYYY-MM-DD). Defaults to "latest".',
            default='latest'  # Frankfurter использует 'latest' для последних доступных данных
        )
        parser.add_argument(
            '--base',
            type=str,
            help='Optional. The base currency code to fetch rates against (e.g., USD, EUR). Defaults to settings.BASE_CURRENCY_FOR_RATES.',
            default=None  # Позже возьмем из settings
        )

    def handle(self, *args, **options):
        # Определяем базовую валюту
        # 1. Из аргумента команды
        # 2. Из настроек Django (settings.py)
        # 3. По умолчанию 'USD', если нигде не задано
        base_currency_code_param = options['base']
        DEFAULT_BASE_CURRENCY = 'USD'  # Наша базовая валюта по умолчанию для хранения курсов

        # Получаем базовую валюту из настроек Django, если она там определена
        # В settings.py можно добавить: BASE_CURRENCY_FOR_RATES = 'USD'
        BASE_CURRENCY_FROM_SETTINGS = getattr(settings, 'BASE_CURRENCY_FOR_RATES', DEFAULT_BASE_CURRENCY)

        # Приоритет аргумента командной строки над настройками
        effective_base_currency = (base_currency_code_param or BASE_CURRENCY_FROM_SETTINGS).upper()

        fetch_date_str = options['date']  # 'latest' или 'YYYY-MM-DD'

        self.stdout.write(
            self.style.NOTICE(
                f"Updating exchange rates for date '{fetch_date_str}' against base currency '{effective_base_currency}'...")
        )

        # Проверяем, существует ли базовая валюта в нашей БД
        try:
            base_currency_obj = Currency.objects.get(code=effective_base_currency)
        except Currency.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                f"Base currency '{effective_base_currency}' not found in the Currency table. "
                f"Please add it first using 'load_currencies' or admin."
            ))
            return

        # Собираем все коды валют из нашей базы, КРОМЕ базовой
        currency_codes_to_fetch = list(
            Currency.objects.exclude(code=effective_base_currency).values_list('code', flat=True)
        )

        if not currency_codes_to_fetch:
            self.stdout.write(self.style.WARNING(
                "No target currencies found in the database (excluding the base currency). "
                "Only the base currency rate (to itself = 1) will be ensured."
            ))
            # Тем не менее, мы все равно должны обеспечить курс базовой валюты к себе = 1
        else:
            self.stdout.write(self.style.NOTICE(f"Target currencies to fetch: {', '.join(currency_codes_to_fetch)}"))

        # Формируем URL для API Frankfurter.app
        # Если fetch_date_str == 'latest', то это последний доступный день.
        # Если конкретная дата, то 'YYYY-MM-DD'.
        api_url = f"https://api.frankfurter.app/{fetch_date_str}"
        params = {
            'from': effective_base_currency,
            'to': ",".join(currency_codes_to_fetch) if currency_codes_to_fetch else ''
            # Пустая строка, если нет других валют
        }

        actual_rates_date = None  # Дата, на которую получены курсы (API может вернуть для предыдущего дня, если 'latest')
        rates_data = {}

        if currency_codes_to_fetch:  # Делаем запрос, только если есть что запрашивать кроме базовой
            try:
                response = requests.get(api_url, params=params, timeout=15)  # Увеличил таймаут
                response.raise_for_status()
                data = response.json()
                rates_data = data.get('rates', {})
                api_date_str = data.get('date')

                if not api_date_str:
                    self.stderr.write(self.style.ERROR("API response did not contain a 'date' field."))
                    return
                try:
                    actual_rates_date = timezone.datetime.strptime(api_date_str, "%Y-%m-%d").date()
                except ValueError:
                    self.stderr.write(self.style.ERROR(f"Invalid date format from API: {api_date_str}"))
                    return

                self.stdout.write(self.style.SUCCESS(f"Received rates from API for date: {actual_rates_date}"))

            except requests.exceptions.Timeout:
                self.stderr.write(self.style.ERROR("API request timed out."))
                return
            except requests.exceptions.RequestException as e:
                self.stderr.write(self.style.ERROR(f"API request failed: {e}"))
                return
            except ValueError:
                self.stderr.write(self.style.ERROR("Failed to decode JSON response from API."))
                return
        elif fetch_date_str == 'latest':  # Если нет других валют, но запросили latest, берем текущую дату
            actual_rates_date = timezone.now().date()
        else:  # Если нет других валют и дата указана явно
            try:
                actual_rates_date = timezone.datetime.strptime(fetch_date_str, "%Y-%m-%d").date()
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Invalid date format provided: {fetch_date_str}"))
                return

        if not actual_rates_date:  # Должна быть определена к этому моменту
            self.stderr.write(self.style.ERROR("Could not determine the date for the exchange rates."))
            return

        updated_count = 0
        created_count = 0
        missing_in_db_count = 0

        # Обновляем/создаем курсы для полученных валют
        for currency_code_api, rate_value_api in rates_data.items():
            try:
                target_currency_obj = Currency.objects.get(code=currency_code_api)
                rate_decimal = Decimal(str(rate_value_api))

                # Наша модель ExchangeRate.rate хранит: "сколько target_currency за 1 effective_base_currency"
                # Frankfurter API с from=USD, to=EUR,JPY возвращает:
                # "rates": {"EUR": 0.92, "JPY": 150.0}
                # Это означает: 1 USD = 0.92 EUR; 1 USD = 150.0 JPY. Это то, что нам нужно.

                obj, created = ExchangeRate.objects.update_or_create(
                    currency=target_currency_obj,
                    date=actual_rates_date,
                    defaults={'rate': rate_decimal}
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Currency.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Currency {currency_code_api} from API response not found in local DB. Skipping."))
                missing_in_db_count += 1
            except InvalidOperation:
                self.stdout.write(
                    self.style.WARNING(f"Invalid rate value for {currency_code_api}: {rate_value_api}. Skipping."))
            except Exception as e_save:
                self.stdout.write(self.style.ERROR(f"Error saving rate for {currency_code_api}: {e_save}"))

        # Убедимся, что курс базовой валюты к самой себе (равный 1) существует на эту дату
        # Это упростит логику конвертации, если from_currency == base_currency
        base_rate_obj, base_created = ExchangeRate.objects.update_or_create(
            currency=base_currency_obj,
            date=actual_rates_date,
            defaults={'rate': Decimal('1.000000')}  # 1.0 с 6 знаками
        )
        if base_created:
            created_count += 1
        else:
            updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Exchange rate update complete for {actual_rates_date} against {effective_base_currency}. "
            f"Created: {created_count}, Updated: {updated_count}. "
            f"Skipped (currency not in local DB): {missing_in_db_count if missing_in_db_count else 0}."
        ))