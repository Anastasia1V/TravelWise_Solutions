# core/management/commands/load_currencies.py
from django.core.management.base import BaseCommand
from core.models import Currency  # Убедитесь, что импорт правильный

# Вы можете расширить этот список или получать его из другого источника
COMMON_CURRENCIES_DATA = [
    {'code': 'USD', 'name': 'Доллар США', 'symbol': '$'},
    {'code': 'EUR', 'name': 'Евро', 'symbol': '€'},
    {'code': 'GBP', 'name': 'Британский фунт стерлингов', 'symbol': '£'},
    {'code': 'JPY', 'name': 'Японская иена', 'symbol': '¥'},
    {'code': 'AUD', 'name': 'Австралийский доллар', 'symbol': 'A$'},
    {'code': 'CAD', 'name': 'Канадский доллар', 'symbol': 'CA$'},
    {'code': 'CHF', 'name': 'Швейцарский франк', 'symbol': 'CHF'},
    {'code': 'CNY', 'name': 'Китайский юань', 'symbol': '¥'},
    {'code': 'RUB', 'name': 'Российский рубль', 'symbol': '₽'},
    {'code': 'TRY', 'name': 'Турецкая лира', 'symbol': '₺'},
    {'code': 'INR', 'name': 'Индийская рупия', 'symbol': '₹'},
    # Добавьте другие валюты, которые часто используются вашими пользователями
]


class Command(BaseCommand):
    help = 'Loads a predefined list of common currencies into the Currency model.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Загрузка стандартных валют..."))
        created_count = 0
        updated_count = 0

        for currency_data in COMMON_CURRENCIES_DATA:
            currency, created = Currency.objects.update_or_create(
                code=currency_data['code'],
                defaults={  # Эти значения будут применены при создании ИЛИ обновлении
                    'name': currency_data.get('name', ''),
                    'symbol': currency_data.get('symbol', None)
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Создана валюта: {currency.code}"))
                created_count += 1
            else:
                # Проверим, нужно ли было обновление (если defaults отличаются от того, что в базе)
                # update_or_create сам обрабатывает обновление, если defaults отличаются.
                # Здесь мы просто считаем, что если не created, то это update (или без изменений)
                self.stdout.write(self.style.NOTICE(f"Валюта {currency.code} уже существует или была обновлена."))
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Загрузка валют завершена. "
            f"Создано новых: {created_count}. "
            f"Существовало/Обновлено: {updated_count}."
        ))