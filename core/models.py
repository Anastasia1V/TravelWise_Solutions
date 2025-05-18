# core/models.py
from django.db import models
from django.utils import timezone  # Для установки даты по умолчанию


class Currency(models.Model):
    code = models.CharField(
        max_length=3,
        unique=True,
        primary_key=True,
        help_text="Трехбуквенный ISO 4217 код валюты (например, USD, EUR, RUB)"
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Полное название валюты (например, Доллар США, Евро)"
    )
    symbol = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="Символ валюты (например, $, €, ₽)"
    )

    def __str__(self):
        return f"{self.code} ({self.name})" if self.name else self.code

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"
        ordering = ['code']


class ExchangeRate(models.Model):
    # Мы будем хранить все курсы относительно ОДНОЙ базовой валюты.
    # Например, USD. Тогда 'rate' будет показывать, сколько ЕДИНИЦ 'currency' 
    # нужно отдать за 1 USD.
    # Пример: если currency=EUR, rate=0.92 -> 1 USD = 0.92 EUR
    # Пример: если currency=RUB, rate=90.00 -> 1 USD = 90.00 RUB

    currency = models.ForeignKey(
        Currency,
        on_delete=models.CASCADE,
        related_name='rates',  # Имя для обратной связи от Currency к ExchangeRate
        help_text="Целевая валюта, для которой указан курс к базовой"
    )
    rate = models.DecimalField(
        max_digits=15,  # Общее количество цифр
        decimal_places=6,  # Количество цифр после запятой
        help_text="Курс: сколько единиц 'currency' за 1 единицу базовой валюты (например, USD)"
    )
    date = models.DateField(
        default=timezone.now,  # По умолчанию сегодняшняя дата
        help_text="Дата, на которую актуален данный курс"
    )
    last_updated = models.DateTimeField(
        auto_now=True,  # Автоматически обновляется при каждом сохранении
        help_text="Время последнего обновления записи"
    )

    def __str__(self):
        # Предполагаем, что базовая валюта - USD, но это не жестко зашито в модель
        return f"1 [БАЗОВАЯ_ВАЛЮТА] = {self.rate} {self.currency.code} на {self.date.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Курс обмена"
        verbose_name_plural = "Курсы обмена"
        # Уникальный курс для валюты на определённую дату (относительно нашей неявной базовой валюты)
        unique_together = ('currency', 'date')
        ordering = ['-date', 'currency__code']  # Сначала самые свежие, потом по коду валюты